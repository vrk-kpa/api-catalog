import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import pylons.config as config
from ckan import model

import ckan.logic as logic
import random
import urllib
import ckan.lib.i18n as i18n
import logging
import itertools

NotFound = logic.NotFound

log = logging.getLogger(__name__)
get_action = toolkit.get_action


def ensure_translated(s):
    ts = type(s)
    if ts == unicode:
        return s
    elif ts == str:
        return unicode(s)
    elif ts == dict:
        language = i18n.get_lang()
        return ensure_translated(s.get(language, u""))


def get_translated(data_dict, field):
    translated = data_dict.get('%s_translated' % field)
    if isinstance(translated, dict):
        language = i18n.get_lang()
        if language in translated:
            return translated[language]
        dialects = [l for l in translated if l.startswith(language) or language.startswith(l)]
        if dialects:
            return translated[dialects[0]]
    return data_dict.get(field)


# Copied from core ckan to call over ridden get_translated
def dataset_display_name(package_or_package_dict):
    if isinstance(package_or_package_dict, dict):
        return get_translated(package_or_package_dict, 'title') or \
               package_or_package_dict['name']
    else:
        # FIXME: we probably shouldn't use the same functions for
        # package dicts and real package objects
        return package_or_package_dict.title or package_or_package_dict.name


def piwik_url():
    return config.get('piwik.site_url', '')


def piwik_site_id():
    return config.get('piwik.site_id', 0)


def service_alerts():
    message = config.get('ckanext.apicatalog_ui.service_alert.message')
    category = "danger"
    if message:
        return [{"message": message, "category": category}]
    else:
        return []

def info_message():
    return config.get('ckanext.apicatalog_ui.info_message', '')

def is_service_bus_id(identifier):
    # GUIDs don't have dots, bus IDs do
    log.warning("is_service_bus_id(%s)" % identifier)
    return '.' in identifier


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
        chunk_size = 2 * random_count
        package_search = logic.get_action('package_search')

        def get_orgs_with_visible_packages(ids):
            id_chunks = (ids[i:i+chunk_size] for i in range(0, len(ids), chunk_size))
            for chunk_ids in id_chunks:
                query = "organization:(%s)+shared_resource:yes" % " OR ".join(chunk_ids)
                packages = package_search({}, {"q": query}).get('results', [])
                valid_ids = {p['organization']['name'] for p in packages}
                for id in (id for id in ids if id in valid_ids):
                    yield id

        all_items = logic.get_action('organization_list')({}, {})
        items = list(set(i for i in all_items if i not in excluded_ids))
        random.shuffle(items)

        result_ids = itertools.islice(get_orgs_with_visible_packages(items), random_count)
        result = [get_group(id) for id in result_ids]

        return result

    groups = get_configured_groups(count)

    # If result comes short, fill it in with random groups
    if len(groups) < count:
        groups = groups + get_random_groups(count - len(groups), [x['id'] for x in groups])

    return groups


def unquote_url(url):
    return urllib.unquote(url)


def get_xroad_organizations():
    context = {}
    all_organizations = get_action('organization_list')(context, {"all_fields": True})
    packageless_organizations = [o for o in all_organizations if o.get('package_count', 0) == 0]

    return packageless_organizations


def custom_organization_list(params):
    page = toolkit.h.get_page_number(params) or 1
    items_per_page = 21

    context = {'model': model, 'session': model.Session,
               'user': toolkit.c.user, 'for_view': True,
               'with_private': False}

    q = toolkit.c.q = params.get('q', '')
    sort_by = toolkit.c.sort_by_selected = params.get('sort')

    if toolkit.c.userobj:
        context['user_id'] = toolkit.c.userobj.id
        context['user_is_admin'] = toolkit.c.userobj.sysadmin

    data_dict_page_results = {
        'all_fields': True,
        'q': q,
        'sort': sort_by,
    }
    results = toolkit.get_action('organization_list')(context, data_dict_page_results)

    def group_by_content(a, b):
        a_has_content = 1 if a['package_count'] else 0
        b_has_content = 1 if b['package_count'] else 0
        return b_has_content - a_has_content

    if not sort_by:
        results.sort(cmp=group_by_content)

    page_start = (page - 1) * items_per_page
    page_end = page * items_per_page
    return results[page_start:page_end]


def get_statistics():
    context = {'model': model, 'session': model.Session,
               'user': toolkit.c.user, 'for_view': True,
               'with_private': True}

    packages = toolkit.get_action('package_search')(context, {})
    organizations = toolkit.get_action('organization_list')(context, {"all_fields": True})
    organizations_with_packages = [o for o in organizations if o.get('package_count', 0) > 0]

    result_dict = {
        'package_count': packages.get('count', 0),
        'organization_count': len(organizations),
        'organizations_with_packages_count': len(organizations_with_packages)
    }

    return result_dict

def is_test_environment():
    return config.get('ckanext.apicatalog_ui.test_environment', False)

class Apicatalog_UiPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IFacets, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'apicatalog_ui')

    def update_config_schema(self, schema):
        ignore_missing = toolkit.get_validator('ignore_missing')

        schema.update({
            'ckanext.apicatalog_ui.service_alert.message': [ignore_missing, unicode],
            'ckanext.apicatalog_ui.info_message': [ignore_missing, unicode],
            'ckanext.apicatalog_routes.readonly_users': [ignore_missing, unicode]
        })

        return schema

    def get_helpers(self):
        return {'piwik_url': piwik_url,
                'get_homepage_organizations': get_homepage_organizations,
                'piwik_site_id': piwik_site_id,
                'service_alerts': service_alerts,
                'info_message': info_message,
                'unquote_url': unquote_url,
                'ensure_translated': ensure_translated,
                'get_translated': get_translated,
                'dataset_display_name': dataset_display_name,
                'get_xroad_organizations': get_xroad_organizations,
                'is_service_bus_id': is_service_bus_id,
                'custom_organization_list': custom_organization_list,
                'get_statistics': get_statistics,
                'is_test_environment': is_test_environment
                }

    # IFacets

    def organization_facets(self, facets_dict, organization_type, package_type):
        if (organization_type == 'organization'):
            facets_dict.pop('organization', None)
        return facets_dict


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
