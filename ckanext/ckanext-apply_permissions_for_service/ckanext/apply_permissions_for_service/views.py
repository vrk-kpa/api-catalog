from builtins import next
import ckan.lib.uploader as uploader
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h
from flask import Blueprint
from logging import getLogger
import re

log = getLogger(__name__)

apply_permissions = Blueprint("apply_permissions", __name__, url_prefix=u'/apply_permissions_for_service')


def index():
    try:
        subsystem_id = toolkit.request.args.get('id')
        context = {u'user': toolkit.g.user, u'auth_user_obj': toolkit.g.userobj}
        data_dict = {'subsystem_id': subsystem_id}
        applications = toolkit.get_action('service_permission_application_list')(context, data_dict)
        extra_vars = {
                'sent_applications': applications,
                'received_applications': applications
                }
        return toolkit.render('apply_permissions_for_service/index.html', extra_vars=extra_vars)
    except toolkit.NotAuthorized:
        toolkit.abort(403, toolkit._(u'Not authorized to see this page'))


def new_post(context, subsystem_id):
    form = toolkit.request.form
    files = toolkit.request.files

    data_dict = {
            'target_organization_id': form.get('target_organization_id'),
            'intermediate_organization_id': form.get('intermediate_organization_id'),
            'business_code': form.get('businessCode'),
            'intermediate_business_code': form.get('intermediate_business_code'),
            'contact_name': form.get('contactName'),
            'contact_email': form.get('contactEmail'),
            'subsystem_id': form.get('subsystemId'),
            'subsystem_code': form.get('subsystemCode'),
            'service_code_list': form.getlist('serviceCode'),
            'ip_address_list': [ip for ip in form.getlist('ipAddress') if ip],
            'request_date': form.get('requestDate'),
            'usage_description': form.get('usageDescription'),
            'file': files.get('file'),
            'file_url': form.get('file_url'),
            'clear_upload': form.get('clear_upload'),
            }

    try:
        organization = toolkit.get_action('organization_show')(context, {'id': form['organization']})
        data_dict['organization_id'] = organization['id']

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
        return new_get(context, subsystem_id, e.error_dict, values=data_dict)

    return toolkit.render('apply_permissions_for_service/sent.html')


def new_get(context, subsystem_id, errors={}, values={}, preview=False):
    service_id = toolkit.request.args.get('service_id')
    package = toolkit.get_action('package_show')(context, {'id': subsystem_id})

    if package.get('service_permission_settings', {}).get('delivery_method') == "none" \
            or package.get('service_permission_settings', {}).get('delivery_method') is None:
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
            'subsystem_id': subsystem_id,
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


def new(subsystem_id):
    try:
        context = {u'user': toolkit.g.user, u'auth_user_obj': toolkit.g.userobj}
        toolkit.check_access('service_permission_application_create', context, {})

        if toolkit.request.method == u'POST':
            return new_post(context, subsystem_id)
        else:
            return new_get(context, subsystem_id)
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


def preview(subsystem_id):
    try:
        context = {u'user': toolkit.g.user, u'auth_user_obj': toolkit.g.userobj}
        toolkit.check_access('service_permission_application_create', context, {})
        return new_get(context, subsystem_id, preview=True)
    except toolkit.NotAuthorized:
        toolkit.abort(403, toolkit._(u'Not authorized to see this page'))


def manage(subsystem_id):
    context = {u'user': toolkit.g.user, u'auth_user_obj': toolkit.g.userobj}
    package = toolkit.get_action('package_show')(context, {'id': subsystem_id})
    toolkit.c.pkg_dict = package

    data_dict = {'subsystem_id': subsystem_id}
    applications = toolkit.get_action('service_permission_application_list')(context, data_dict)

    extra_vars = {
            'subsystem_id': subsystem_id,
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
        'original_filename': form.get('file_url'),
        'clear_upload': form.get('clear_upload'),
        'web': form.get('web')
    }

    if toolkit.check_ckan_version(min_version='2.5'):
        upload = uploader.get_uploader('apply_permission')
    else:
        upload = uploader.Upload('apply_permission')

    upload.update_data_dict(data_dict, 'file_url',
                            'file', 'clear_upload')
    upload.upload(max_size=uploader.get_max_resource_size())

    file_url = data_dict.get('file_url', '')
    if re.match('https?:', file_url) is None:
        file_url = h.url_for_static(
            'uploads/apply_permission/%s' % file_url,
            qualified=True
        )
        data_dict['file_url'] = file_url

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


apply_permissions.add_url_rule('/', 'list_permission_applications', view_func=index)
apply_permissions.add_url_rule('/new/<subsystem_id>', 'new_permission_application', view_func=new, methods=['GET', 'POST'])
apply_permissions.add_url_rule('/view/<application_id>', 'view_permission_application', view_func=view)
apply_permissions.add_url_rule('/preview/<subsystem_id>', 'preview_permission_application', view_func=preview)
apply_permissions.add_url_rule('/manage/<subsystem_id>', 'manage_permission_applications', view_func=manage)
apply_permissions.add_url_rule('/settings/<subsystem_id>', 'permission_application_settings',
                               view_func=settings, methods=['GET', 'POST'])


def get_blueprints():
    return [apply_permissions]
