from flask import Blueprint
from ckan.plugins.toolkit import  render

announcements = Blueprint("announcements", __name__)

def index():

    return render(u'announcements/index.html')

announcements.add_url_rule(u'/announcements', view_func=index)

def get_blueprints():
    return [announcements]