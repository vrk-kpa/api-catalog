from ckan.logic import check_access

def service_permission_application_create(context, data_dict):
    check_access('service_permission_application_create', context, data_dict)
    return ''

