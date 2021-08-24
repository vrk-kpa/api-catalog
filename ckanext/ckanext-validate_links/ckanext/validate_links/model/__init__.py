# -*- coding: utf-8 -*-

import logging
import datetime

from sqlalchemy import Table, Column, ForeignKey, types
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import relation

import ckan.model as model
from ckan.model.meta import metadata, mapper, Session
from ckan.model.types import make_uuid
from ckan.model.domain_object import DomainObject

link_validation_result_table = None
link_validation_referrer_table = None

__all__ = [
    'LinkValidationResult', 'link_validation_result_table',
    'LinkValidationReferrer', 'link_validation_referrer_table',
]

log = logging.getLogger(__name__)


class LinkValidationResult(DomainObject):
    @classmethod
    def get_since(cls, t):
        return (model.Session.query(cls)
                .filter(cls.timestamp > t)
                .all())


class LinkValidationReferrer(DomainObject):
    pass


def setup():
    if link_validation_result_table is None:
        define_tables()
        log.debug('Link validation tables defined in memory')

    if not link_validation_result_table.exists():
        link_validation_result_table.create()
        link_validation_referrer_table.create()
        log.debug('Link validation tables created')
    else:
        log.debug('Link validation tables already exist')


def define_tables():
    global link_validation_result_table, link_validation_referrer_table

    if link_validation_result_table is not None:
        return

    link_validation_result_columns = (
        Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
        Column('type', types.UnicodeText, default=None),
        Column('timestamp', types.DateTime, default=datetime.datetime.utcnow),
        Column('url', types.UnicodeText, nullable=False),
        Column('reason', types.UnicodeText, nullable=False),
    )
    link_validation_result_table = Table('link_validation_result', metadata,
                                         *link_validation_result_columns)

    link_validation_referrer_columns = (
        Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
        Column('result_id', types.UnicodeText, ForeignKey('link_validation_result.id')),
        Column('url', types.UnicodeText, nullable=False),
    )
    link_validation_referrer_table = Table('link_validation_referrer', metadata,
                                           *link_validation_referrer_columns)

    mapper(LinkValidationResult, link_validation_result_table)

    mapper(LinkValidationReferrer, link_validation_referrer_table,
           properties={
               'result': relation(LinkValidationResult, backref='referrers'),
               }
           )


def clear_tables():
    Session.query(LinkValidationReferrer).delete()
    Session.query(LinkValidationResult).delete()
    try:
        Session.commit()
    except InvalidRequestError:
        Session.rollback()
        log.error("Clearing LinkValidation tables failed")
    log.info("LinkValidation tables cleared")


def migrate():
    q = "select column_name from INFORMATION_SCHEMA.COLUMNS where table_name = 'link_validation_result';"
    current_cols = list([m[0] for m in Session.execute(q)])
    if "reason" not in current_cols:
        Session.execute("ALTER TABLE link_validation_result ADD COLUMN reason "
                        "character varying NOT NULL default 'Reason was not stored in database.'")
        Session.commit()
