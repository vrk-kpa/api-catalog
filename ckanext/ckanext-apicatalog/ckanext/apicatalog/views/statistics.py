
import ckan.plugins as p

from flask import Blueprint
from ckan import logic
from ckan.common import g, _


statistics = Blueprint(u'admin_stats', __name__, url_prefix=u'/ckan-admin')


@statistics.route('/statistics', endpoint='read', methods=['GET'])
def read():
    context = {u'user': g.user, u'auth_user_obj': g.userobj}

    try:
        p.toolkit.check_access('admin_stats', context, {})
    except logic.NotAuthorized:
        p.toolkit.abort(403, _(u'Not authorized to see this page'))
        return

    return p.toolkit.render('admin/statistics.html')


def get_blueprints():
    return [statistics]
