from ckan.plugins import toolkit as tk
from ... import model
import logging

_ = tk._
log = logging.getLogger(__name__)



def service_permission_application_create(context, data_dict):
    tk.check_access('service_permission_application_create', context, data_dict)

    errors = {}
    error_summary = {}

    organization = data_dict.get('organization')
    if organization is None or organization == "":
        errors['organization_id'] = _('Missing value')
    business_code = data_dict.get('business_code')
    if business_code is None or business_code == "":
        errors['business_code'] = _('Missing value')
    contact_name = data_dict.get('contact_name')
    if contact_name is None or contact_name == "":
        errors['contact_name'] = _('Missing value')
    contact_email = data_dict.get('contact_email')
    if contact_email is None or contact_email == "":
        errors['contact_email'] = _('Missing value')
    ip_address_list = data_dict.get('ip_address_list')
    if ip_address_list is None or ip_address_list == "":
        errors['ip_address_list'] = _('Missing value')
    subsystem_id = data_dict.get('subsystem_id')
    if subsystem_id is None or subsystem_id == "":
        errors['subsystem_id'] = _('Missing value')
    subsystem_code = data_dict.get('subsystem_code')
    if subsystem_code is None or subsystem_code == "":
        errors['subsystem_code'] = _('Missing value')
    service_code = data_dict.get('service_code')
    if service_code is None or service_code == "":
        errors['service_code'] = _('Missing value')


    if errors:
        raise tk.ValidationError(errors)

    usage_description = data_dict.get('usage_description')
    request_date = data_dict.get('request_date')



    model.ApplyPermission.create(organization=organization, business_code=business_code,
                                 contact_name=contact_name,
                                 contact_email=contact_email,
                                 ip_address_list=ip_address_list,
                                 subsystem_id=subsystem_id,
                                 subsystem_code=subsystem_code,
                                 service_code=service_code,
                                 usage_description=usage_description,
                                 request_date=request_date)

