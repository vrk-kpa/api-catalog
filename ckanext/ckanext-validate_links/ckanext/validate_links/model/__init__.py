# -*- coding: utf-8 -*-

import logging
import datetime

from sqlalchemy import Column, ForeignKey, types
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import relation

import ckan.model as model
from ckan.model.types import make_uuid
from ckan.plugins import toolkit

link_validation_result_table = None
link_validation_referrer_table = None

__all__ = [
    'LinkValidationResult', 'link_validation_result_table',
    'LinkValidationReferrer', 'link_validation_referrer_table',
]

log = logging.getLogger(__name__)


class LinkValidationResult(toolkit.BaseModel):
    __tablename__ = 'link_validation_result'
    id = Column('id', types.UnicodeText, primary_key=True, default=make_uuid)
    type = Column('type', types.UnicodeText, default=None)
    timestamp = Column('timestamp', types.DateTime, default=datetime.datetime.utcnow)
    url = Column('url', types.UnicodeText, nullable=False)
    reason = Column('reason', types.UnicodeText, nullable=False)

    @classmethod
    def get_since(cls, t):
        return (model.Session.query(cls)
                .filter(cls.timestamp > t)
                .all())

    @classmethod
    def get_for_organization_since(cls, organization_id, t):
        return (model.Session.query(cls)
                .join(LinkValidationReferrer)
                .filter(LinkValidationReferrer.organization == organization_id)
                .filter(cls.timestamp > t)
                .all())


class LinkValidationReferrer(toolkit.BaseModel):
    __tablename__ = 'link_validation_referrer'
    id = Column('id', types.UnicodeText, primary_key=True, default=make_uuid)
    result_id = Column('result_id', types.UnicodeText, ForeignKey('link_validation_result.id'))
    url = Column('url', types.UnicodeText, nullable=False)
    organization = Column('organization', types.UnicodeText, nullable=True)
    result = relation(LinkValidationResult, backref='referrers')


def clear_tables():
    model.Session.query(LinkValidationReferrer).delete()
    model.Session.query(LinkValidationResult).delete()
    try:
        model.Session.commit()
    except InvalidRequestError:
        model.Session.rollback()
        log.error("Clearing LinkValidation tables failed")
    log.info("LinkValidation tables cleared")
