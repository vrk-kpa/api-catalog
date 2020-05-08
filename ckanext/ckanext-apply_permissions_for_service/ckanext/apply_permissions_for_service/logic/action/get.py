from ckan.logic import NotFound, check_access, side_effect_free
from ckan import plugins

@side_effect_free
def service_permission_application_list(context, data_dict):
    check_access('service_permission_application_list', context, data_dict)
    result = {
            'sent': [service_permission_application_show(context, {'id': str(i)})
                     for i in range(10)],
            'received': [service_permission_application_show(context, {'id': str(i)})
                         for i in range(10, 20)]
            }
    return result

@side_effect_free
def service_permission_application_show(context, data_dict):
    check_access('service_permission_application_show', context, data_dict)
    application_id = data_dict.get('id')

    if application_id is None:
        raise NotFound

    packages = plugins.toolkit.get_action('package_search')(context, {}).get('results', [])
    fake_count = 10
    random_from = packages[int(application_id) % len(packages)]
    random_to = packages[(7 * int(application_id) + 3) % len(packages)]
    return {
        'id': str(application_id),
        'from': {
            'subsystem': random_from,
            },
        'to': {
            'subsystem': random_to,
            'services': random_to['resources']
            },
        'organization': random_from.get('organization', {}).get('name'),
        'business_code': '%07d-%d' % (int(application_id) % 10000000, int(application_id) % 10),
        'contact_name': 'Person %s' % application_id,
        'contact_email': 'person%s@%s.doesnot.exist' % (application_id, random_from['organization']['name']),
        'ip_addresses': ['127.0.0.1', '10.0.0.1'],
        'usage_description': 'Lorem ipsum, dolor sit amet.',
        'request_date': '2020-01-01'
        }
