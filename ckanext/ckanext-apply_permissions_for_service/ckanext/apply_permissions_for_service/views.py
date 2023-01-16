from builtins import next
import ckan.lib.uploader as uploader
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h
from ckan.views.user import _extra_template_variables as ckan_user_extra_template_variables
from flask import Blueprint
from logging import getLogger
import re

log = getLogger(__name__)

apply_permissions = Blueprint("apply_permissions", __name__, url_prefix=u'/apply_permissions_for_service')


def dashboard(app_type='sent'):
    context = {
        u'user': toolkit.g.user,
        u'auth_user_obj': toolkit.g.userobj,
        u'for_view': True
    }
    data_dict = {u'user_obj': toolkit.g.userobj}
    extra_vars = ckan_user_extra_template_variables(context, data_dict)
    applications = toolkit.get_action('service_permission_application_list')(context, {})
    if app_type == 'received':
        extra_vars['applications'] = applications.get('received')
    else:
        extra_vars['applications'] = applications.get('sent')

    return toolkit.render('apply_permissions_for_service/dashboard.html', extra_vars=extra_vars)


def new_post(context, subsystem_id):
    form = toolkit.request.form
    files = toolkit.request.files

    data_dict = {
            'organization_id': form.get('organization_id'),
            'target_organization_id': form.get('target_organization_id'),
            'intermediate_organization_id': None,
            'member_code': form.get('member_code'),
            'intermediate_member_code': None,
            'contact_name': form.get('contact_name'),
            'contact_email': form.get('contact_email'),
            'target_subsystem_id': form.get('target_subsystem_id'),
            'subsystem_id': form.get('subsystem_id'),
            'service_id_list': form.getlist('service_id_list'),
            'ip_address_list': [ip for ip in form.getlist('ip_address_list') if ip],
            'request_date': form.get('request_date'),
            'usage_description': form.get('usage_description'),
            'file': files.get('file'),
            'file_url': form.get('file_url'),
            'clear_upload': form.get('clear_upload'),
            }

    '''
    The template doesn't switch the inputs if intermediate organization is enabled and selected
    but in reality when there's an intermediate organization the subsystem belongs to the organization
    that uses the data and not the intermediate org
    'Intermediate organization' applies for permission to use 'Target organization's subsystem' in the name of
    the utilizing 'Organization' and their 'Subsystem'. I.e. The intermediate organization should never be the owner
    of either subsystem in the application
    '''
    if form.get('enable_intermediate_organization'):
        data_dict['organization_id'] = form.get('intermediate_organization_id')
        data_dict['member_code'] = form.get('intermediate_member_code')
        data_dict['intermediate_organization_id'] = form.get('organization_id')
        data_dict['intermediate_member_code'] = form.get('member_code')

    try:
        if toolkit.check_ckan_version(min_version='2.5'):
            upload = uploader.get_uploader('apply_permission')
        else:
            upload = uploader.Upload('apply_permission')

        upload.update_data_dict(data_dict, 'file_url',
                                'file', 'clear_upload')
        upload.upload(max_size=uploader.get_max_resource_size())

        file_url = data_dict.get('file_url', '')
        data_dict['application_filename'] = file_url

        toolkit.get_action('service_permission_application_create')(context, data_dict)
    except (toolkit.ValidationError, KeyError) as e:
        if form.get('enable_intermediate_organization'):
            data_dict['organization_id'] = form.get('organization_id')
            data_dict['member_code'] = form.get('member_code')
            data_dict['intermediate_organization_id'] = form.get('intermediate_organization_id')
            data_dict['intermediate_member_code'] = form.get('intermediate_member_code')
            e.error_dict['member_code'], e.error_dict['intermediate_member_code'] = \
                e.error_dict['intermediate_member_code'], e.error_dict['member_code']

            data_dict['enable_intermediate_organization'] = True

        return new_get(context, subsystem_id, e.error_dict, values=data_dict)

    return toolkit.render('apply_permissions_for_service/sent.html')


def new_get(context, target_subsystem_id, errors={}, values={}, preview=False):
    service_id = toolkit.request.args.get('service_id')
    package = toolkit.get_action('package_show')(context, {'id': target_subsystem_id})

    if (package.get('service_permission_settings', {}).get('delivery_method') == "none"
            or package.get('service_permission_settings', {}).get('delivery_method') is None) and preview is False:
        toolkit.abort(403, toolkit._("This API is not accepting access applications."))
    organization = toolkit.get_action('organization_show')(context, {'id': package['owner_org']})
    user_managed_organizations = toolkit.get_action('organization_list_for_user')(context, {
        'permission': 'manage_group'
        })
    user_managed_datasets_query = 'owner_org:({})'.format(' OR '.join(o['id'] for o in user_managed_organizations))
    user_managed_datasets = toolkit.get_action('package_search')(context, {
        'q': user_managed_datasets_query,
        'include_private': True,
        'rows': 1000
        }).get('results', []) if user_managed_organizations else []

    extra_vars = {
            'target_subsystem_id': target_subsystem_id,
            'service_id': service_id,
            'pkg': package,
            'service': next((r for r in package.get('resources', []) if r['id'] == service_id), None),
            'org': organization,
            'user': toolkit.g.userobj,
            'user_managed_organizations': user_managed_organizations,
            'user_managed_datasets': user_managed_datasets,
            'values': values,
            'errors': errors
            }

    if preview:
        return toolkit.render('apply_permissions_for_service/preview.html', extra_vars=extra_vars)

    return toolkit.render('apply_permissions_for_service/new.html', extra_vars=extra_vars)


def new(target_subsystem_id):
    try:
        context = {u'user': toolkit.g.user, u'auth_user_obj': toolkit.g.userobj}
        toolkit.check_access('service_permission_application_create', context, {})

        if toolkit.request.method == u'POST':
            return new_post(context, target_subsystem_id)
        else:
            return new_get(context, target_subsystem_id)
    except toolkit.NotAuthorized:
        toolkit.abort(403, toolkit._(u'Not authorized to see this page'))


def view(application_id):
    try:
        context = {u'user': toolkit.g.user, u'auth_user_obj': toolkit.g.userobj}
        data_dict = {'id': application_id}
        application = toolkit.get_action('service_permission_application_show')(context, data_dict)
        extra_vars = {'application': application}
        return toolkit.render('apply_permissions_for_service/view.html', extra_vars=extra_vars)
    except toolkit.NotAuthorized:
        toolkit.abort(403, toolkit._(u'Not authorized to see this page'))


def preview(target_subsystem_id):
    try:
        context = {u'user': toolkit.g.user, u'auth_user_obj': toolkit.g.userobj}
        toolkit.check_access('service_permission_settings', context, {"subsystem_id": target_subsystem_id})
        return new_get(context, target_subsystem_id, preview=True)
    except toolkit.NotAuthorized:
        toolkit.abort(403, toolkit._(u'Not authorized to see this page'))


def manage(target_subsystem_id):
    context = {u'user': toolkit.g.user, u'auth_user_obj': toolkit.g.userobj}
    package = toolkit.get_action('package_show')(context, {'id': target_subsystem_id})
    toolkit.c.pkg_dict = package

    data_dict = {'target_subsystem_id': package.get('id')}
    applications = toolkit.get_action('service_permission_application_list')(context, data_dict)
    extra_vars = {
            'target_subsystem_id': target_subsystem_id,
            'pkg_dict': package,
            'applications': applications
            }
    return toolkit.render('apply_permissions_for_service/manage.html', extra_vars=extra_vars)


def settings_get(context, subsystem_id, errors={}, values=None):
    package = toolkit.get_action('package_show')(context, {'id': subsystem_id})
    toolkit.c.pkg_dict = package
    settings = values or toolkit.get_action('service_permission_settings_show')(context, {'subsystem_id': subsystem_id})
    user_managed_organizations = toolkit.get_action('organization_list_for_user')(context, {
        'permission': 'manage_group'
    })

    extra_vars = {
            'subsystem_id': subsystem_id,
            'pkg_dict': package,
            'errors': errors,
            'settings': settings,
            'user_managed_organizations': user_managed_organizations
            }

    return toolkit.render('apply_permissions_for_service/settings.html', extra_vars=extra_vars)


def settings_post(context, subsystem_id):
    form = toolkit.request.form
    files = toolkit.request.files

    data_dict = {
        'subsystem_id': subsystem_id,
        'delivery_method': form.get('deliveryMethod'),
        'email': form.get('email'),
        'api': form.get('api'),
        'file': files.get('file'),
        'file_url': form.get('file_url'),
        'original_filename': form.get('original_filename'),
        'clear_upload': form.get('clear_upload'),
        'web': form.get('web'),
        'additional_file': files.get('additional_file'),
        'require_additional_application_file': toolkit.asbool(form.get('require_additional_application_file')),
        'additional_file_url': form.get('additional_file_url'),
        'original_additional_filename': form.get('original_additional_filename'),
        'additional_file_clear_upload': form.get('additional_file_clear_upload'),
        'guide_text_translated': {
            'fi': form.get('guide_text_translated-fi', ''),
            'en': form.get('guide_text_translated-en', ''),
            'sv': form.get('guide_text_translated-sv', '')
        }
    }

    if toolkit.check_ckan_version(min_version='2.5'):
        upload = uploader.get_uploader('apply_permission')
    else:
        upload = uploader.Upload('apply_permission')

    if (data_dict.get('delivery_method') == 'file' and data_dict.get('file_url', None)):
        upload.update_data_dict(data_dict, 'file_url',
                                'file', 'clear_upload')
        upload.upload(max_size=uploader.get_max_resource_size())

        file_url = data_dict.get('file_url', '')
        if re.match('https?:', file_url) is None:
            # File has been updated, so update filename too
            data_dict['original_filename'] = file_url
            file_url = h.url_for_static(
                'uploads/apply_permission/%s' % file_url,
                qualified=True
            )
            data_dict['file_url'] = file_url

    if (data_dict.get('delivery_method') == 'email' and data_dict.get('require_additional_application_file') and
            data_dict.get('additional_file_url', None)):
        upload.update_data_dict(data_dict, 'additional_file_url',
                                'additional_file', 'additional_file_clear_upload')
        upload.upload(max_size=uploader.get_max_resource_size())

        additional_file_url = data_dict.get('additional_file_url', '')
        if re.match('https?:', additional_file_url) is None:
            # File has been updated, so update filename too
            data_dict['original_additional_filename'] = additional_file_url
            additional_file_url = h.url_for_static(
                'uploads/apply_permission/%s' % additional_file_url,
                qualified=True
            )
            data_dict['additional_file_url'] = additional_file_url
        elif not data_dict['original_additional_filename'] in additional_file_url:
            ''' If additional_file_url doesn't contain the original filename but it does contain
                http(s) we can assume it's been updated with an url instead of a file and we need
                to update the filename as well in order not to show the old filename for the
                download button '''
            # full url
            data_dict['original_additional_filename'] = additional_file_url
            # vs filename?
            # data_dict['original_additional_filename'] = additional_file_url.split('/')[-1]

    try:
        toolkit.get_action('service_permission_settings_update')(context, data_dict)
        pass
    except toolkit.ValidationError as e:
        return settings_get(context, subsystem_id, e.error_dict, values=data_dict)

    toolkit.h.flash_success(toolkit._('Changes saved successfully'))
    return settings_get(context, subsystem_id, values=data_dict)


def settings(subsystem_id):
    try:
        context = {u'user': toolkit.g.user, u'auth_user_obj': toolkit.g.userobj}
        if toolkit.request.method == u'POST':
            return settings_post(context, subsystem_id)
        else:
            return settings_get(context, subsystem_id)
    except toolkit.NotAuthorized:
        toolkit.abort(403, toolkit._(u'Not authorized to see this page'))


apply_permissions.add_url_rule('/dashboard/<app_type>', 'dashboard', view_func=dashboard)
apply_permissions.add_url_rule('/dashboard', 'dashboard', view_func=dashboard)
apply_permissions.add_url_rule('/new/<target_subsystem_id>', 'new_permission_application',
                               view_func=new, methods=['GET', 'POST'])
apply_permissions.add_url_rule('/view/<application_id>', 'view_permission_application', view_func=view)
apply_permissions.add_url_rule('/preview/<target_subsystem_id>', 'preview_permission_application', view_func=preview)
apply_permissions.add_url_rule('/manage/<target_subsystem_id>', 'manage_permission_applications', view_func=manage)
apply_permissions.add_url_rule('/settings/<subsystem_id>', 'permission_application_settings',
                               view_func=settings, methods=['GET', 'POST'])


def get_blueprints():
    return [apply_permissions]
