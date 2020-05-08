import uuid

from ckan import model
from ckan.lib import dictization
from sqlalchemy import Column, types
from sqlalchemy.ext.declarative import declarative_base

import logging
log = logging.getLogger(__name__)

Base = declarative_base()

def make_uuid():
    return unicode(uuid.uuid4())

class ApplyPermission(Base):

    __tablename__ = 'apply_permission'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    organization = Column(types.UnicodeText, nullable=False)
    business_code = Column(types.UnicodeText, nullable=False)
    contact_name = Column(types.UnicodeText, nullable=False)
    contact_email = Column(types.UnicodeText, nullable=False)
    ip_address_list = Column(types.JSON, nullable=False)
    subsystem_code = Column(types.UnicodeText, nullable=False)

    subsystem_id = Column(types.UnicodeText, nullable=False)
    request_description = Column(types.UnicodeText)

    @classmethod
    def create(cls, organization, business_code, contact_name, contact_email, ip_address_list, subsystem_code,
               subsystem_id, request_description):

        apply_permission = ApplyPermission(organization=organization, business_code=business_code,
                                           contact_name=contact_name,
                                           contact_email=contact_email,
                                           ip_address_list=ip_address_list,
                                           subsystem_code=subsystem_code,
                                           subsystem_id=subsystem_id,
                                           request_description=request_description)
        model.Session.add(apply_permission)
        model.repo.commit()

    def as_dict(self):
        context = {'model': model}
        application_dict = dictization.table_dictize(self, context)
        return application_dict


def init_table(engine):
    Base.metadata.create_all(engine)
    log.info("Table for applying permissions is set-up")