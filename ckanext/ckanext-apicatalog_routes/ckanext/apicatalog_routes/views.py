from flask import Blueprint
from ckan.plugins.toolkit import render, h, request, c
from ckanext.apicatalog_routes.helpers import get_announcements

import logging
log = logging.getLogger(__name__)

announcements = Blueprint("announcements", __name__)

def index():

    c.announcement_list = get_announcements(50)

    return render(u'announcements/index.html')

announcements.add_url_rule(u'/announcements', view_func=index)

def get_blueprints():
    return [announcements]