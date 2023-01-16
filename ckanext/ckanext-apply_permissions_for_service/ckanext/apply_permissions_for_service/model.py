from builtins import str
import uuid

from ckan import model
from ckan.lib import dictization
from ckan.logic import NotFound
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
    member_code = Column(types.UnicodeText, nullable=False)
    intermediate_member_code = Column(types.UnicodeText, nullable=True)
    contact_name = Column(types.UnicodeText, nullable=False)
    contact_email = Column(types.UnicodeText, nullable=False)
    ip_address_list = Column(types.JSON, nullable=False)
    target_subsystem_id = Column(types.UnicodeText, nullable=False)
    subsystem_id = Column(types.UnicodeText, nullable=False)
    service_id_list = Column(types.JSON, nullable=False)
    usage_description = Column(types.UnicodeText)
    request_date = Column(types.Date)
    application_filename = Column(types.UnicodeText)

    @classmethod
    def create(cls, organization_id, target_organization_id, intermediate_organization_id, member_code,
               intermediate_member_code, contact_name, contact_email, ip_address_list, subsystem_id,
               target_subsystem_id, service_id_list, usage_description, request_date, application_filename=None):

        apply_permission = ApplyPermission(organization_id=organization_id,
                                           target_organization_id=target_organization_id,
                                           intermediate_organization_id=intermediate_organization_id,
                                           member_code=member_code,
                                           intermediate_member_code=intermediate_member_code,
                                           contact_name=contact_name,
                                           contact_email=contact_email,
                                           ip_address_list=ip_address_list,
                                           subsystem_id=subsystem_id,
                                           target_subsystem_id=target_subsystem_id,
                                           service_id_list=service_id_list,
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
        print(application_dict)

        application_dict['subsystem'] = toolkit.get_action('package_show')(
            {'ignore_auth': True}, {'id': application_dict['subsystem_id']})

        application_dict['target_subsystem'] = toolkit.get_action('package_show')(
            {'ignore_auth': True}, {'id': application_dict['target_subsystem_id']})

        application_dict['services'] = []
        for service in application_dict['service_id_list']:
            try:
                resource = toolkit.get_action('resource_show')({'ignore_auth': True}, {'id': service})
                application_dict['services'].append(resource)
            except NotFound:
                pass

        application_dict['organization'] = toolkit.get_action('organization_show')(
            {'ignore_auth': True}, {'id': application_dict['organization_id']})

        application_dict['target_organization'] = toolkit.get_action('organization_show')(
            {'ignore_auth': True}, {'id': application_dict['target_organization_id']})

        if application_dict.get('intermediate_organization_id'):
            try:
                application_dict['intermediate_organization'] = toolkit.get_action('organization_show')(
                    {'ignore_auth': True}, {'id': application_dict['intermediate_organization_id']})
            except NotFound:
                pass

        return application_dict


def init_table(engine):
    Base.metadata.create_all(engine)
