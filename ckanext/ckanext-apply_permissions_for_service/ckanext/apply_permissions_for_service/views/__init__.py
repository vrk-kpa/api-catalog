import ckan.plugins as plugins
from logging import getLogger

log = getLogger(__name__)

def index():
    context = {u'user': plugins.toolkit.g.user, u'auth_user_obj': plugins.toolkit.g.userobj}
    data_dict = {}
    applications = plugins.toolkit.get_action('service_permission_application_list')(context, data_dict)
    extra_vars = {
            'sent_applications': applications.get('sent', []),
            'received_applications': applications.get('received', [])
            }
    return plugins.toolkit.render('apply_permissions_for_service/index.html', extra_vars=extra_vars)

def new(subsystem_id):
    context = {u'user': plugins.toolkit.g.user, u'auth_user_obj': plugins.toolkit.g.userobj}
    if plugins.toolkit.request.method == u'POST':
        form = plugins.toolkit.request.form
        data_dict = {
                'organization': form.get('organization'),
                'business_code': form.get('businessCode'),
                'contact_name': form.get('contactName'),
                'contact_email': form.get('contactEmail'),
                'subsystem_id': form.get('subsystemId'),
                'subsystem_code': form.get('subsystemCode'),
                'service_code': form.getlist('serviceCode'),
                'ip_address': form.get('ip_addresses'),
                'request_date': form.get('requestDate'),
                'usage_description': form.get('usageDescription'),
                }
        plugins.toolkit.get_action('service_permission_application_create')(context, data_dict)
        return plugins.toolkit.render('apply_permissions_for_service/sent.html')
    else:
        service_id = plugins.toolkit.request.args.get('service_id')
        package = plugins.toolkit.get_action('package_show')(context, {'id': subsystem_id})
        organization = plugins.toolkit.get_action('organization_show')(context, {'id': package['owner_org']})
        user_managed_organizations = plugins.toolkit.get_action('organization_list_for_user')(context, {
            'permission': 'manage_group'
            })
        user_managed_datasets_query = 'owner_org:({})'.format(' OR '.join(o['id'] for o in user_managed_organizations))
        user_managed_datasets = plugins.toolkit.get_action('package_search')(context, {
            'q': user_managed_datasets_query
            }).get('results', []) if user_managed_organizations else []

        log.info(plugins.toolkit.g)
        extra_vars = {
                'subsystem_id': subsystem_id,
                'service_id': service_id,
                'pkg': package,
                'org': organization,
                'user': plugins.toolkit.g.userobj,
                'user_managed_organizations': user_managed_organizations,
                'user_managed_datasets': user_managed_datasets
                }
        return plugins.toolkit.render('apply_permissions_for_service/new.html', extra_vars=extra_vars)

def view(application_id):
    context = {u'user': plugins.toolkit.g.user, u'auth_user_obj': plugins.toolkit.g.userobj}
    data_dict = {'id': application_id}
    application = plugins.toolkit.get_action('service_permission_application_show')(context, data_dict)
    extra_vars = {'application': application}
    return plugins.toolkit.render('apply_permissions_for_service/view.html', extra_vars=extra_vars)

