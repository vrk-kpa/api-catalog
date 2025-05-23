from __future__ import absolute_import
from builtins import str
from builtins import range
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan import model

import ckan.logic as logic
import html
import random
import urllib.request
import urllib.parse
import urllib.error
import ckan.lib.i18n as i18n
import logging
import itertools
import requests
import json
import six
from datetime import datetime, timedelta
from ckanext.scheming.helpers import lang
import ckan.lib.helpers as h
from ckan.lib.plugins import DefaultTranslation, DefaultPermissionLabels
import ckan.lib.mailer as mailer
from flask import has_request_context
from ckan.lib.navl.dictization_functions import validate as _validate

from .utils import package_generator, organization_generator, filter_allowed_resources
import ckanext.apicatalog.admindashboard as admindashboard
from ckanext.apicatalog.schema import create_user_to_organization_schema

from . import validators
from ckanext.apicatalog import cli
from ckanext.apicatalog import auth, db
from ckanext.apicatalog.helpers import with_field_string_replacements, \
    apicatalog_scheming_language_text, username_from_id, \
    is_boolean_selected

from collections import OrderedDict

NotFound = logic.NotFound
ObjectNotFound = toolkit.ObjectNotFound
config = toolkit.config
log = logging.getLogger(__name__)
get_action = toolkit.get_action
_ = toolkit._

ValidationError = toolkit.ValidationError

_LOCALE_ALIASES = {'en_GB': 'en'}


def ensure_translated(s):
    ts = type(s)
    if ts == six.text_type:
        return s
    elif ts == str:
        return six.text_type(s)
    elif ts == dict:
        language = i18n.get_lang()
        return ensure_translated(s.get(language, u""))


def get_translated(data_dict, field, language=None):
    translated = data_dict.get('%s_translated' % field) or data_dict.get(field)
    if isinstance(translated, dict):
        language = language or i18n.get_lang()
        if language in translated:
            return translated[language] or data_dict.get(field)
        dialects = [tl for tl in translated if tl.startswith(language) or language.startswith(tl)]
        if dialects:
            return translated[dialects[0]] or data_dict.get(field)
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


def get_matomo_config():
    return {
        "site_url": config.get('matomo.site_url', ''),
        "site_id": config.get('matomo.site_id', 0)
    }


def service_alerts():
    locale = i18n.get_lang()
    message = config.get('ckanext.apicatalog.service_alert.' + locale + '.message')
    category = "danger"
    if message:
        return [{"message": message, "category": category}]
    else:
        return []


def info_message():
    locale = i18n.get_lang()
    return config.get('ckanext.apicatalog.info_message.' + locale, '')


def column_contents():
    locale = i18n.get_lang()
    return {
        'left': config.get('ckanext.apicatalog.left_column.' + locale, ''),
        'right': config.get('ckanext.apicatalog.right_column.' + locale, '')
    }


def get_slogan():
    locale = i18n.get_lang()
    if locale == 'fi':
        return config.get('ckan.site_description', '')

    return config.get('ckanext.apicatalog.site_description.' + locale, '')


def get_welcome_text():
    locale = i18n.get_lang()
    if locale == 'fi':
        return config.get('ckan.site_intro_text', '')

    return config.get('ckanext.apicatalog.site_intro_text.' + locale, '')


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


def get_homepage_datasets(count=1):
    context = {}
    datasets = package_generator(context=context,
                                 query='res_name:*',
                                 page_size=count*5,
                                 sort='metadata_created desc',
                                 dataset_type='dataset')

    def criteria(dataset):
        return dataset.get('notes') and len(dataset.get('resources', [])) > 0

    return list(itertools.islice(filter(criteria, datasets), count))


ANNOUNCEMENT_CACHE = None


def get_homepage_announcements(count=3, cache_duration=timedelta(days=1)):
    global ANNOUNCEMENT_CACHE
    from ckanext.apicatalog.helpers import get_announcements
    if ANNOUNCEMENT_CACHE is None or datetime.now() - ANNOUNCEMENT_CACHE[0] > cache_duration:

        announcements = get_announcements(count)
        announcement_cache_timestamp = datetime.now()
        ANNOUNCEMENT_CACHE = (announcement_cache_timestamp, announcements)
    else:
        announcement_cache_timestamp, announcements = ANNOUNCEMENT_CACHE
    return announcements


def unquote_url(url):
    return urllib.parse.unquote(url)


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

    organization_list_options = {
        'q': q,
        'all_fields': True,
        'include_extras': True,
        'sort': sort_by
    }

    # FIXME: Fetching every organization with all fields to filter for paging, could this be improved?

    results = list(organization_generator(context, organization_list_options))

    all_orgs = params.get('all_orgs', '').lower() in ('true', '1', 'yes')
    if not all_orgs:
        results = [group for group in results if group.get('xroad_member_type') == "provider"]

    def sort_by_providers_first(g):
        return 0 if g.get('xroad_member_type') == 'provider' else 1

    if not sort_by:
        results.sort(key=sort_by_providers_first)

    page_start = (page - 1) * items_per_page
    page_end = page * items_per_page

    custom_page = h.Page(
        collection=results,
        page=page,
        url=h.pager_url,
        items_per_page=items_per_page,
    )

    return {
        'organizations': results[page_start:page_end],
        'count': len(results),
        'page': custom_page,
        "all_orgs": all_orgs
    }


def get_statistics():
    context = {'model': model, 'session': model.Session,
               'user': toolkit.c.user, 'for_view': True,
               'with_private': True}

    packages = toolkit.get_action('package_search')(context, {})
    organizations = list(organization_generator(context, {"all_fields": True, "include_extras": True}))
    provider_organizations = [o for o in organizations if o.get('xroad_member_type', '') == 'provider']

    result_dict = {
        'package_count': packages.get('count', 0),
        'organization_count': len(organizations),
        'provider_organizations': len(provider_organizations)
    }

    return result_dict


@logic.side_effect_free
def get_last_12_months_statistics(context=None, data_dict=None):
    packages = list(p for p in package_generator(context, query='metadata_modified:[NOW-12MONTHS TO *]'))
    organizations = toolkit.get_action('organization_list')(context, {"all_fields": True, "include_dataset_count": False})

    package_create_dates = (
        datetime.strptime(result['metadata_created'], '%Y-%m-%dT%H:%M:%S.%f')
        for result in packages if 'metadata_created' in result)

    resource_create_dates = (
        datetime.strptime(resource['created'], '%Y-%m-%dT%H:%M:%S.%f')
        for result in packages
        for resource in result.get('resources', [])
        if 'created' in resource)

    organization_create_dates = (
        datetime.strptime(organization['created'], '%Y-%m-%dT%H:%M:%S.%f')
        for organization in organizations if 'created' in organization)

    # log.info(pformat(list(package_create_dates)))
    one_year_ago = datetime.now() - timedelta(days=365)
    return {'new_packages': sum(1 if d >= one_year_ago else 0 for d in package_create_dates),
            'new_resources': sum(1 if d >= one_year_ago else 0 for d in resource_create_dates),
            'new_organizations': sum(1 if d >= one_year_ago else 0 for d in organization_create_dates),
            'visitors': fetch_visitor_count()}


VISITOR_CACHE = None


def fetch_visitor_count(cache_duration=timedelta(days=1)):
    global VISITOR_CACHE
    if VISITOR_CACHE is None or datetime.now() - VISITOR_CACHE[0] > cache_duration:
        try:
            matomo_site_url = config['matomo.site_url']
            matomo_site_id = config['matomo.site_id']
            matomo_token_auth = config['matomo.token_auth']

            if matomo_token_auth == "":
                log.info("Matomo auth key not set, returning 0...")
                return 0

            params = {
                    'module': 'API',
                    'method': 'VisitsSummary.getVisits',
                    'idSite': matomo_site_id,
                    'period': 'month',
                    'date': 'last12',
                    'format': 'json',
                    'token_auth': matomo_token_auth}
            stats = requests.get('{}/index.php'.format(matomo_site_url),
                                 params=params).json()
            visitor_count = sum(iter(list(stats.values())))
        except Exception:
            # Fetch failed for some reason, keep old value until cache invalidates
            visitor_count = 0 if VISITOR_CACHE is None else VISITOR_CACHE[1]

        visitor_cache_timestamp = datetime.now()
        VISITOR_CACHE = (visitor_cache_timestamp, visitor_count)
    else:
        visitor_cache_timestamp, visitor_count = VISITOR_CACHE

    return visitor_count


def is_test_environment():
    return toolkit.asbool(config.get('ckanext.apicatalog.test_environment', False))


def is_extension_loaded(extension_name):
    return extension_name in config.get('ckan.plugins', [])


def get_submenu_content():

    pages_list = toolkit.get_action('ckanext_pages_list')(None, {'private': False})
    submenu_pages = [page for page in pages_list if page.get('submenu_order')]
    return sorted(submenu_pages, key=lambda p: p['submenu_order'])


def build_pages_nav_main(*args):
    about_menu = toolkit.asbool(config.get('ckanext.pages.about_menu', True))
    group_menu = toolkit.asbool(config.get('ckanext.pages.group_menu', True))
    org_menu = toolkit.asbool(config.get('ckanext.pages.organization_menu', True))

    # Different CKAN versions use different route names - gotta catch em all!
    about_menu_routes = ['about', 'home.about']
    group_menu_routes = ['group_index', 'home.group_index']
    org_menu_routes = ['organizations_index', 'home.organizations_index']

    language = lang()

    new_args = []
    for arg in args:
        if arg[0] in about_menu_routes and not about_menu:
            continue
        if arg[0] in org_menu_routes and not org_menu:
            continue
        if arg[0] in group_menu_routes and not group_menu:
            continue
        new_args.append(arg)

    output = h.build_nav_main(*new_args)

    # do not display any private datasets in menu even for sysadmins
    pages_list = toolkit.get_action('ckanext_pages_list')(None, {'order': True, 'private': False})

    page_name = ''

    if (hasattr(toolkit.c, 'action') and toolkit.c.action in ('pages_show', 'blog_show')
            and toolkit.c.controller == 'ckanext.pages.controller:PagesController'):
        page_name = toolkit.c.environ['routes.url'].current().split('/')[-1]

    for page in pages_list:
        type_ = 'blog' if page['page_type'] == 'blog' else 'pages'
        name = urllib.parse.quote(page['name'])
        if page.get('title_' + language):
            title = html.escape(page['title' + '_' + language])
        else:
            title = html.escape(page['title'])
        link = h.literal(u'<a href="/{}/{}/{}">{}</a>'.format(language, type_, name, title))
        if page['name'] == page_name:
            li = h.literal('<li class="active">') + link + h.literal('</li>')
        else:
            li = h.literal('<li>') + link + h.literal('</li>')
        output = output + li

    return output


def admin_only(context, data_dict=None):
    return {'success': False, 'msg': 'Access restricted to system administrators'}


def scheming_field_only_default_required(field, lang):
    if (field
            and field.get('only_default_lang_required')
            and lang == toolkit.config.get('ckan.locale_default', 'en')):
        return True
    return False


def add_locale_to_source(kwargs, locale):
    copy = kwargs.copy()
    source = copy.get('data-module-source', None)
    if source:
        copy.update({'data-module-source': source + '_' + locale})
        return copy
    return copy


def scheming_language_text_or_empty(text, prefer_lang=None):
    """
    :param text: {lang: text} dict or text string
    :param prefer_lang: choose this language version if available
    Convert "language-text" to users' language by looking up
    language in dict or using gettext if not a dict
    """
    if not text:
        return u''

    if hasattr(text, 'get'):
        try:
            if prefer_lang is None:
                prefer_lang = lang()
        except TypeError:
            pass  # lang() call will fail when no user language available
        else:
            if prefer_lang in _LOCALE_ALIASES:
                prefer_lang = _LOCALE_ALIASES[prefer_lang]
            try:
                return text[prefer_lang]
            except KeyError:
                return ''

    t = _(text)
    if isinstance(t, str):
        return t.decode('utf-8')
    return t


def get_lang_prefix():
    language = lang()
    if language in _LOCALE_ALIASES:
        language = _LOCALE_ALIASES[language]

    return language


def call_toolkit_function(fn, args, kwargs):
    return getattr(toolkit, fn)(*args, **kwargs)


def create_vocabulary(name, defer=False):
    user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}

    try:
        data = {'id': name}
        return toolkit.get_action('vocabulary_show')(context, data)
    except toolkit.ObjectNotFound:
        pass

    log.info("Creating vocab '" + name + "'")
    data = {'name': name}
    try:
        if defer:
            context['defer_commit'] = True
        return toolkit.get_action('vocabulary_create')(context, data)
    except Exception as e:
        log.error('%s' % e)


def create_tag_to_vocabulary(tag, vocab, defer=False):
    user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}

    data = {'id': vocab}
    v = toolkit.get_action('vocabulary_show')(context, data)

    data = {
        "name": tag,
        "vocabulary_id": v['id']}

    if defer:
        context['defer_commit'] = True
    try:
        toolkit.get_action('tag_create')(context, data)
    except toolkit.ValidationError:
        pass


def get_field_from_schema(schema, field_name):

    field = next(field for field in schema.get('dataset_fields', []) if field.get('field_name') == field_name)
    return field


def get_max_resource_size():
    return toolkit.config.get('ckan.max_resource_size')


def send_reset_link(context, data_dict):
    toolkit.check_access('send_reset_link', context)

    user_obj = model.User.get(data_dict['user_id'])
    mailer.send_reset_link(user_obj)


def create_user_to_organization(context, data_dict):

    toolkit.check_access('create_user_to_organization', context)
    schema = context.get('schema') or create_user_to_organization_schema()
    session = context['session']

    data, errors = _validate(data_dict, schema, context)

    if errors:
        session.rollback()
        raise ValidationError(errors)

    created_user = db.UserForOrganization.create(data['fullname'],
                                                 data['email'],
                                                 data['business_id'],
                                                 data['organization_name'])

    return {
        "msg": _("User {name} stored in database.").format(name=created_user.fullname)
    }


def create_organization_users(context, data_dict):
    toolkit.check_access('create_organization_users', context)
    retry = data_dict.get('retry', False)
    pending_user_applications = db.UserForOrganization.get_pending(include_failed=retry)

    organizations = toolkit.get_action('organization_list')(context, {'all_fields': True, 'include_extras': True})
    organizations_by_membercode = {}
    for organization in organizations:
        xroad_member_code = organization.get('xroad_membercode')

        if not xroad_member_code:
            continue

        organizations_by_membercode.setdefault(xroad_member_code, []).append(organization)

    user_list = toolkit.get_action('user_list')
    user_invite = toolkit.get_action('user_invite')
    organization_list_for_user = toolkit.get_action('organization_list_for_user')
    organization_member_create = toolkit.get_action('organization_member_create')
    created = []
    added = []
    invalid = []
    ambiguous = []
    duplicate = []

    for application in pending_user_applications:
        matching_organizations = organizations_by_membercode.get(application.business_id, [])

        if len(matching_organizations) == 0:
            log.warn('No organization found for business id %s, skipping invalid user application', application.business_id)
            application.mark_invalid()
            invalid.append(application.business_id)
            continue
        elif len(matching_organizations) > 1:
            log.warn('Multiple organizations found with business id %s, skipping ambiguous user application',
                     application.business_id)
            application.mark_ambiguous()
            ambiguous.append(application.business_id)
            continue

        organization = next(iter(matching_organizations))

        matching_users = user_list(context, {'email': application.email, 'all_fields': False})
        matching_user = next(iter(matching_users), None)
        try:
            if matching_user:
                user_organizations = organization_list_for_user(context, {'id': matching_user})
                if organization['id'] in (uo['id'] for uo in user_organizations):
                    log.warn('Existing member in %s found for email address %s, skipping duplicate user',
                             organization['name'], application.email)
                    application.mark_duplicate()
                    duplicate.append(application.email)
                    continue
                log.info('Adding user %s to organization %s (%s)',
                         matching_user, organization['title'], organization['id'])
                organization_member_create(context, {'id': organization['id'],
                                                     'username': matching_user,
                                                     'role': 'admin'})

                added.append(matching_user)
            else:
                log.info('Inviting user %s to organization %s (%s)',
                         application.email, organization['title'], organization['id'])
                user = user_invite(context, {'email': application.email,
                                             'group_id': organization['id'],
                                             'role': 'admin'})
                created.append(user.get('name'))
        except ValidationError as e:
            log.warn(e)
            continue
        except ObjectNotFound as e:
            log.warn(e)
            continue

        application.mark_done()

    context.get('session', model.Session).commit()
    return {'success': True, 'result': {'created': created, 'added': added,
                                        'invalid': invalid, 'ambiguous': ambiguous,
                                        'duplicate': duplicate}}


class ApicatalogPlugin(plugins.SingletonPlugin, DefaultTranslation, DefaultPermissionLabels):
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IPermissionLabels)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'apicatalog')

    def update_config_schema(self, schema):
        ignore_missing = toolkit.get_validator('ignore_missing')
        unicode_safe = toolkit.get_validator('unicode_safe')

        schema.update({
            'ckanext.apicatalog.service_alert.fi.message': [ignore_missing, unicode_safe],
            'ckanext.apicatalog.service_alert.sv.message': [ignore_missing, unicode_safe],
            'ckanext.apicatalog.service_alert.en_GB.message': [ignore_missing, unicode_safe],
            'ckanext.apicatalog.info_message.fi': [ignore_missing, unicode_safe],
            'ckanext.apicatalog.info_message.sv': [ignore_missing, unicode_safe],
            'ckanext.apicatalog.info_message.en_GB': [ignore_missing, unicode_safe],
            'ckanext.apicatalog.left_column.fi': [ignore_missing, unicode_safe],
            'ckanext.apicatalog.left_column.sv': [ignore_missing, unicode_safe],
            'ckanext.apicatalog.left_column.en_GB': [ignore_missing, unicode_safe],
            'ckanext.apicatalog.right_column.fi': [ignore_missing, unicode_safe],
            'ckanext.apicatalog.right_column.sv': [ignore_missing, unicode_safe],
            'ckanext.apicatalog.right_column.en_GB': [ignore_missing, unicode_safe],
            'ckanext.apicatalog.readonly_users': [ignore_missing, unicode_safe],
            'ckanext.apicatalog.site_intro_text.sv': [ignore_missing, unicode_safe],
            'ckanext.apicatalog.site_intro_text.en_GB': [ignore_missing, unicode_safe],
            'ckanext.apicatalog.site_description.sv': [ignore_missing, unicode_safe],
            'ckanext.apicatalog.site_description.en_GB': [ignore_missing, unicode_safe]
        })

        return schema

    def get_helpers(self):
        return {'get_homepage_organizations': get_homepage_organizations,
                'get_homepage_datasets': get_homepage_datasets,
                'get_homepage_announcements': get_homepage_announcements,
                'service_alerts': service_alerts,
                'info_message': info_message,
                'column_contents': column_contents,
                'unquote_url': unquote_url,
                'ensure_translated': ensure_translated,
                'get_translated': get_translated,
                'dataset_display_name': dataset_display_name,
                'get_xroad_organizations': get_xroad_organizations,
                'is_service_bus_id': is_service_bus_id,
                'custom_organization_list': custom_organization_list,
                'get_statistics': get_statistics,
                'get_last_12_months_statistics': get_last_12_months_statistics,
                'is_test_environment': is_test_environment,
                'get_submenu_content': get_submenu_content,
                'build_nav_main': build_pages_nav_main,
                'get_slogan': get_slogan,
                'get_welcome_text': get_welcome_text,
                'is_extension_loaded': is_extension_loaded,
                'get_matomo_config': get_matomo_config,
                'scheming_field_only_default_required': scheming_field_only_default_required,
                'scheming_language_text_or_empty': scheming_language_text_or_empty,
                'get_lang_prefix': get_lang_prefix,
                'call_toolkit_function': call_toolkit_function,
                'add_locale_to_source': add_locale_to_source,
                'get_field_from_schema': get_field_from_schema,
                'max_resource_size': get_max_resource_size,
                'with_field_string_replacements': with_field_string_replacements,
                'scheming_language_text': apicatalog_scheming_language_text,
                'username_from_id': username_from_id,
                'is_boolean_selected': is_boolean_selected
                }

    def get_actions(self):
        return {
            'get_last_12_months_statistics': get_last_12_months_statistics,
            "send_reset_link": send_reset_link,
            "create_user_to_organization": create_user_to_organization,
            "create_organization_users": create_organization_users
        }

    # IBlueprint

    def get_blueprint(self):
        from .views.useradd import useradd
        from .views.statistics import statistics
        from .views import announcements_bp, health_bp
        return [useradd, statistics, announcements_bp, health_bp]

    # IFacets

    def organization_facets(self, facets_dict, organization_type, package_type):
        if (organization_type == 'organization'):
            facets_dict.pop('organization', None)
        return facets_dict

    # IValidators

    def get_validators(self):
        return {
            'lower_if_exists': validators.lower_if_exists,
            'upper_if_exists': validators.upper_if_exists,
            'valid_resources': validators.valid_resources,
            'only_default_lang_required': validators.only_default_lang_required,
            'keep_old_value_if_missing': validators.keep_old_value_if_missing,
            'default_value': validators.default_value,
            'business_id_validator': validators.business_id_validator,
            'ignore_not_package_maintainer': validators.ignore_not_package_maintainer,
            'create_fluent_tags': validators.create_fluent_tags,
            'convert_to_json_compatible_str_if_str': validators.convert_to_json_compatible_str_if_str,
            'mark_as_modified_in_catalog_if_changed': validators.mark_as_modified_in_catalog_if_changed,
            'override_field_with_default_translation': validators.override_field_with_default_translation,
            'override_translation_with_default_language': validators.override_translation_with_default_language,
            'fluent_list': validators.fluent_list,
            'fluent_list_output': validators.fluent_list_output,
            'ignore_non_existent_organizations': validators.ignore_non_existent_organizations,
            'list_to_json_string': validators.list_to_json_string,
            'json_string_to_list': validators.json_string_to_list,
            'debug': validators.debug,
            'empty_to_list': validators.empty_to_list,
            'fluent_core_translated_output_any_field': validators.fluent_core_translated_output_any_field,
        }

    # IFacets

    def dataset_facets(self, facets_dict, package_type):
        lang = get_lang_prefix()
        facets_dict = OrderedDict([
            ('services', _('Services')),
            ('organization', _('Organization')),
            ('vocab_keywords_' + lang, _('Tags')),
            ('res_format', _('Formats'))
        ])
        return facets_dict

    # IPackageController

    def before_dataset_index(self, pkg_dict):
        # Map keywords to vocab_keywords_{lang}
        translated_vocabs = ['keywords']
        languages = ['fi', 'sv', 'en']
        for prop_key in translated_vocabs:
            prop_json = pkg_dict.get(prop_key)
            # Add only if not already there
            if not prop_json:
                continue
            prop_value = json.loads(prop_json)
            # Add for each language
            for language in languages:
                if prop_value.get(language):
                    pkg_dict['vocab_%s_%s' % (prop_key, language)] = [tag.lower() for tag in prop_value[language]]

        if pkg_dict.get('num_resources', 0) > 0:
            pkg_dict['services'] = "Subsystems with services"
        else:
            pkg_dict['services'] = "Subsystems without services"

        return pkg_dict

    # After package_search, filter out the resources which the user doesn't have access to
    def after_dataset_search(self, search_results, search_params):
        # Only filter results if processing a request
        if not has_request_context():
            return search_results

        try:
            if 'user' in toolkit.g:
                user = toolkit.get_action('user_show')({'ignore_auth': True}, {'id': toolkit.g.user})
                if user and user.get('sysadmin'):
                    return search_results
        except ObjectNotFound:
            pass

        results = search_results.get('results', [])

        for result in results:
            user_name = toolkit.g.user
            org_id = result.get('organization', {}).get('id', '')
            resources = result.get('resources', [])
            allowed_resources = filter_allowed_resources(resources, org_id, user_name)
            result['resources'] = allowed_resources
            result['num_resources'] = len(allowed_resources)

        search_results['results'] = results
        return search_results

    # After package_show, filter out the resources which the user doesn't have access to
    def after_dataset_show(self, context, data_dict):
        # Only filter results if processing a request
        if not has_request_context():
            return data_dict

        # Skip access check if sysadmin or auth is ignored
        if context.get('ignore_auth') or (context.get('auth_user_obj')
                                          and not context.get('auth_user_obj').is_anonymous
                                          and context.get('auth_user_obj').sysadmin):
            return data_dict

        user_name = context.get('user')

        org_id = data_dict.get('organization', {}).get('id', '')
        resources = data_dict.get('resources', [])
        allowed_resources = filter_allowed_resources(resources, org_id, user_name)
        data_dict['resources'] = allowed_resources
        data_dict['num_resources'] = len(allowed_resources)

        return data_dict

    # IClick

    def get_commands(self):
        return cli.get_commands()

    # IAuthFunctions

    def get_auth_functions(self):
        return {'revision_index': admin_only,
                'revision_list': admin_only,
                'revision_diff': admin_only,
                'package_revision_list': admin_only,
                'package_show': auth.package_show,
                'read_members': auth.read_members,
                'group_edit_permissions': auth.read_members,
                'send_reset_link': admin_only,
                'create_user_to_organization': auth.create_user_to_organization,
                'create_organization_users': admin_only,
                'user_create': auth.user_create,
                'user_update': auth.user_update,
                'user_show': auth.user_show,
                'member_create': auth.member_create,
                'member_delete': auth.member_delete,
                'organization_member_create': auth.organization_member_create,
                'organization_member_delete': auth.organization_member_delete,
                'group_show': auth.group_show,
                'user_invite': auth.user_invite,
                'package_create': admin_only,
                'organization_delete': admin_only,
                'package_delete': admin_only,
                'resource_delete': auth.resource_delete
                }

    # IPermissionLabels

    def get_dataset_labels(self, dataset_obj):

        labels = super(ApicatalogPlugin, self).get_dataset_labels(dataset_obj)

        context = {
            'ignore_auth': True
        }

        for user_name in toolkit.config.get('ckanext.apicatalog.readonly_users', '').split():
            try:
                user_obj = get_action('user_show')(context, {'id': user_name})
                labels.append(u'read_only_admin-%s' % user_obj['id'])
            except ObjectNotFound:
                continue

        pkg_dict = get_action('package_show')(context, {'id': dataset_obj.id})

        if pkg_dict.get('xroad_removed') is True:
            # Only sysadmin can view subsystems removed from xroad
            return []

        if pkg_dict.get('private') and \
                pkg_dict.get('private') is True:
            allowed_organizations = [o.strip() for o in pkg_dict.get('allowed_organizations', "").split(',')
                                     if pkg_dict.get('allowed_organizations', "")]
            for org_name in allowed_organizations:
                organization_dict = get_action('organization_show')(context, {'id': org_name})
                labels.append(u'allowed_organization_members-%s' % organization_dict['id'])

        return labels

    def get_user_dataset_labels(self, user_obj):

        labels = super(ApicatalogPlugin, self).get_user_dataset_labels(user_obj)
        readonly_users = toolkit.aslist(toolkit.config.get('ckanext.apicatalog.readonly_users', ''))

        if user_obj and user_obj.name in readonly_users:
            labels.append(u'read_only_admin-%s' % user_obj.id)

        if user_obj and not user_obj.is_anonymous:
            orgs = get_action(u'organization_list_for_user')({u'user': user_obj.id}, {})
            labels.extend(u'allowed_organization_members-%s' % o['id'] for o in orgs)
        return labels


class Apicatalog_AdminDashboardPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IBlueprint)

    # IAuthFunctions

    def get_auth_functions(self):
        return {'admin_dashboard': admin_only,
                'admin_useradd': admin_only,
                'admin_stats': admin_only}

    # IBlueprint

    def get_blueprint(self):
        return admindashboard.get_blueprint()
