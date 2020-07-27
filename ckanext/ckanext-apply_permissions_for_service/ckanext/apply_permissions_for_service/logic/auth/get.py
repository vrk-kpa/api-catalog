from ckan.plugins import toolkit

def service_permission_application_list(context, data_dict):
    return {'success': True}

def service_permission_application_show(context, data_dict):
    return {'success': True}

def service_permission_settings(context, data_dict):
    return {'success': toolkit.check_access('package_update', context, {'id': data_dict['subsystem_id']})}
