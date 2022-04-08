from builtins import str
import uuid

from ckan import model
from ckan.lib import dictization
from ckan.plugins import toolkit
from sqlalchemy import Column, types
from sqlalchemy.ext.declarative import declarative_base

import logging
log = logging.getLogger(__name__)

Base = declarative_base()


def make_uuid():
    return str(uuid.uuid4())


class ApplyPermission(Base):

    __tablename__ = 'apply_permission'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    organization_id = Column(types.UnicodeText, nullable=False)
    intermediate_organization_id = Column(types.UnicodeText, nullable=True)
    target_organization_id = Column(types.UnicodeText, nullable=False)
    business_code = Column(types.UnicodeText, nullable=False)
    intermediate_business_code = Column(types.UnicodeText, nullable=True)
    contact_name = Column(types.UnicodeText, nullable=False)
    contact_email = Column(types.UnicodeText, nullable=False)
    ip_address_list = Column(types.JSON, nullable=False)
    subsystem_id = Column(types.UnicodeText, nullable=False)
    subsystem_code = Column(types.UnicodeText, nullable=False)
    service_code_list = Column(types.JSON, nullable=False)

    usage_description = Column(types.UnicodeText)
    request_date = Column(types.Date)
    application_filename = Column(types.UnicodeText)

    @classmethod
    def create(cls, organization_id, target_organization_id, intermediate_organization_id, business_code,
               intermediate_business_code, contact_name, contact_email, ip_address_list, subsystem_code,
               subsystem_id, service_code_list, usage_description, request_date, application_filename=None):

        apply_permission = ApplyPermission(organization_id=organization_id,
                                           target_organization_id=target_organization_id,
                                           intermediate_organization_id=intermediate_organization_id,
                                           business_code=business_code,
                                           intermediate_business_code=intermediate_business_code,
                                           contact_name=contact_name,
                                           contact_email=contact_email,
                                           ip_address_list=ip_address_list,
                                           subsystem_code=subsystem_code,
                                           subsystem_id=subsystem_id,
                                           service_code_list=service_code_list,
                                           usage_description=usage_description,
                                           request_date=request_date,
                                           application_filename=application_filename)
        model.Session.add(apply_permission)
        model.repo.commit()
        return apply_permission.id

    @classmethod
    def get(cls, application_id):
        return model.Session.query(cls).filter(cls.id == application_id).first()

    def as_dict(self):
        context = {'model': model}
        application_dict = dictization.table_dictize(self, context)

        application_dict['requester_subsystem'] = toolkit.get_action('package_show')(
            {'ignore_auth': True}, {'id': application_dict['subsystem_id']})

        application_dict['subsystem'] = toolkit.get_action('package_show')(
            {'ignore_auth': True}, {'id': application_dict['subsystem_code']})
        application_dict['member'] = toolkit.get_action('organization_show')(
            {'ignore_auth': True}, {'id': application_dict['subsystem']['owner_org']})
        application_dict['services'] = [toolkit.get_action('resource_show')(
            {'ignore_auth': True}, {'id': service}) for service in application_dict['service_code_list']]

        application_dict['organization'] = toolkit.get_action('organization_show')(
            {'ignore_auth': True}, {'id': application_dict['organization_id']})

        application_dict['target_organization'] = toolkit.get_action('organization_show')(
            {'ignore_auth': True}, {'id': application_dict['target_organization_id']})

        application_dict['intermediate_organization'] = toolkit.get_action('organization_show')(
            {'ignore_auth': True}, {'id': application_dict['intermediate_organization_id']})

        return application_dict


def init_table(engine):
    Base.metadata.create_all(engine)
    log.info("Table for applying permissions is set-up")
