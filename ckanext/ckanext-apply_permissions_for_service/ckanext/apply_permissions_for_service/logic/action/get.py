from ckan.logic import NotFound, check_access, side_effect_free
from ckan import plugins
from ckan import model

from ... import model as apply_permission_model


@side_effect_free
def service_permission_application_list(context, data_dict):
    check_access('service_permission_application_list', context, data_dict)

    applications = model.Session.query(apply_permission_model.ApplyPermission)

    subsystem_id = data_dict.get('subsystem_id')
    if subsystem_id:
        applications = applications.filter(apply_permission_model.ApplyPermission.subsystem_id == subsystem_id)

    applications = applications.all()

    return [application.as_dict() for application in applications]


@side_effect_free
def service_permission_application_show(context, data_dict):
    check_access('service_permission_application_show', context, data_dict)
    application_id = data_dict.get('id')

    if application_id is None:
        raise NotFound

    application = apply_permission_model.ApplyPermission.get(application_id).as_dict()
    return application


@side_effect_free
def service_permission_settings_show(context, data_dict):
    check_access('service_permission_settings', context, data_dict)
    subsystem_id = data_dict.get('subsystem_id')

    if subsystem_id is None:
        raise NotFound

    pkg = plugins.toolkit.get_action('package_show')(context, {'id': subsystem_id})

    return pkg.get('service_permission_settings', {})
