from __future__ import absolute_import
from builtins import next
from ckanext.apicatalog_routes import views, cli, auth, helpers, db

from flask import has_request_context

from ckanext.apicatalog.schema import create_user_to_organization_schema

from ckan import plugins, model
from ckan.plugins import toolkit


import logging

from ckan.plugins.toolkit import _
from ckan.lib.plugins import DefaultPermissionLabels

from ckan.lib.navl.dictization_functions import validate as _validate
import ckan.lib.mailer as mailer


abort = toolkit.abort
render = toolkit.render
check_access = toolkit.check_access
NotAuthorized = toolkit.NotAuthorized
ObjectNotFound = toolkit.ObjectNotFound
get_action = toolkit.get_action

ValidationError = toolkit.ValidationError

log = logging.getLogger(__name__)


def admin_only(context, data_dict=None):
    return {'success': False, 'msg': 'Access restricted to system administrators'}


class Apicatalog_RoutesPlugin(plugins.SingletonPlugin, DefaultPermissionLabels):
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IPermissionLabels)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IClick)

    # IRoutes

    def before_map(self, m):
        controller = 'ckanext.apicatalog_routes.plugin:Apicatalog_RevisionController'
        m.connect('/revision', action='index', controller=controller)
        m.connect('/revision/list', action='list', controller=controller)
        m.connect('/revision/diff/{id}', action='diff', controller=controller)

        extra_information_controller = 'ckanext.apicatalog_routes.plugin:ExtraInformationController'
        m.connect('data_exchange_layer_user_organizations',
                  '/data_exchange_layer_user_organizations',
                  action='data_exchange_layer_user_organizations',
                  controller=extra_information_controller)

        return m

    # IAuthFunctions

    def get_auth_functions(self):
        return {'revision_index': admin_only,
                'revision_list': admin_only,
                'revision_diff': admin_only,
                'package_revision_list': admin_only,
                'package_show': auth.package_show,
                'read_members': auth.read_members,
                'group_edit_permissions': auth.read_members,
                'send_reset_link': admin_only,
                'create_user_to_organization': auth.create_user_to_organization,
                'create_organization_users': admin_only,
                'user_create': auth.user_create,
                'user_update': auth.user_update,
                'user_show': auth.user_show,
                'member_create': auth.member_create,
                'member_delete': auth.member_delete,
                'organization_member_create': auth.organization_member_create,
                'organization_member_delete': auth.organization_member_delete,
                'group_show': auth.group_show,
                'user_invite': auth.user_invite,
                'package_create': admin_only,
                'organization_delete': admin_only,
                'package_delete': admin_only,
                'resource_delete': admin_only
                }

    # IPermissionLabels

    def get_dataset_labels(self, dataset_obj):

        labels = super(Apicatalog_RoutesPlugin, self).get_dataset_labels(dataset_obj)

        context = {
            'ignore_auth': True
        }

        for user_name in toolkit.config.get('ckanext.apicatalog_routes.readonly_users', '').split():
            try:
                user_obj = get_action('user_show')(context, {'id': user_name})
                labels.append(u'read_only_admin-%s' % user_obj['id'])
            except ObjectNotFound:
                continue

        pkg_dict = get_action('package_show')(context, {'id': dataset_obj.id})

        if pkg_dict.get('private') and \
                pkg_dict.get('private') is True:
            allowed_organizations = [o.strip() for o in pkg_dict.get('allowed_organizations', "").split(',')
                                     if pkg_dict.get('allowed_organizations', "")]
            for org_name in allowed_organizations:
                organization_dict = get_action('organization_show')(context, {'id': org_name})
                labels.append(u'allowed_organization_members-%s' % organization_dict['id'])

        return labels

    def get_user_dataset_labels(self, user_obj):

        labels = super(Apicatalog_RoutesPlugin, self).get_user_dataset_labels(user_obj)
        readonly_users = toolkit.aslist(toolkit.config.get('ckanext.apicatalog_routes.readonly_users', ''))

        if user_obj and user_obj.name in readonly_users:
            labels.append(u'read_only_admin-%s' % user_obj.id)

        if user_obj:
            orgs = get_action(u'organization_list_for_user')({u'user': user_obj.id}, {})
            labels.extend(u'allowed_organization_members-%s' % o['id'] for o in orgs)
        return labels

    # After package_search, filter out the resources which the user doesn't have access to
    def after_search(self, search_results, search_params):
        # Only filter results if processing a request
        if not has_request_context():
            return search_results

        try:
            if 'user' in toolkit.g:
                user = toolkit.get_action('user_show')({'ignore_auth': True}, {'id': toolkit.g.user})
                if user and user.get('sysadmin'):
                    return search_results
        except ObjectNotFound:
            pass

        for result in search_results['results']:
            # Accessible resources are:
            # 1) Visibility/private is public (False)
            # OR
            # 2) Visibility/private is limited (True) AND the logged in user is on the allowed users list
            # OR
            # 3) Visibility/private is limited (True) AND the logged in user's list of organizations contains
            #    the organization of the package
            log.warn("results")
            user_orgs = toolkit.get_action('organization_list_for_user')(
                    {'ignore_auth': True},
                    {'id': toolkit.g.user, 'permission': 'read'})
            allowed_resources = [resource for resource in result.get('resources', [])
                                 if resource.get('access_restriction_level', '') in ('', 'public') or
                                 ((resource.get('access_restriction_level', '') == 'private')
                                  and any(o.get('name') in orgs for orgs in
                                          resource.get('allowed_organizations', '').split(',') for o in user_orgs)) or
                                 ((resource.get('access_restriction_level', '') == 'true') and
                                  any(o.get('id', None) == result.get('organization',
                                                                      {}).get('id', '') for o in user_orgs))]

            result['resources'] = allowed_resources
            result['num_resources'] = len(allowed_resources)
        return search_results

    # After package_show, filter out the resources which the user doesn't have access to
    def after_show(self, context, data_dict):
        # Only filter results if processing a request
        if not has_request_context():
            return data_dict

        # Skip access check if sysadmin or auth is ignored
        if context.get('ignore_auth') or (context.get('auth_user_obj') and context.get('auth_user_obj').sysadmin):
            return data_dict

        user_name = context.get('user')

        if user_name:
            user_orgs = [{'name': o['name'], 'id': o['id']} for o in toolkit.get_action('organization_list_for_user')(
                {'ignore_auth': True},
                {'id': user_name, 'permission': 'read'})]
        else:
            user_orgs = []

        # Allowed resources are the ones where:
        # 1) Visibility/private is public (False)
        # OR
        # 2) Visibility/private is limited (True) AND the logged in user is on the allowed users list
        # OR
        # 3) Visibility/private is limited (True) AND the logged in user's list of organizations contains
        #    the organization of the package

        allowed_resources = [resource for resource in data_dict.get('resources', [])
                             if resource.get('access_restriction_level', '') in ('', 'public') or
                             ((resource.get('access_restriction_level', '') == 'private')
                              and any(o.get('name') in orgs for orgs in
                                      resource.get('allowed_organizations', '').split(',') for o in user_orgs)) or
                             ((resource.get('access_restriction_level', '') == 'private') and
                              any(o.get('id', None) == data_dict.get('organization',
                                                                     {}).get('id', '') for o in user_orgs))]

        data_dict['resources'] = allowed_resources
        data_dict['num_resources'] = len(allowed_resources)

        return data_dict

    # IActions
    def get_actions(self):
        return {
            "send_reset_link": send_reset_link,
            "create_user_to_organization": create_user_to_organization,
            "create_organization_users": create_organization_users,
        }

    # IBlueprint
    def get_blueprint(self):
        return views.get_blueprints()

    def get_helpers(self):
        return {
            "lang": helpers.lang
        }

    # IClick

    def get_commands(self):
        return cli.get_commands()


def send_reset_link(context, data_dict):
    toolkit.check_access('send_reset_link', context)

    user_obj = model.User.get(data_dict['user_id'])
    mailer.send_reset_link(user_obj)


def create_user_to_organization(context, data_dict):

    toolkit.check_access('create_user_to_organization', context)
    schema = context.get('schema') or create_user_to_organization_schema()
    session = context['session']

    data, errors = _validate(data_dict, schema, context)

    if errors:
        session.rollback()
        raise ValidationError(errors)

    created_user = db.UserForOrganization.create(data['fullname'],
                                                 data['email'],
                                                 data['business_id'],
                                                 data['organization_name'])

    return {
        "msg": _("User {name} stored in database.").format(name=created_user.fullname)
    }


def create_organization_users(context, data_dict):
    toolkit.check_access('create_organization_users', context)
    retry = data_dict.get('retry', False)
    pending_user_applications = db.UserForOrganization.get_pending(include_failed=retry)

    organizations = toolkit.get_action('organization_list')(context, {'all_fields': True, 'include_extras': True})
    organizations_by_membercode = {}
    for organization in organizations:
        xroad_member_code = organization.get('xroad_membercode')

        if not xroad_member_code:
            continue

        organizations_by_membercode.setdefault(xroad_member_code, []).append(organization)

    user_list = toolkit.get_action('user_list')
    user_invite = toolkit.get_action('user_invite')
    created = []
    invalid = []
    ambiguous = []
    duplicate = []

    for application in pending_user_applications:
        matching_organizations = organizations_by_membercode.get(application.business_id, [])

        if len(matching_organizations) == 0:
            log.warn('No organization found for business id %s, skipping invalid user application', application.business_id)
            application.mark_invalid()
            invalid.append(application.business_id)
            continue
        elif len(matching_organizations) > 1:
            log.warn('Multiple organizations found with business id %s, skipping ambiguous user application',
                     application.business_id)
            application.mark_ambiguous()
            ambiguous.append(application.business_id)
            continue

        organization = next(iter(matching_organizations))

        matching_users = user_list(context, {'email': application.email, 'all_fields': False})
        if matching_users:
            log.warn('Existing user found for email address %s, skipping duplicate user', application.email)
            application.mark_duplicate()
            duplicate.append(application.email)
            continue

        log.info('Inviting user %s to organization %s (%s)', application.email, organization['title'], organization['id'])
        try:
            user = user_invite(context, {'email': application.email, 'group_id': organization['id'], 'role': 'admin'})
        except ValidationError as e:
            log.warn(e)
            continue
        except ObjectNotFound as e:
            log.warn(e)
            continue

        application.mark_done()
        created.append(user.get('name'))

    context.get('session', model.Session).commit()
    return {'success': True, 'result': {'created': created, 'invalid': invalid, 'ambiguous': ambiguous,
                                        'duplicate': duplicate}}


# TODO: If some asks for /data_exchange_layer_user_organizations url, convert this to action
# class ExtraInformationController(toolkit.BaseController):

#    def data_exchange_layer_user_organizations(self):
#        context = {}
#        all_organizations = get_action('organization_list')(context, {"all_fields": True})
#        packageless_organizations = [o for o in all_organizations if o.get('package_count', 0) == 0]
#        response.headers['content-type'] = 'application/json'
#        return json.dumps(packageless_organizations)
