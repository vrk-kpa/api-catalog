from __future__ import absolute_import

from ckan.lib.plugins import DefaultTranslation
from future import standard_library

from builtins import next

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.scheming.helpers import lang
from ckanext.apicatalog_scheming import cli
import json

try:
    from collections import OrderedDict  # 2.7
except ImportError:
    from sqlalchemy.util import OrderedDict

from . import validators
import logging

standard_library.install_aliases()

log = logging.getLogger(__name__)
_ = toolkit._

_LOCALE_ALIASES = {'en_GB': 'en'}



class Apicatalog_SchemingPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.ITranslation)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')

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
            'fluent_list': validators.fluent_list,
            'fluent_list_output': validators.fluent_list_output,
            }

    def get_helpers(self):
        return {'scheming_field_only_default_required': scheming_field_only_default_required,
                'scheming_language_text_or_empty': scheming_language_text_or_empty,
                'get_lang_prefix': get_lang_prefix,
                'call_toolkit_function': call_toolkit_function,
                'add_locale_to_source': add_locale_to_source,
                'get_field_from_schema': get_field_from_schema}

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

    def before_index(self, pkg_dict):
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
                    pkg_dict['vocab_%s_%s' % (prop_key, language)] = [tag for tag in prop_value[language]]

        if pkg_dict.get('num_resources', 0) > 0:
            pkg_dict['services'] = "Subsystems with services"
        else:
            pkg_dict['services'] = "Subsystems without services"

        return pkg_dict

    # IClick

    def get_commands(self):
        return cli.get_commands()


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
