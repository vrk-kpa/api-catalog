import flask
from datetime import datetime, timedelta
import ckan.plugins.toolkit as toolkit
from .model import LinkValidationResult


admin_broken_links = flask.Blueprint('admin_broken_links', __name__, url_prefix='/ckan-admin')
broken_links = flask.Blueprint('broken_links', __name__)


def get_blueprint():
    return [admin_broken_links, broken_links]


@admin_broken_links.route('/admin_broken_links')
def read():
    context = {
        u'user': toolkit.g.user,
        u'auth_user_obj': toolkit.g.userobj
    }
    try:
        toolkit.check_access('admin_broken_links', context)
    except toolkit.NotAuthorized:
        toolkit.abort(403, toolkit._(u'Not authorized to see this page'))

    a_week_ago = datetime.today().date() - timedelta(weeks=1)
    results = LinkValidationResult.get_since(a_week_ago)

    def get_org(name):
        try:
            return toolkit.get_action('organization_show')(context, {'id': name})
        except toolkit.ObjectNotFound:
            return None

    for result in results:
        organization_ids = {r.organization for r in result.referrers if r.organization}
        result.organizations = [o for o in (get_org(oid) for oid in organization_ids) if o]

    extra_vars = {'results': results}
    return toolkit.render('admin/broken_links.html', extra_vars=extra_vars)


@broken_links.route('/organization/broken_links/<organization_id>')
def organization_read(organization_id):
    context = {
        u'user': toolkit.g.user,
        u'auth_user_obj': toolkit.g.userobj
    }
    try:
        toolkit.check_access('organization_update', context, {"id": organization_id})
    except toolkit.NotAuthorized:
        toolkit.abort(403, toolkit._(u'Not authorized to see this page'))

    a_week_ago = datetime.today().date() - timedelta(weeks=1)
    results = LinkValidationResult.get_for_organization_since(organization_id, a_week_ago)
    organization = toolkit.get_action('organization_show')(context, {'id': organization_id})
    toolkit.c.group_dict = organization
    extra_vars = {'results': results, 'group_type': 'organization', 'group_dict': organization}
    return toolkit.render('organization/broken_links.html', extra_vars=extra_vars)
