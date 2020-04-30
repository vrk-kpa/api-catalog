from ckan.logic import NotFound, check_access, side_effect_free

@side_effect_free
def service_permission_application_list(context, data_dict):
    check_access('service_permission_application_list', context, data_dict)
    return [service_permission_application_show(context, {'application_id': str(i)}) for i in range(10)]

@side_effect_free
def service_permission_application_show(context, data_dict):
    check_access('service_permission_application_show', context, data_dict)
    application_id = data_dict.get('application_id')

    if application_id is None:
        raise NotFound

    return {'id': application_id}
