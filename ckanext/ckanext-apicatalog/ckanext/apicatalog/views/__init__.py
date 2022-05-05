from flask import Blueprint, Response
from ckan.plugins.toolkit import render, c
from ckanext.apicatalog.helpers import get_announcements
import ckanext.apicatalog.health as health

import logging
log = logging.getLogger(__name__)


def get_blueprints():
    return [announcements_bp, health_bp]


# Announcements

def announcements():
    c.announcement_list = get_announcements(50)
    return render(u'announcements/index.html')


announcements_bp = Blueprint("announcements", __name__)
announcements_bp.add_url_rule(u'/announcements', view_func=announcements)


# Health

def health_check():
    try:
        health.heartbeat()
    except health.HealthError as e:
        return Response(e.message, status=503)
    return Response('OK')


def health_xroad_catalog_heartbeat():
    try:
        health.xroad_catalog_heartbeat()
        return Response('OK')
    except health.HealthError as e:
        return Response(e.message, status=503)


health_bp = Blueprint('health', __name__)
health_bp.add_url_rule(u'/health', view_func=health_check)
health_bp.add_url_rule(u'/xroad_catalog_heartbeat', view_func=health_xroad_catalog_heartbeat)
