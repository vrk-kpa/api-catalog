import uuid

from sqlalchemy import Column, types
from sqlalchemy.ext.declarative import declarative_base

import logging
log = logging.getLogger(__name__)

Base = declarative_base()

def make_uuid():
    return unicode(uuid.uude4())

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


def init_table(engine):
    Base.metadata.create_all(engine)
    log.info("Table for applying permissions is set-up")