from ckan.plugins import toolkit
from ckanext.apply_permissions_for_service import model


def service_permission_application_list(context, data_dict):
    return {'success': True}


def service_permission_application_show(context, data_dict):

    permission_application_id = toolkit.get_or_bust(data_dict, 'id')
    application = model.ApplyPermission.get(permission_application_id).as_dict()
    organization = application.get('organization')
    target_organization = application.get('target_organization')
    membership_organizations = toolkit.get_action('organization_list_for_user')(context, {'permission': 'read'})

    if any(True for x in (org.get('id') for org in membership_organizations)
           if x in (organization['id'], target_organization['id'])):
        return {'success': True}

    return {'success': False,
            "msg": toolkit._("User not authorized to view permission application.")}


def service_permission_settings(context, data_dict):
    return {'success': toolkit.check_access('package_update', context, {'id': data_dict['subsystem_id']})}


def service_permission_application_create(context, data_dict):
    editor_or_admin_orgs = toolkit.get_action('organization_list_for_user')(context, {'permission': 'create_dataset'})
    return {'success': len(editor_or_admin_orgs) > 0}
