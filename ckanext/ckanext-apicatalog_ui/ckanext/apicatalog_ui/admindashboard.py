import ckan.lib.base as base
import logging
import ckan.logic as logic
import ckan.model as model
import ckan.lib.activity_streams as activity_streams
from ckan.common import c
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.dictization as dictization
from sqlalchemy import func, text
from datetime import datetime, timedelta

get_action = logic.get_action
check_access = logic.check_access
NotAuthorized = logic.NotAuthorized
log = logging.getLogger(__name__)


class AdminDashboardController(base.BaseController):
    def read(self):
        context = {'model': model, 'user': c.user, 'auth_user_obj': c.userobj}
        try:
            check_access('admin_dashboard', context, {})

            # Query package statistics
            statistics = fetch_package_statistics()

            # Get harvest user id
            harvest_id = (
                    model.Session.query(model.User.id)
                    .filter(model.User.name == 'harvest')
                    .one())

            # Generate activity stream snippet
            package_activity_html = fetch_recent_package_activity_list_html(
                    context, user_id_not=harvest_id)
            harvest_activity_html = fetch_recent_package_activity_list_html(
                    context, user_id=harvest_id)
            privatized_activity_html = fetch_recent_package_activity_list_html(
                    context, only_privatized=True)
            interesting_activity_html = fetch_recent_package_activity_list_html(
                    context, only_resourceful=True)

            # Render template
            vars = {'package_activity_html': package_activity_html,
                    'harvest_activity_html': harvest_activity_html,
                    'privatized_activity_html': privatized_activity_html,
                    'interesting_activity_html': interesting_activity_html,
                    'stats': statistics
                    }
            template = 'admin/dashboard.html'
            return base.render(template, extra_vars=vars)
        except NotAuthorized:
            base.abort(403)


def fetch_package_statistics():
    # Query the number of packages by "private"-value
    public_private_query = (
            model.Session.query(model.Package.private, func.count(model.Package.id))
            .filter(model.Package.state == 'active')
            .group_by(model.Package.private))

    public_count = 0
    private_count = 0

    for private, count in public_private_query:
        if private:
            private_count = count
        else:
            public_count = count

    # Query new package counts for different intervals
    def new_packages_since(dt):
        created = (
                model.Session.query(
                    model.PackageRevision.id.label('id'),
                    func.min(model.PackageRevision.revision_timestamp).label('ts'))
                .group_by(model.PackageRevision.id)
                .subquery())

        return (model.Session.query(func.count(created.c.id))
                .filter(created.c.ts >= dt)
                .one())[0]

    new_last_week = new_packages_since(datetime.utcnow() - timedelta(weeks=1))
    new_last_month = new_packages_since(datetime.utcnow() - timedelta(days=30))
    new_last_year = new_packages_since(datetime.utcnow() - timedelta(days=365))

    return {'public': public_count,
            'private': private_count,
            'new_last_week': new_last_week,
            'new_last_month': new_last_month,
            'new_last_year': new_last_year,
            }


def fetch_recent_package_activity_list_html(
        context, user_id=None, user_id_not=None, only_privatized=False,
        only_resourceful=False, limit=30):
    # Fetch recent revisions, store as list oredered by time
    recent_revisions_query = model.Session.query(model.PackageRevision).distinct()
    if only_resourceful:
        recent_revisions_query = (
                recent_revisions_query
                .join(model.Resource, model.Resource.package_id == model.PackageRevision.id)
                .filter(model.Resource.state == "active"))
    if user_id is not None:
        recent_revisions_query = recent_revisions_query.filter(
                model.PackageRevision.creator_user_id == user_id)
    if user_id_not is not None:
        recent_revisions_query = recent_revisions_query.filter(
                model.PackageRevision.creator_user_id != user_id_not)
    if only_privatized:
        recent_revisions_query = recent_revisions_query.filter(
                model.PackageRevision.private)
    recent_revisions_query = (
            recent_revisions_query
            .order_by(model.PackageRevision.revision_timestamp.desc())
            .limit(limit))

    recent_revisions = [r for r in recent_revisions_query]

    # Fetch related packages, store by id
    packages = {r.id: None for r in recent_revisions}
    packages_query = (
            model.Session.query(model.Package)
            .filter(model.Package.id.in_(packages.keys())))
    for package in packages_query:
        packages[package.id] = package

    # Fetch related packages' first revision timestamps
    packages_created = {}
    packages_created_query = (
            model.Session.query(
                model.PackageRevision.id.label('id'),
                func.min(model.PackageRevision.revision_timestamp).label('ts'))
            .filter(model.PackageRevision.id.in_(packages.keys()))
            .group_by(model.PackageRevision.id))
    for package_id, created in packages_created_query:
        packages_created[package_id] = created

    # Fetch previous revisions for the recent revisions
    packages_previous = {}
    packages_previous_query = (
            model.Session.query(model.PackageRevision.revision_id.label("rid"), model.PackageRevision)
            .from_statement(text("""
            select p.revision_id as rid, r.*
            from package_revision r
            left join (
                    select l.revision_id, r.id, max(r.revision_timestamp) as previous_timestamp
                    from package_revision r
                    join package_revision l on r.id = l.id
                    where l.revision_id = ANY(:ids)
                      and r.revision_timestamp < l.revision_timestamp
                    group by l.revision_id, r.id, l.revision_timestamp
                    ) p on r.id = p.id
            where r.revision_timestamp = p.previous_timestamp
            """))
            .params(ids=[r.revision_id for r in recent_revisions]))
    for rid, package in packages_previous_query:
        packages_previous[rid] = package

    # Add support for new color for privacy-changed packages
    activity_streams.activity_stream_string_icons['changed package privacy'] = 'sitemap'
    activity_streams.activity_stream_string_functions['changed package privacy'] = \
        activity_streams.activity_stream_string_changed_package

    # Create activity objects based on revision data
    def revision_to_activity(r):
        pr = packages_previous.get(r.revision_id)
        if only_privatized and (pr is None or (pr.private or not r.private)):
            return None

        privacy_changed = pr is not None and pr.private != r.private

        activity_type = None
        if r.state in ('active', 'draft'):
            if packages_created[r.id] == r.revision_timestamp:
                activity_type = 'new package'
            elif privacy_changed:
                activity_type = 'changed package privacy'
            else:
                activity_type = 'changed package'
        elif r.state in ('deleted'):
            activity_type = 'deleted package'
        else:
            log.warning("Unknown package state, skipping: %s" % r.state)
            return None

        d = {'package': dictization.table_dictize(
            packages[r.id], context={'model': model})}
        activity = model.Activity(r.creator_user_id, r.id, r.revision_id, activity_type, d)
        activity.timestamp = r.revision_timestamp
        return activity

    activity_objects = (
            (r for r in
                (revision_to_activity(r) for r in recent_revisions)
                if r is not None))

    # Render activity list snippet
    changed_packages = model_dictize.activity_list_dictize(activity_objects, context)
    return activity_streams.activity_list_to_html(
            context, changed_packages, {'offset': 0})
