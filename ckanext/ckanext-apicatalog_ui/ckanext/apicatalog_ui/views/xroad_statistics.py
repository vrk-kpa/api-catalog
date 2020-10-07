
import ckan.plugins as p

from flask import Blueprint
from ckan import logic
from ckan.common import g

xroad_statistics = Blueprint(u'admin_xroadstats', __name__, url_prefix=u'/ckan-admin')


@xroad_statistics.route('/xroad_statistics', endpoint='read', methods=['GET'])
def read():
    context = {u'user': g.user, u'auth_user_obj': g.userobj}

    try:
        p.toolkit.check_access('admin_xroadstats', context, {})
    except logic.NotAuthorized:
        p.toolkit.abort(403)
        return

    return p.toolkit.render('admin/xroad_statistics.html')


def get_blueprints():
    return [xroad_statistics]
