import ckan.lib.base as base
import logging
import ckan.logic as logic
import ckan.model as model
import ckan.lib.activity_streams as activity_streams
from ckan.common import c
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.dictization as dictization
from sqlalchemy import func
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

            # Render template
            vars = {'package_activity_html': package_activity_html,
                    'harvest_activity_html': harvest_activity_html,
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
        context, user_id=None, user_id_not=None, limit=50):
    # Fetch recent revisions, store as list oredered by time
    recent_revisions_query = model.Session.query(model.PackageRevision)
    if user_id is not None:
        recent_revisions_query = recent_revisions_query.filter(
                model.PackageRevision.creator_user_id == user_id)
    if user_id_not is not None:
        recent_revisions_query = recent_revisions_query.filter(
                model.PackageRevision.creator_user_id != user_id_not)
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

    # Create activity objects based on revision data
    def revision_to_activity(r):
        activity_type = None
        if r.state in ('active', 'draft'):
            if packages_created[r.id] == r.revision_timestamp:
                activity_type = 'new'
            else:
                activity_type = 'changed'
        elif r.state in ('deleted'):
            activity_type = 'deleted'
        else:
            log.warning("Unknown package state, skipping: %s" % r.state)
            return None

        d = {'package': dictization.table_dictize(
            packages[r.id], context={'model': model})}
        activity = model.Activity(
                r.creator_user_id, r.id,
                r.revision_id, "%s package" % activity_type, d)
        activity.timestamp = r.revision_timestamp
        return activity

    # Render activity list snippet
    activity_objects = (
            revision_to_activity(r)
            for r in recent_revisions if r is not None)
    changed_packages = model_dictize.activity_list_dictize(activity_objects, context)
    return activity_streams.activity_list_to_html(
            context, changed_packages, {'offset': 0})
