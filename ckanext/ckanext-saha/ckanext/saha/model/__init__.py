# -*- coding: utf-8 -*-

import logging
import datetime

from sqlalchemy import Table, Column, ForeignKey, types
from sqlalchemy.orm import relation

from ckan.model.meta import metadata, mapper
from ckan.model.domain_object import DomainObject

from ckan.model import group

saha_organization_table = None

__all__ = [
    'SahaOrganization', 'saha_organization_table',
]

log = logging.getLogger('ckanext_saha')


class SahaOrganization(DomainObject):
    pass


def setup():
    if not group.group_table.exists():
        log.warning('Group tables not defined?')
        return

    if saha_organization_table is None:
        define_tables()
        log.debug('SAHA tables defined in memory')

    if not saha_organization_table.exists():
        saha_organization_table.create()
        log.debug('SAHA tables created')
    else:
        log.debug('SAHA tables already exist')


def define_tables():
    global saha_organization_table

    if saha_organization_table is not None:
        return

    saha_organization_columns = (
        Column('id', types.UnicodeText, primary_key=True),
        Column('groupId', types.UnicodeText, ForeignKey('group.id'), nullable=True),
        Column('modifiedDate', types.DateTime, default=datetime.datetime.utcnow),
        Column('organizationName', types.UnicodeText),
        Column('organizationUnit', types.UnicodeText),
        Column('businessId', types.UnicodeText),
    )
    saha_organization_table = Table('saha_organization', metadata,
                                    *saha_organization_columns)

    mapper(SahaOrganization, saha_organization_table,
           properties={
               'group': relation(group.Group),
               }
           )
