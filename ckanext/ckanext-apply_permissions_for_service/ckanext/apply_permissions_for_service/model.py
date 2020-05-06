import uuid

from ckan import model
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
    vat_id = Column(types.UnicodeText, nullable=False)
    contact_person_name = Column(types.UnicodeText, nullable=False)
    contact_person_email = Column(types.UnicodeText, nullable=False)
    ip_address_list = Column(types.JSON, nullable=False)
    subsystem_code = Column(types.UnicodeText, nullable=False)

    api_id = Column(types.UnicodeText, nullable=False)
    request_description = Column(types.UnicodeText)

    @classmethod
    def create(cls, organization, vat_id, contact_person_name, contact_person_email, ip_address_list, subsystem_code,
               api_id, request_description):

        apply_permission = ApplyPermission(organization=organization, vat_id=vat_id,
                                           contact_person_name=contact_person_name,
                                           contact_person_email=contact_person_email,
                                           ip_address_list=ip_address_list,
                                           subsystem_code=subsystem_code,
                                           api_id=api_id,
                                           request_description=request_description)
        model.Session.add(apply_permission)
        model.repo.commit()


def init_table(engine):
    Base.metadata.create_all(engine)
    log.info("Table for applying permissions is set-up")