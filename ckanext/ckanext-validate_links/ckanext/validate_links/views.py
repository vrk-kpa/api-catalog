import flask
from datetime import datetime, timedelta
import ckan.plugins.toolkit as toolkit
from ckanext.validate_links.model import LinkValidationResult, define_tables


admin_broken_links = flask.Blueprint('admin_broken_links', __name__, url_prefix='/ckan-admin')


def get_blueprint():
    return [admin_broken_links]


@admin_broken_links.route('/admin_broken_links')
def read():
    context = {
        u'user': toolkit.g.user,
        u'for_view': True,
        u'auth_user_obj': toolkit.g.userobj
    }
    toolkit.check_access('admin_broken_links', context)
    define_tables()
    a_week_ago = datetime.today().date() - timedelta(weeks=1)
    results = LinkValidationResult.get_since(a_week_ago)

    def get_org(name):
        try:
            return toolkit.get_action('organization_show')({'ignore_auth': True}, {'id': name})
        except toolkit.ObjectNotFound:
            return None

    for result in results:
        organization_ids = {r.organization for r in result.referrers if r.organization}
        result.organizations = [o for o in (get_org(oid) for oid in organization_ids) if o]

    extra_vars = {'results': results}
    return toolkit.render('admin/broken_links.html', extra_vars=extra_vars)
