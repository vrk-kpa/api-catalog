import ckan.plugins.toolkit as toolkit
from flask import Blueprint
from logging import getLogger

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
    data_dict = {
            'organization': form.get('organization'),
            'business_code': form.get('businessCode'),
            'contact_name': form.get('contactName'),
            'contact_email': form.get('contactEmail'),
            'subsystem_id': form.get('subsystemId'),
            'subsystem_code': form.get('subsystemCode'),
            'service_code_list': form.getlist('serviceCode'),
            'ip_address_list': [ip for ip in form.getlist('ipAddress') if ip],
            'request_date': form.get('requestDate'),
            'usage_description': form.get('usageDescription'),
            }

    try:
        toolkit.get_action('service_permission_application_create')(context, data_dict)
    except toolkit.ValidationError as e:
        return new_get(context, subsystem_id, e.error_dict, values=data_dict)

    return toolkit.render('apply_permissions_for_service/sent.html')


def new_get(context, subsystem_id, errors={}, values={}):
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


def manage(subsystem_id):
    context = {u'user': toolkit.g.user, u'auth_user_obj': toolkit.g.userobj}
    package = toolkit.get_action('package_show')(context, {'id': subsystem_id})
    toolkit.c.pkg_dict = package

    data_dict = {'subsystem_id': subsystem_id}
    applications = toolkit.get_action('service_permission_application_list')(context, data_dict)

    extra_vars = {
            'subsystem_id': subsystem_id,
            'pkg': package,
            'applications': applications
            }
    return toolkit.render('apply_permissions_for_service/manage.html', extra_vars=extra_vars)


def settings_get(context, subsystem_id, errors={}, values=None):
    package = toolkit.get_action('package_show')(context, {'id': subsystem_id})
    toolkit.c.pkg_dict = package
    settings = values or toolkit.get_action('service_permission_settings_show')(context, {'subsystem_id': subsystem_id})

    extra_vars = {
            'subsystem_id': subsystem_id,
            'pkg': package,
            'errors': errors,
            'settings': settings,
            }

    return toolkit.render('apply_permissions_for_service/settings.html', extra_vars=extra_vars)


def settings_post(context, subsystem_id):
    form = toolkit.request.form
    data_dict = {
            'subsystem_id': subsystem_id,
            'delivery_method': form.get('deliveryMethod'),
            'email': form.get('email'),
            'api': form.get('api'),
            'web': form.get('web')
            }

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
apply_permissions.add_url_rule('/manage/<subsystem_id>', 'manage_permission_applications', view_func=manage)
apply_permissions.add_url_rule('/settings/<subsystem_id>', 'permission_application_settings', view_func=settings, methods=['GET', 'POST'])


def get_blueprints():
    return [apply_permissions]