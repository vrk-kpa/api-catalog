import ckan.plugins as plugins
from plugins.toolkit import _, h, g, get_action, ValidationError, NotAuthorized
from logging import getLogger

log = getLogger(__name__)


def index():
    try:
        context = {u'user': g.user, u'auth_user_obj': g.userobj}
        data_dict = {}
        applications = get_action('service_permission_application_list')(context, data_dict)
        extra_vars = {
                'sent_applications': applications.get('sent', []),
                'received_applications': applications.get('received', [])
                }
        return plugins.toolkit.render('apply_permissions_for_service/index.html', extra_vars=extra_vars)
    except NotAuthorized:
        plugins.toolkit.abort(403, plugins.toolkit._(u'Not authorized to see this page'))


def new_post(context, subsystem_id):
    form = plugins.toolkit.request.form
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
        get_action('service_permission_application_create')(context, data_dict)
    except ValidationError as e:
        return new_get(context, subsystem_id, e.error_dict, values=data_dict)

    return plugins.toolkit.render('apply_permissions_for_service/sent.html')


def new_get(context, subsystem_id, errors={}, values={}):
    service_id = plugins.toolkit.request.args.get('service_id')
    package = get_action('package_show')(context, {'id': subsystem_id})
    organization = get_action('organization_show')(context, {'id': package['owner_org']})
    user_managed_organizations = get_action('organization_list_for_user')(context, {
        'permission': 'manage_group'
        })
    user_managed_datasets_query = 'owner_org:({})'.format(' OR '.join(o['id'] for o in user_managed_organizations))
    user_managed_datasets = get_action('package_search')(context, {
        'q': user_managed_datasets_query,
        'include_private': True,
        'rows': 1000
        }).get('results', []) if user_managed_organizations else []

    log.info(g)
    extra_vars = {
            'subsystem_id': subsystem_id,
            'service_id': service_id,
            'pkg': package,
            'service': next((r for r in package.get('resources', []) if r['id'] == service_id), None),
            'org': organization,
            'user': g.userobj,
            'user_managed_organizations': user_managed_organizations,
            'user_managed_datasets': user_managed_datasets,
            'values': values,
            'errors': errors
            }
    return plugins.toolkit.render('apply_permissions_for_service/new.html', extra_vars=extra_vars)


def new(subsystem_id):
    try:
        context = {u'user': g.user, u'auth_user_obj': g.userobj}
        plugins.toolkit.check_access('service_permission_application_create', context, {})

        if plugins.toolkit.request.method == u'POST':
            return new_post(context, subsystem_id)
        else:
            return new_get(context, subsystem_id)
    except NotAuthorized:
        plugins.toolkit.abort(403, plugins.toolkit._(u'Not authorized to see this page'))

def view(application_id):
    try:
        context = {u'user': g.user, u'auth_user_obj': g.userobj}
        data_dict = {'id': application_id}
        application = get_action('service_permission_application_show')(context, data_dict)
        extra_vars = {'application': application}
        return plugins.toolkit.render('apply_permissions_for_service/view.html', extra_vars=extra_vars)
    except NotAuthorized:
        plugins.toolkit.abort(403, plugins.toolkit._(u'Not authorized to see this page'))

