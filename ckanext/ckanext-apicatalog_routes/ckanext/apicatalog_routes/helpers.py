import itertools

from ckan.plugins.toolkit import get_action

from ckan.logic import NotFound
from ckanext.apicatalog_ui.plugin import parse_datetime

import logging
log = logging.getLogger(__name__)

def get_announcements(count=3, offset=0):

    organization_show = get_action('organization_show')
    package_show = get_action('package_show')

    def activity_to_announcement(activity):
        try:
            published = parse_datetime(activity.get('timestamp'))
            activity_type = activity.get('activity_type')
            data = {'activity': activity, 'published': published}

            if activity_type == 'new organization':
                organization_id = activity.get('object_id')
                data['organization'] = organization_show({}, {'id': organization_id})

            elif activity_type in ('new package', 'changed package', 'deleted package'):
                package_data = activity.get('data', {}).get('package', {})
                if package_data.get('private', False):
                    return None
                package_id = activity.get('object_id')
                organization_id = package_data.get('owner_org')
                data['package'] = package_show({}, {'id': package_id})
                data['organization'] = organization_show({}, {'id': organization_id})

            elif activity_type in ('new resource', 'changed resource', 'deleted resource'):
                resource_id = activity.get('object_id')
                resource = activity.get('data', {}).get('resource', {})
                package = package_show({}, {'id': resource.get('package_id')})
                organization = organization_show({}, {'id': package.get('owner_org')})
                data['resource'] = resource
                data['package'] = package
                data['organization'] = organization

            else:
                log.debug('Skipping announcement item of type %s', activity_type)
                return None

            return data
        except Exception as e:
            log.warn('Error parsing announcement item: %s', e)
            return None

    def get_activities(activity_count=3, activity_offset=0):
        admin_context = {'ignore_auth': True}

        allowed_activity_types = ['new organization', 'new package', 'changed package', 'deleted package',
                                  'new resource', 'changed resource', 'deleted resource']
        limit = activity_count * 2 or 100
        collected_activities = []

        while len(collected_activities) <= activity_count:
            try:
                harvest_activity = get_action('user_activity_list')(admin_context, {'id': 'harvest', 'offset': activity_offset, 'limit': limit})
            except NotFound:
                harvest_activity = get_action('user_activity_list')(admin_context, {'id': 'default', 'offset': activity_offset, 'limit': limit})

            if len(harvest_activity) is 0:
                log.info("No activities left, stopping search..")
                break

            activity_offset += limit

            collected_activities += (activity for activity in harvest_activity
                                     if activity.get('activity_type') in allowed_activity_types)
        return collected_activities

    harvest_activities = get_activities(count, offset)

    all_announcements = (a for a in (activity_to_announcement(a)
                                     for a in harvest_activities)
                         if a is not None)

    announcements = list(itertools.islice(all_announcements, count))

    return announcements