from ckan.plugins import toolkit


def service_permission_application_list(context, data_dict):
    return {'success': True}


def service_permission_application_show(context, data_dict):
    return {'success': True}


def service_permission_settings(context, data_dict):
    return {'success': toolkit.check_access('package_update', context, {'id': data_dict['subsystem_id']})}


def service_permission_application_create(context, data_dict):
    editor_or_admin_orgs = toolkit.get_action('organization_list_for_user')(context, {'permission': 'create_dataset'})
    return {'success': len(editor_or_admin_orgs) > 0}
