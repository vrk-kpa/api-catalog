# -*- coding: utf-8 -*-

from ckan.plugins import toolkit as tk
from ckan.lib.mailer import mail_user
from ckan.model.user import User
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
    service_code_list = data_dict.get('service_code_list')
    if service_code_list is None or service_code_list == "":
        errors['service_code_list'] = _('Missing value')


    if errors:
        raise tk.ValidationError(errors)

    usage_description = data_dict.get('usage_description')
    request_date = data_dict.get('request_date') or None

    # Determine notification email recipients before creating the application
    # in case there are errors
    package = tk.get_action('package_show')(context, {'id': subsystem_id})

    system_context = {'ignore_auth': True}
    package_org_admin_members = tk.get_action('member_list')(system_context, {
        'id': package['owner_org'],
        'object_type': 'user',
        'capacity': 'admin'
        })

    package_org_admin_users = [User.get(uid) for uid, t, c in package_org_admin_members]

    application_id = model.ApplyPermission.create(organization=organization,
                                                  business_code=business_code,
                                                  contact_name=contact_name,
                                                  contact_email=contact_email,
                                                  ip_address_list=ip_address_list,
                                                  subsystem_id=subsystem_id,
                                                  subsystem_code=subsystem_code,
                                                  service_code_list=service_code_list,
                                                  usage_description=usage_description,
                                                  request_date=request_date)


    application = model.ApplyPermission.get(application_id).as_dict()
    email_subject = u'{} pyytää lupaa käyttää Suomi.fi-palveluväylässä tarjoamaasi palvelua'.format(
            application['organization'])
    email_content = tk.render('apply_permissions_for_service/notification_email.html',
                              extra_vars={'application': application})

    log.info('Sending application notification emails to {} users'.format(len(package_org_admin_users)))
    for u in package_org_admin_users:
        try:
            mail_user(u, email_subject, email_content, headers={'content-type': 'text/html'})
        except Exception as e:
            # Email exceptions are not user relevant nor action critical, but should be logged
            log.warning(e)
