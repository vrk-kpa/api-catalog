from ckanext.apicatalog_routes import views
import ckanext.apicatalog_routes.cli as cli
from ckanext.apicatalog_scheming.schema import create_user_to_organization_schema

from ckan.plugins import toolkit
import ckan.lib.plugins as lib_plugins
import ckan.plugins as plugins
from ckan.common import _, request, response
import ckan.model as model
import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.lib.mailer as mailer

import json
from helpers import lang
from db import UserForOrganization
import logging
import auth
from flask import has_request_context

abort = toolkit.abort
render = toolkit.render
check_access = toolkit.check_access
NotAuthorized = toolkit.NotAuthorized
ObjectNotFound = toolkit.ObjectNotFound
get_action = toolkit.get_action

unflatten = dictization_functions.unflatten
DataError = dictization_functions.DataError

ValidationError = toolkit.ValidationError

_validate = dictization_functions.validate

log = logging.getLogger(__name__)


def admin_only(context, data_dict=None):
    return {'success': False, 'msg': 'Access restricted to system administrators'}


def set_repoze_user(user_id):
    '''Set the repoze.who cookie to match a given user_id'''
    if 'repoze.who.plugins' in request.environ:
        rememberer = request.environ['repoze.who.plugins']['friendlyform']
        identity = {'repoze.who.userid': user_id}
        response.headerlist += rememberer.remember(request.environ, identity)


class Apicatalog_RoutesPlugin(plugins.SingletonPlugin, lib_plugins.DefaultPermissionLabels):
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
                'package_create': admin_only
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

        return labels

    def get_user_dataset_labels(self, user_obj):

        labels = super(Apicatalog_RoutesPlugin, self).get_user_dataset_labels(user_obj)

        if user_obj and user_obj.name in toolkit.config.get('ckanext.apicatalog_routes.readonly_users', '').split():
            labels.append(u'read_only_admin-%s' % user_obj.id)

        return labels

    # After package_search, filter out the resources which the user doesn't have access to
    def after_search(self, search_results, search_params):
        # Only filter results if processing a request
        if not has_request_context():
            return search_results

        user_orgs = get_action('organization_list_for_user')(auth_context(), {})
        for result in search_results['results']:
            # Accessible resources are:
            # 1) access_restriction_level is public
            # OR
            # 2) access_restriction_level is only_allowed_users AND the logged in user is on the allowed users list
            # OR
            # 3) access_restriction_level is same_organization AND the logged in user's list of organizations contains
            #    the organization of the package
            allowed_resources = [resource for resource in result.get('resources', [])
                                 if resource.get('access_restriction_level', '') in ('', 'public') or
                                 (resource.get('access_restriction_level', '') == 'only_allowed_users'
                                  and toolkit.g.user in resource.get('allowed_users', '').split(',')) or
                                 (resource.get('access_restriction_level', '') == 'same_organization' and
                                  any(o.get('id', None) == result.get('organization', {}).get('id', '') for o in user_orgs))]
            result['resources'] = allowed_resources
            result['num_resources'] = len(allowed_resources)
        return search_results

    # After package_show, filter out the resources which the user doesn't have access to
    def after_show(self, context, data_dict):
        # Skip access check if sysadmin
        if (context.get('sysadmin')):
            return data_dict

        user_name = context.get('user')

        if user_name:
            user_orgs = get_action('organization_list_for_user')(context, {'id': user_name})
        else:
            user_orgs = []

        # Allowed resources are the ones where:
        # 1) access_restriction_level is public
        # OR
        # 2) access_restriction_level is only_allowed_users AND the logged in user is on the allowed users list
        # OR
        # 3) access_restriction_level is same_organization AND the logged in user's list of organizations contains
        #    the organization of the package
        allowed_resources = [resource for resource in data_dict.get('resources', [])
                             if 'access_restriction_level' not in resource or
                             resource.get('access_restriction_level', '') in ('', 'public') or
                             (resource.get('access_restriction_level', '') == 'only_allowed_users'
                              and toolkit.g.user in resource.get('allowed_users', '').split(',')) or
                             (resource.get('access_restriction_level', '') == 'same_organization' and
                              any(o.get('id', None) == data_dict.get('organization', {}).get('id', '') for o in user_orgs))]
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
            "lang": lang
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

    created_user = UserForOrganization.create(data['fullname'], data['email'], data['business_id'], data['organization_name'])

    return {
        "msg": _("User {name} stored in database.").format(name=created_user.fullname)
    }


def create_organization_users(context, data_dict):
    toolkit.check_access('create_organization_users', context)
    retry = data_dict.get('retry', False)
    pending_user_applications = UserForOrganization.get_pending(include_failed=retry)

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
            log.warn('Multiple organizations found with business id %s, skipping ambiguous user application', application.business_id)
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
    return {'success': True, 'result': {'created': created, 'invalid': invalid, 'ambiguous': ambiguous, 'duplicate': duplicate}}


def auth_context():
    return {'model': model,
            'session': model.Session,
            'user': toolkit.g.get('user') or toolkit.g.get('author')}


class ExtraInformationController(toolkit.BaseController):

    def data_exchange_layer_user_organizations(self):
        context = {}
        all_organizations = get_action('organization_list')(context, {"all_fields": True})
        packageless_organizations = [o for o in all_organizations if o.get('package_count', 0) == 0]
        response.headers['content-type'] = 'application/json'
        return json.dumps(packageless_organizations)
