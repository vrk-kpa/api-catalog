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
    return unicode(uuid.uuid4())

class UserForOrganization(Base):

    __tablename__ = 'user_for_organization'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    name = Column(types.UnicodeText, nullable=False)
    email = Column(types.UnicodeText, nullable=False)
    business_id = Column(types.UnicodeText, nullable=False)
    organization_name = Column(types.UnicodeText, nullable=False)

    @classmethod
    def create(cls, name, email, business_id, organization_name):

        user_for_organization = UserForOrganization(name=name,
                                                    email=email,
                                                    business_id=business_id,
                                                    organization_name=organization_name)
        model.Session.add(user_for_organization)
        model.repo.commit()


def init_table(engine):
    Base.metadata.create_all(engine)
    log.info("Table for users for organization is set-up")