from ckan.plugins import toolkit as tk
import model
import ckan.model as ckan_model

def service_permission_application_create(context, data_dict):
    tk.check_access('service_permission_application_create', context, data_dict)

    organization = data_dict.get('organization')
    vat_id = data_dict.get('vat_id')
    contact_person_name = data_dict.get('contact_person_name')
    contact_person_email = data_dict.get('contact_person_email')
    ip_address_list = data_dict.get('ip_address_list')
    subsystem_code = data_dict.get('subsystem_code')

    api_id = data_dict.get('api_id')
    request_description = data_dict.get('api_id')

    model.ApplyPermission.create(organization=organization, vat_id=vat_id,
                          contact_person_name=contact_person_name,
                          contact_person_email=contact_person_email,
                          ip_address_list=ip_address_list,
                          subsystem_code=subsystem_code,
                          api_id=api_id,
                          request_description=request_description)

