import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import pylons.config as config

import ckan.logic as logic
import random
import urllib
import ckan.lib.i18n as i18n
import logging
import requests

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

    def get_configured_groups(configured_count):
        ''' Return list of valid groups in ckan.featured_orgs up to configured_count or an empty list if none present '''
        items = config.get('ckan.featured_orgs', '').split()
        result = []

        for group_name in items:
            group = get_group(group_name)
            if not group:
                log.warning('Setting ckan.featured_orgs: Organisation \'' + group_name + '\' not found')
                continue
            result.append(group)

        if len(result) > configured_count:
            result = result[:configured_count]

        return result

    def get_random_groups(random_count, excluded_ids):
        ''' Return random valid groups up to random_count where id is not in excluded '''
        result = []
        found = []

        items = logic.get_action('organization_list')({}, {})

        for group_name in items:
            group = get_group(group_name)

            if not group:
                continue
            if group['id'] in excluded_ids:
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
            result.append(group)

        if len(result) > random_count:
            result = random.sample(result, random_count)

        return result

    groups = get_configured_groups(count)

    # If result comes short, fill it in with random groups
    if len(groups) < count:
        groups = groups + get_random_groups(count - len(groups), [x['id'] for x in groups])

    return groups


def unquote_url(url):
    return urllib.unquote(url)

def get_xroad_organizations():

    orgs = []
    try:
        r = requests.get("http://localhost:9090/rest-gateway-0.0.8/Consumer/ListMembers?changedAfter=2011-01-01")
        catalog = r.json()
        members = catalog['memberList']['member']

        for member in members:
            orgs.append({'display_name': member['name']})
    except:
        pass
    return orgs

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
                'ensure_translated': ensure_translated,
                'get_xroad_organizations': get_xroad_organizations
                }


def admin_only(context, data_dict=None):
    return {'success': False, 'msg': 'Access restricted to system administrators'}


class Apicatalog_AdminDashboardPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IConfigurer)

    def update_config(self, config):
        toolkit.add_ckan_admin_tab(config, 'admin_dashboard', 'Dashboard')

    def before_map(self, m):
        controller = 'ckanext.apicatalog_ui.admindashboard:AdminDashboardController'
        m.connect('admin_dashboard', '/admindashboard', action='read', controller=controller)
        return m

    def get_auth_functions(self):
        return {'admin_dashboard': admin_only}
