from ckan.logic import NotFound, check_access, side_effect_free
from ckan import plugins

from ... import model

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

    application = model.ApplyPermission.get(application_id).as_dict()
    return application

