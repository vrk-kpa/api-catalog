import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import pylons.config as config

import ckan.logic as logic
import random
import urllib
import ckan.lib.i18n as i18n
import logging

log = logging.getLogger(__name__)

def ensure_translated(s):
    ts = type(s)
    if ts == unicode:
        return s
    elif ts == str:
        return unicode(s)
    elif ts == dict:
        language = i18n.get_lang()
        return ensure_translated(s.get(language, u""))


def piwik_url():
    return config.get('piwik.site_url', '')


def piwik_site_id():
    return config.get('piwik.site_id', 0)


def service_alerts():
    message = config.get('ckanext.apicatalog_ui.service_alert.message')
    category = "info"
    if message:
        return [{"message": message, "category": category}]
    else:
        return []


def get_homepage_organizations(count=1):
    def get_group(id):
        context = {'ignore_auth': True,
                   'limits': {'packages': 2},
                   'for_view': True}
        data_dict = {'id': id,
                     'include_datasets': True}

        try:
            out = logic.get_action('organization_show')(context, data_dict)
        except logic.NotFound:
            return None
        return out

    def get_configured_groups():
        ''' Return valid groups listed in ckan.featured_orgs or an empty list if none present '''
        groups_data = []

        config_orgs = config.get('ckan.featured_orgs', '').split()

        for group_name in config_orgs:
            group = get_group(group_name)
            if not group:
                log.warning('Setting ckan.featured_orgs: Organisation \'' + group_name + '\' not found')
                continue
            groups_data.append(group)

        return groups_data

    def get_random_groups():
        groups_data = []

        items = logic.get_action('organization_list')({}, {})

        # list of found ids to prevent duplicates
        found = []
        for group_name in items:
            group = get_group(group_name)
            if not group:
                continue
            # check if duplicate
            if group['id'] in found:
                continue
            # skip orgs with 0 packages
            if group['package_count'] is 0:
                continue
            # skip orgs with 1 package, if shared resource is "no"
            if group['package_count'] is 1 and group['packages'][0].get('shared_resource', 'no') == 'no':
                continue
            found.append(group['id'])
            groups_data.append(group)

        if len(groups_data) > count:
            groups_data = random.sample(groups_data, count)

        return groups_data


    groups = get_configured_groups()
    if len(groups) is 0:
        groups = get_random_groups()

    return groups

def unquote_url(url):
    return urllib.unquote(url)


class Apicatalog_UiPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'apicatalog_ui')

    def update_config_schema(self, schema):
        ignore_missing = toolkit.get_validator('ignore_missing')

        schema.update({
            'ckanext.apicatalog_ui.service_alert.message': [ignore_missing, unicode],
        })

        return schema

    def get_helpers(self):
        return {'piwik_url': piwik_url,
                'get_homepage_organizations': get_homepage_organizations,
                'piwik_site_id': piwik_site_id,
                'service_alerts': service_alerts,
                'unquote_url': unquote_url,
                'ensure_translated': ensure_translated
                }
