from ckan.logic import NotFound, check_access, side_effect_free
from ckan import plugins
from ckan import model

from ... import model as apply_permission_model

@side_effect_free
def service_permission_application_list(context, data_dict):
    check_access('service_permission_application_list', context, data_dict)

    applications = model.Session.query(apply_permission_model.ApplyPermission).all()

    return {"sent":[application.as_dict() for application in applications]}

@side_effect_free
def service_permission_application_show(context, data_dict):
    check_access('service_permission_application_show', context, data_dict)
    application_id = data_dict.get('id')

    if application_id is None:
        raise NotFound

    application = apply_permission_model.ApplyPermission.get(application_id).as_dict()
    return application

