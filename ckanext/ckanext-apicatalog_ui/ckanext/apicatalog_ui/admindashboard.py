from __future__ import absolute_import
import logging
import ckan.logic as logic
import ckan.model as model
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.dictization as dictization
from sqlalchemy import func, text, or_, and_
from datetime import datetime, timedelta
from .utils import package_generator

import flask
from ckan.plugins import toolkit

get_action = logic.get_action
check_access = logic.check_access
NotAuthorized = logic.NotAuthorized
log = logging.getLogger(__name__)

admin_dashboard = flask.Blueprint('admin_dashboard', __name__, url_prefix='/ckan-admin')


def get_blueprint():
    return [admin_dashboard]


@admin_dashboard.route('/admin_dashboard')
def read():
    context = {'user': toolkit.g.user, 'auth_user_obj': toolkit.g.userobj}
    try:
        toolkit.check_access('admin_dashboard', context, {})

        # Fetch invalid resources
        invalid_resources = fetch_invalid_resources()

        # Query package statistics
        statistics = fetch_package_statistics()

        # Find packageless organizations and produce a changelog
        (packageless_organizations, packageless_organizations_changelog) = \
            fetch_packageless_organizations_and_changelog(context)

        # Generate activity stream snippet
        # FIXME: Disabled because fetch_recent_package_activity_list_html is not ported to CKAN 2.9
        # package_activity_html = fetch_recent_package_activity_list_html(context, user_not='harvest')
        # harvest_activity_html = fetch_recent_package_activity_list_html(context, user='harvest')
        # privatized_activity_html = fetch_recent_package_activity_list_html(context, only_privatized=True)
        # interesting_activity_html = fetch_recent_package_activity_list_html(context, only_resourceful=True)

        # Render template
        vars = {'invalid_resources': invalid_resources,
                # 'package_activity_html': package_activity_html,
                # 'harvest_activity_html': harvest_activity_html,
                # 'privatized_activity_html': privatized_activity_html,
                # 'interesting_activity_html': interesting_activity_html,
                'packageless_organizations': packageless_organizations,
                'packageless_organizations_changelog': packageless_organizations_changelog,
                'stats': statistics
                }
        template = 'admin/dashboard.html'
        return toolkit.render(template, extra_vars=vars)
    except toolkit.NotAuthorized:
        toolkit.abort(403)


def fetch_invalid_resources():
    context = {'ignore_auth': True}

    def invalid_resource_generator():
        for package in package_generator(context, '*:*', 1000):
            for resource in package.get('resources', []):
                if resource.get('valid_content', 'yes') == 'no':
                    yield (resource, package)

    return list(invalid_resource_generator())


def fetch_package_statistics():
    # Query the number of packages by "private"-value
    public_private_query = (
            model.Session.query(model.Package.private, func.count(model.Package.id))
            .filter(model.Package.state == 'active')
            .filter(model.Package.type == 'dataset')
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
                    model.Package.id.label('id'),
                    model.Package.metadata_created.label('ts'))
                .filter(model.Package.type == 'dataset')
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
        context, user=None, user_not=None, only_privatized=False,
        only_resourceful=False, limit=30):

    # FIXME: disable function pending porting to CKAN 2.9
    raise Exception('fetch_recent_package_activity_list_html is not yet ported for CKAN 2.9')

    # FIXME: activity_streams was removed in CKAN 2.9, hack to "fix" references until porting
    activity_streams = None

    # Fetch recent revisions, store as list oredered by time
    recent_revisions_query = (
            model.Session.query(model.PackageRevision, model.User.id)
            .join(model.Revision, model.PackageRevision.revision_id == model.Revision.id)
            .join(model.User, model.Revision.author == model.User.name)
            .distinct())

    if only_resourceful:
        recent_revisions_query = (
                recent_revisions_query
                .join(model.Resource, model.Resource.package_id == model.PackageRevision.id)
                .filter(model.Resource.state == "active"))
    if user is not None:
        recent_revisions_query = recent_revisions_query.filter(
                model.Revision.author == user)
    if user_not is not None:
        recent_revisions_query = recent_revisions_query.filter(
                model.Revision.author != user_not)
    if only_privatized:
        recent_revisions_query = recent_revisions_query.filter(
                model.PackageRevision.private)
    recent_revisions_query = (
            recent_revisions_query
            .order_by(model.PackageRevision.metadata_modified.desc())
            .limit(limit))

    recent_revisions = [r for r in recent_revisions_query]

    # Fetch related packages, store by id
    packages = {r.id: None for r, uid in recent_revisions}
    packages_query = (
            model.Session.query(model.Package)
            .filter(model.Package.id.in_(list(packages.keys()))))
    for package in packages_query:
        packages[package.id] = package

    # Fetch related packages' first revision timestamps
    packages_created = {}
    packages_created_query = (
            model.Session.query(
                model.PackageRevision.id.label('id'),
                func.min(model.PackageRevision.metadata_modified).label('ts'))
            .filter(model.PackageRevision.id.in_(list(packages.keys())))
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
                    select l.revision_id, r.id, max(r.metadata_modified) as previous_timestamp
                    from package_revision r
                    join package_revision l on r.id = l.id
                    where l.revision_id = ANY(:ids)
                      and r.metadata_modified < l.metadata_modified
                    group by l.revision_id, r.id, l.metadata_modified
                    ) p on r.id = p.id
            where r.metadata_modified = p.previous_timestamp
            """))
            .params(ids=[r.revision_id for r, uid in recent_revisions]))
    for rid, package in packages_previous_query:
        packages_previous[rid] = package

    # Add support for new color for privacy-changed packages
    activity_streams.activity_stream_string_icons['changed package privacy'] = 'sitemap'
    activity_streams.activity_stream_string_functions['changed package privacy'] = \
        activity_streams.activity_stream_string_changed_package

    # Create activity objects based on revision data
    def revision_to_activity(r, uid):
        pr = packages_previous.get(r.revision_id)
        if only_privatized and (pr is None or (pr.private or not r.private)):
            return None

        privacy_changed = pr is not None and pr.private != r.private

        activity_type = None
        if r.state in ('active', 'draft'):
            if packages_created[r.id] == r.metadata_modified:
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
        activity = model.Activity(uid, r.id, r.revision_id, activity_type, d)
        activity.timestamp = r.metadata_modified
        return activity

    activity_objects = (
            (r for r in
                (revision_to_activity(r, uid) for r, uid in recent_revisions)
                if r is not None))

    # Render activity list snippet
    changed_packages = model_dictize.activity_list_dictize(activity_objects, context)
    return activity_streams.activity_list_to_html(context, changed_packages, {'offset': 0})


def fetch_packageless_organizations_and_changelog(context):
    # Query package owners
    package_owners = dict(model.Session.query(model.Package.id, model.Package.owner_org).all())

    # Query organization data
    organizations = (model.Session.query(model.Group.id, model.Group.created, model.Group.title, model.GroupExtra.value)
                     .join(model.GroupExtra, and_(model.GroupExtra.group_id == model.Group.id,
                                                  model.GroupExtra.key == 'title_translated',
                                                  model.GroupExtra.active == True), isouter=True) # noqa
                     .filter(model.Group.type == 'organization')
                     .all())

    # Query package new/delete activity events
    package_new_delete_activities = (model.Session.query(model.Activity.timestamp,
                                                         model.Activity.object_id, model.Activity.activity_type)
                                     .filter(or_(model.Activity.activity_type == 'new package',
                                                 model.Activity.activity_type == 'deleted package'))
                                     .order_by(model.Activity.timestamp)
                                     .all())

    # Define organization objects required for UI
    organizations_by_id = {oid: {'id': oid, 'created': created, 'title': title, 'title_translated': title_translated}
                           for oid, created, title, title_translated in organizations}

    # Initialize organization timelines with no packages at the time of their creation
    organization_timelines = {oid: [(created, set())] for oid, created, _, _ in organizations}

    # Create a timeline of contained packages for each organization
    for timestamp, package_id, activity_type in package_new_delete_activities:
        owner_id = package_owners.get(package_id)

        if not owner_id:
            log.warning('No owner found for package "%s"', package_id)
            continue

        organization_timeline = organization_timelines.get(owner_id)

        if not organization_timeline:
            log.warning('No timeline found for organization "%s"', owner_id)
            continue

        latest_timestamp, latest_package_set = organization_timeline[-1]

        if activity_type == 'new package':
            if package_id not in latest_package_set:
                new_package_set = latest_package_set.copy()
                new_package_set.add(package_id)
                organization_timeline.append((timestamp, new_package_set))
            else:
                log.warning('Adding package "%s" a second time?', package_id)
                continue

        if activity_type == 'deleted package':
            if package_id in latest_package_set:
                new_package_set = latest_package_set.copy()
                new_package_set.remove(package_id)
                organization_timeline.append((timestamp, new_package_set))
            else:
                log.warning('Removing package "%s" before adding?', package_id)
                continue

    # Produce a collective changelog for all organizations
    changelog = []

    for oid, organization_timeline in list(organization_timelines.items()):
        organization = organizations_by_id.get(oid)

        if not organization:
            log.warning('Organization "%s" not found', oid)
            continue

        for timestamp, package_set in organization_timeline:
            if len(package_set) == 0:
                changelog.append((timestamp, organization, False))
            elif len(package_set) == 1:
                changelog.append((timestamp, organization, True))

    changelog.sort()

    # Collect currently packageless organizations
    packageless_organizations = []

    for oid, organization_timeline in list(organization_timelines.items()):
        latest_timestamp, latest_package_set = organization_timeline[-1]

        if len(latest_package_set) == 0:
            organization = organizations_by_id.get(oid)

            if not organization:
                log.warning('Organization "%s" not found', oid)
                continue

            packageless_organization = organization.copy()
            packageless_organization['packageless_since'] = latest_timestamp
            packageless_organizations.append(packageless_organization)

    return (packageless_organizations, changelog)
