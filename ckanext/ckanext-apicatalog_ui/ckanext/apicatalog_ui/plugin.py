import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import pylons.config as config

import ckan.logic as logic
import random


def piwik_url():
    return config.get('piwik.site_url', '')


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

    groups_data = []

    extras = logic.get_action('organization_list')({}, {})

    # list of found ids to prevent duplicates
    found = []
    for group_name in extras:
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
        if group['package_count'] is 1 and group['packages'][0]['shared_resource'] == "no":
            continue
        found.append(group['id'])
        groups_data.append(group)

    if len(groups_data) > count:
        groups_data = random.sample(groups_data, count)
        
    return groups_data


class Apicatalog_UiPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'apicatalog_ui')

    def get_helpers(self):
        return {'piwik_url': piwik_url,
                'get_homepage_organizations': get_homepage_organizations}
