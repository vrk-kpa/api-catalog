import itertools
import copy
from datetime import datetime

from ckan.plugins.toolkit import get_action, request
from ckanext.scheming.helpers import scheming_language_text

from ckan.logic import NotFound

import logging
log = logging.getLogger(__name__)


def get_announcements(count=3, offset=0):

    organization_show = get_action('organization_show')
    package_show = get_action('package_show')
    activity_show = get_action('activity_show')

    def activity_to_announcement(activity):
        try:
            published = parse_datetime(activity.get('timestamp'))
            activity_type = activity.get('activity_type')
            data = {'activity': activity, 'published': published}

            if activity_type == 'new organization':
                organization_id = activity.get('object_id')
                data['organization'] = organization_show({}, {'id': organization_id})

            elif activity_type in ('new package', 'changed package', 'deleted package'):
                package_data = activity_show({'ignore_auth': True}, {'id': activity.get('id'), 'include_data': True})\
                    .get('data', {}).get('package', {})
                if package_data.get('private', False):
                    return None
                organization_id = package_data.get('owner_org')
                data['package'] = package_data
                data['organization'] = organization_show({}, {'id': organization_id})

            # TODO: Update these once ckan 2.9 has resource activities
            elif activity_type in ('new resource', 'changed resource', 'deleted resource'):
                activity.get('object_id')
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
                harvest_activity = get_action('user_activity_list')(admin_context, {'id': 'harvest',
                                                                                    'offset': activity_offset,
                                                                                    'limit': limit})
            except NotFound:
                harvest_activity = get_action('user_activity_list')(admin_context, {'id': 'default',
                                                                                    'offset': activity_offset,
                                                                                    'limit': limit})

            if len(harvest_activity) == 0:
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


# Override scheming helper to map en_GB to en
# TODO: Convert to chained helper once upgraded to ckan 2.10
def apicatalog_scheming_language_text(text, prefer_lang=None):
    current_lang = request.environ.get('CKAN_LANG')

    if current_lang == "en_GB":
        return scheming_language_text(text, prefer_lang="en")

    return scheming_language_text(text, prefer_lang=prefer_lang)


def parse_datetime(t):
    try:
        return datetime.strptime(t, '%Y-%m-%dT%H:%M:%S.%fZ')
    except Exception:
        try:
            return datetime.strptime(t, '%Y-%m-%dT%H:%M:%S.%f')
        except Exception as e:
            log.warn(e)
            return None


def with_field_string_replacements(fields, replaced, replacement, affected_values):
    fields = copy.deepcopy(fields)

    def process(value):
        if isinstance(value, list):
            return [process(v) for v in value]
        else:
            return (value
                    .replace(replaced, replacement)
                    .replace(replaced.capitalize(), replacement.capitalize()))

    for field in fields:
        for value_name in affected_values:
            value = field.get(value_name)
            if value is not None:
                field[value_name] = process(value)

    return fields


def username_from_id(uid):
    return get_action('user_show')({'ignore_auth': True}, {'id': uid}).get('name')
