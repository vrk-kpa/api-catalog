import json

from ckan import plugins

def service_permission_settings_update(context, data_dict):
    plugins.toolkit.check_access('service_permission_settings', context, data_dict)
    subsystem_id = data_dict.get('subsystem_id')

    if subsystem_id is None:
        raise NotFound

    pkg = plugins.toolkit.get_action('package_show')(context, {'id': subsystem_id})
    settings = {field: data_dict[field]
                for field in ('delivery_method', 'api', 'web', 'email')
                if field in data_dict}

    plugins.toolkit.get_action('package_patch')(context, {
        'id': data_dict['subsystem_id'],
        'service_permission_settings': json.dumps(settings)
        })

    return settings


