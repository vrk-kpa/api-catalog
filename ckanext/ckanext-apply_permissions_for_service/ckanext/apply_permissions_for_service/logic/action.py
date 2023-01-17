# -*- coding: utf-8 -*-
import json

from ckan.plugins import toolkit as tk
from ckan import model as ckan_model
from ckan.logic import NotFound
from ckan.lib.mailer import mail_recipient
import ckan.lib.helpers as h
from .. import model
import logging
from ckanext.apply_permissions_for_service.helpers import get_application_attachment

_ = tk._

check_access = tk.check_access
side_effect_free = tk.side_effect_free
log = logging.getLogger(__name__)


def service_permission_application_create(context, data_dict):
    tk.check_access('service_permission_application_create', context, data_dict)

    errors = {}

    organization_id = data_dict.get('organization_id')
    if organization_id is None or organization_id == "":
        errors['organization_id'] = _('Missing value')

    intermediate_organization_id = data_dict.get('intermediate_organization_id')

    target_organization_id = data_dict.get('target_organization_id')
    if target_organization_id is None or target_organization_id == "":
        errors['target_organization_id'] = _('Missing value')

    member_code = data_dict.get('member_code')
    if member_code is None or member_code == "":
        errors['member_code'] = _('Missing value')
    else:
        try:
            # From ckanext-apicatalog
            tk.get_validator('business_id_validator')(member_code)
        except tk.Invalid as e:
            errors['member_code'] = e.error

    intermediate_member_code = data_dict.get('intermediate_member_code')
    if intermediate_member_code:
        try:
            tk.get_validator('business_id_validator')(intermediate_member_code)
        except tk.Invalid as e:
            errors['intermediate_member_code'] = e.error

    contact_name = data_dict.get('contact_name')
    if contact_name is None or contact_name == "":
        errors['contact_name'] = _('Missing value')

    contact_email = data_dict.get('contact_email')
    if contact_email is None or contact_email == "":
        errors['contact_email'] = _('Missing value')
    else:
        try:
            tk.get_validator('email_validator')(contact_email, context)
        except tk.Invalid as e:
            errors['contact_email'] = e.error

    ip_address_list = data_dict.get('ip_address_list')
    if not (isinstance(ip_address_list, list) and any(ip_address_list)):
        errors['ip_address_list'] = _('Missing value')
    target_subsystem_id = data_dict.get('target_subsystem_id')
    if target_subsystem_id is None or target_subsystem_id == "":
        errors['target_subsystem_id'] = _('Missing value')

    '''
    subsystem_id (previously subsystem_code) must exist and match subsystem belonging to the selected utilizing organization
    utilizing organization is always organization(_id), the orgazination using the data regardless of whether they made
    the application themselves or an intermediate_organization did it for them
    '''
    subsystem_id = data_dict.get('subsystem_id')
    if subsystem_id is None or subsystem_id == "":
        errors['subsystem_id'] = _('Missing value')
    else:
        subsystem = tk.get_action('package_show')(context, {'id': subsystem_id})
        if not subsystem.get('owner_org', '').endswith(member_code):
            errors['subsystem_id'] = _('Selected subsystem does not belong to the utilizing organization')

    service_id_list = data_dict.get('service_id_list')
    if not service_id_list:
        errors['service_id_list'] = _('Missing value')

    if errors:
        raise tk.ValidationError(errors)

    usage_description = data_dict.get('usage_description')
    request_date = data_dict.get('request_date') or None
    application_filename = data_dict.get('application_filename') or None

    # Need sysadmin privileges to see permission_application_settings
    sysadmin_context = {'ignore_auth': True, 'use_cache': False}
    package = tk.get_action('package_show')(sysadmin_context, {'id': subsystem_id})
    owner_org = tk.get_action('organization_show')(context, {'id': package['owner_org']})

    application_id = model.ApplyPermission.create(organization_id=organization_id,
                                                  target_organization_id=target_organization_id,
                                                  intermediate_organization_id=intermediate_organization_id,
                                                  member_code=member_code,
                                                  intermediate_member_code=intermediate_member_code,
                                                  contact_name=contact_name,
                                                  contact_email=contact_email,
                                                  ip_address_list=ip_address_list,
                                                  target_subsystem_id=target_subsystem_id,
                                                  subsystem_id=subsystem_id,
                                                  service_id_list=service_id_list,
                                                  usage_description=usage_description,
                                                  request_date=request_date,
                                                  application_filename=application_filename)

    service_permission_settings = package.get('service_permission_settings', {})
    delivery_method = service_permission_settings.get('delivery_method', 'email')

    if delivery_method == 'email':
        email_address = service_permission_settings.get('email', owner_org.get('email_address'))
        if email_address:
            log.info('Sending permission application notification email to {}'.format(email_address))
            application = model.ApplyPermission.get(application_id).as_dict()
            email_subject = u'{} pyytää lupaa käyttää Suomi.fi-palveluväylässä tarjoamaasi palvelua'.format(
                application['organization']['title'])
            email_content = tk.render('apply_permissions_for_service/notification_email.html',
                                      extra_vars={'application': application})
            try:
                if application_filename:
                    with get_application_attachment(application_filename) as file:
                        mail_recipient(owner_org['title'], email_address, email_subject, email_content,
                                       headers={'Content-Type': 'text/html'}, attachments=[(application_filename, file)])
                else:
                    mail_recipient(owner_org['title'], email_address, email_subject, email_content,
                                   headers={'Content-Type': 'text/html'})
            except Exception as e:
                # Email exceptions are not user relevant nor action critical, but should be logged
                log.warning(e)
        else:
            log.info('Organization %s has no email address defined, not sending permission application notification.',
                     owner_org['name'])


@side_effect_free
def service_permission_application_list(context, data_dict):
    check_access('service_permission_application_list', context, data_dict)
    applications = ckan_model.Session.query(model.ApplyPermission)

    target_subsystem_id = data_dict.get('target_subsystem_id')
    if target_subsystem_id:
        applications = applications.filter(model.ApplyPermission.target_subsystem_id == target_subsystem_id)

    applications = applications.all()

    if not target_subsystem_id:
        membership_organizations = tk.get_action('organization_list_for_user')(context, {'permission': 'read'})
        organization_id_list = [org['id'] for org in membership_organizations]
        response = {'received': [], 'sent': []}
        for application in applications:
            application_dict = application.as_dict()
            if len(application_dict.get('services')) > 0:
                if application_dict.get('organization_id') in organization_id_list:
                    response['sent'].append(application_dict)
                if application_dict.get('target_organization_id') in organization_id_list:
                    response['received'].append(application_dict)
    else:
        response = [application.as_dict() for application in applications]

    return response


@side_effect_free
def service_permission_application_show(context, data_dict):
    check_access('service_permission_application_show', context, data_dict)
    application_id = data_dict.get('id')

    if application_id is None:
        raise NotFound

    application = model.ApplyPermission.get(application_id).as_dict()

    filename = application.get('application_filename')
    if filename and not filename.startswith('http'):
        application['application_fileurl'] = h.url_for_static(
            'uploads/apply_permission/%s' % filename,
            qualified=True
        )
    elif filename and filename.startswith('http'):
        application['application_fileurl'] = filename

    return application


@side_effect_free
def service_permission_settings_show(context, data_dict):
    check_access('service_permission_settings', context, data_dict)
    subsystem_id = data_dict.get('subsystem_id')

    if subsystem_id is None:
        raise NotFound

    pkg = tk.get_action('package_show')(context, {'id': subsystem_id})

    return pkg.get('service_permission_settings', {})


def service_permission_settings_update(context, data_dict):
    tk.check_access('service_permission_settings', context, data_dict)
    subsystem_id = data_dict.get('subsystem_id')

    if subsystem_id is None:
        raise NotFound

    settings = {field: data_dict[field]
                for field in ('delivery_method', 'web', 'email', 'file_url', 'original_filename',
                              'require_additional_application_file', 'additional_file_url', 'original_additional_filename',
                              'guide_text_translated')
                if field in data_dict}

    if settings.get('delivery_method') == 'file' and not settings.get('file_url', None):
        raise tk.ValidationError({'file_url': _("You must provide application file when \
                                                 'Organisation’s downloadable application (PDF)' is selected")})

    if (settings.get('delivery_method') == 'email' and settings.get('require_additional_application_file') and
            not settings.get('additional_file_url', None)):
        raise tk.ValidationError({'additional_file_url': _("You must provide additional file when \
                                                            'Request additional info with an attachment' is selected")})

    tk.get_action('package_patch')(context, {
        'id': data_dict['subsystem_id'],
        'service_permission_settings': json.dumps(settings)
    })

    return settings
