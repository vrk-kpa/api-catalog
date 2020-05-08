from ckan.plugins import toolkit as tk
import ckanext.apply_permissions_for_service.model

_ = tk._

def service_permission_application_create(context, data_dict):
    tk.check_access('service_permission_application_create', context, data_dict)

    errors = {}
    error_summary = {}

    organization = data_dict.get('organization')
    if organization is None:
        errors['organization'] = _('Missing value')
    vat_id = data_dict.get('vat_id')
    if vat_id is None:
        errors['vat_id'] = _('Missing value')
    contact_person_name = data_dict.get('contact_person_name')
    if contact_person_name is None:
        errors['contact_person_name'] = _('Missing value')
    contact_person_email = data_dict.get('contact_person_email')
    if contact_person_email is None:
        errors['contact_person_email'] = _('Missing value')
    ip_address_list = data_dict.get('ip_address_list')
    if ip_address_list is None:
        errors['ip_address_list'] = _('Missing value')
    subsystem_code = data_dict.get('subsystem_code')
    if subsystem_code is None:
        errors['subsystem_code'] = _('Missing value')
    api_id = data_dict.get('api_id')
    if api_id is None:
        errors['api_id'] = _('Missing value')

    if errors:
        raise tk.ValidationError(errors)

    request_description = data_dict.get('api_id')


    model.ApplyPermission.create(organization=organization, vat_id=vat_id,
                                 contact_person_name=contact_person_name,
                                 contact_person_email=contact_person_email,
                                 ip_address_list=ip_address_list,
                                 subsystem_code=subsystem_code,
                                 api_id=api_id,
                                 request_description=request_description)

