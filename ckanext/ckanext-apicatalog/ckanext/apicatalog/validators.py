from __future__ import absolute_import
from past.builtins import basestring
import re
from ckan.common import _
import ckan.lib.navl.dictization_functions as df
from ckanext.fluent.validators import fluent_text
from ckan.common import config
import ckan.plugins.toolkit as toolkit
import ckan.logic.validators as validators
import json
from . import plugin

import logging
log = logging.getLogger(__name__)

missing = toolkit.missing
get_action = toolkit.get_action
ObjectNotFound = toolkit.ObjectNotFound

try:
    from ckanext.scheming.validation import (
        scheming_validator, validators_from_string)
except ImportError:
    # If scheming can't be imported, return a normal validator instead
    # of the scheming validator
    def scheming_validator(fn):
        def noop(key, data, errors, context):
            return fn(None, None)(key, data, errors, context)
        return noop
    validators_from_string = None


def lower_if_exists(s):
    return s.lower() if s else s


def upper_if_exists(s):
    return s.upper() if s else s


def get(field, obj):
    return obj[field] if type(obj) is dict else obj.__getattribute__(field)


def valid_resources(private, context):
    package = context.get('package')
    if not package:
        return private

    change = get('private', package) != private
    to_public = private is False or private == u'False'

    if change and to_public:
        for resource in get('resources', package):
            if get('extras', resource).get('valid_content') == 'no':
                raise df.Invalid(_("Package contains invalid resources"))
    return private


@scheming_validator
def only_default_lang_required(field, schema):
    default_lang = ''
    if field and field.get('only_default_lang_required'):
        default_lang = config.get('ckan.locale_default', 'en')

    def validator(key, data, errors, context):
        if errors[key]:
            return

        if default_lang == "":
            return

        value = data[key]

        if value is not missing:
            if isinstance(value, basestring):
                try:
                    value = json.loads(value)
                except ValueError:
                    errors[key].append(_('Failed to decode JSON string'))
                    return
                except UnicodeDecodeError:
                    errors[key].append(_('Invalid encoding for JSON string'))
                    return

            if not isinstance(value, dict):
                errors[key].append(_('expecting JSON object'))
                return

            if value.get(default_lang) is None:
                errors[key].append(_('Required language "%s" missing') % default_lang)

            return

        prefix = key[-1] + '-'
        extras = data.get(key[:-1] + ('__extras',), {})

        if extras.get(prefix + default_lang) == '':
            errors[key[:-1] + (key[-1] + '-' + default_lang,)] = [_('Missing value')]

    return validator


@scheming_validator
def keep_old_value_if_missing(field, schema):
    from ckan.lib.navl.dictization_functions import missing, flatten_dict

    def validator(key, data, errors, context):

        if 'package' in context:
            data_dict = flatten_dict(get_action('package_show')(context, {'id': context['package'].id}))

        elif 'group' in context and context['group'] is not None:
            data_dict = flatten_dict(get_action('organization_show')(context, {'id': context['group'].id}))

        else:
            return

        if key not in data or data[key] is missing:
            if key in data_dict:
                data[key] = data_dict[key]

    return validator


def default_value(default):
    from ckan.lib.navl.dictization_functions import missing

    def converter(value, context):
        return value if value is not missing else default
    return converter


def business_id_validator(value):
    matches = re.match(r"(^[0-9]{6,7})-([0-9])$", value)
    if not matches:
        raise toolkit.Invalid(_("Business id is incorrect format."))

    business_id = matches.group(1)
    if len(business_id) == 6:
        business_id = "0" + business_id

    verification_number = (7 * int(business_id[0]) +
                           9 * int(business_id[1]) +
                           10 * int(business_id[2]) +
                           5 * int(business_id[3]) +
                           8 * int(business_id[4]) +
                           4 * int(business_id[5]) +
                           2 * int(business_id[6])) % 11

    if verification_number > 1:
        verification_number = 11 - verification_number

    if verification_number != int(matches.group(2)):
        raise toolkit.Invalid(_("Business id verification number does not match business id."))

    return value


@scheming_validator
def mark_as_modified_in_catalog_if_changed(field, schema):
    from ckan.logic import get_action

    def validator(key, data, errors, context):

        if context.get('group'):
            # Auth audit will fail during harvester updates
            context.pop('__auth_audit', None)
            old_organization = get_action('organization_show')(context, {'id': context['group'].id})
            if json.dumps(old_organization.get(key[0])) != data[key] and 'for_edit' in context:
                flattened = df.flatten_dict({key[0] + '_modified_in_catalog': True})
                data.update(flattened)

    return validator


def ignore_not_package_maintainer(key, data, errors, context):
    '''Ignore the field if user not sysadmin or ignore_auth in context.'''

    if 'package' not in context:
        return

    if not toolkit.check_access('package_update', context, {'id': context['package'].id}):
        data.pop(key)


def create_fluent_tags(vocab):
    def callable(key, data, errors, context):
        value = data[key]
        if isinstance(value, str):
            value = json.loads(value)
        if isinstance(value, dict):
            for lang in value:
                add_to_vocab(context, value[lang], vocab + '_' + lang)
            data[key] = json.dumps(value)

    return callable


def add_to_vocab(context, tags, vocab):

    defer = context.get('defer', False)
    try:
        v = get_action('vocabulary_show')(context, {'id': vocab})
    except toolkit.ObjectNotFound:
        v = plugin.create_vocabulary(vocab, defer)

    import ckan.model as model
    context['vocabulary'] = model.Vocabulary.get(v.get('id'))

    if isinstance(tags, basestring):
        tags = [tags]

    for tag in tags:
        validators.tag_length_validator(tag, context)
        validators.tag_name_validator(tag, context)

        try:
            validators.tag_in_vocabulary_validator(tag, context)
        except toolkit.Invalid:
            plugin.create_tag_to_vocabulary(tag, vocab, defer)


def convert_to_json_compatible_str_if_str(value):
    if isinstance(value, basestring):
        if value == "":
            return json.dumps({})
        try:
            json.loads(value)
        except ValueError:
            value = json.dumps({'fi': value})
        return value


def override_field_with_default_translation(overridden_field_name):
    @scheming_validator
    def implementation(field, schema):

        from ckan.lib.navl.dictization_functions import missing

        default_lang = config.get('ckan.locale_default', 'en')

        def validator(key, data, errors, context):
            value = data[key]
            override_value = missing

            if value is not missing:
                if isinstance(value, basestring):
                    try:
                        value = json.loads(value)
                    except ValueError:
                        errors[key].append(_('Failed to decode JSON string'))
                        return
                    except UnicodeDecodeError:
                        errors[key].append(_('Invalid encoding for JSON string'))
                        return
                if not isinstance(value, dict):
                    errors[key].append(_('expecting JSON object'))
                    return

                override_value = value.get(default_lang, missing)

            if override_value not in (None, missing):
                overridden_key = tuple(overridden_field_name.split('.'))
                data[overridden_key] = override_value

        return validator

    return implementation


@scheming_validator
def override_translation_with_default_language(field, schema):
    from ckan.lib.navl.dictization_functions import missing

    default_lang = config.get('ckan.locale_default', 'en')

    def validator(key, data, errors, context):
        value = data[key]
        override_value = missing

        if value is not missing:
            if isinstance(value, basestring):
                try:
                    value = json.loads(value)
                except UnicodeDecodeError:
                    errors[key].append(_('Invalid encoding for JSON string'))
                    return
                except ValueError:
                    errors[key].append(_('Failed to decode JSON string'))
            if not isinstance(value, dict):
                errors[key].append(_('expecting JSON object'))
                return

            override_value = value.get(default_lang, missing)

        if override_value not in (None, missing):
            for subKey in value.keys():
                if value[subKey] in (None, missing, ''):
                    value[subKey] = override_value

        data[key] = json.dumps(value)

    return validator


@scheming_validator
def fluent_list(field, schema):
    fluent_text_validator = fluent_text(field, schema)

    def validator(key, data, errors, context):
        value = None
        if data.get(key):
            value = data[key]
            if not isinstance(value, dict):
                try:
                    value = json.loads(value)
                except ValueError:
                    value = None

        if not value:
            fluent_text_validator(key, data, errors, context)

            if errors[key]:
                return

            json_value = data[key]

            if json_value is missing:
                return

            value = json.loads(json_value)

        result = {lang: lang_value if isinstance(lang_value, list) else [item.strip() for item in lang_value.split(',')]
                  for lang, lang_value in list(value.items())}

        data[key] = json.dumps(result)

    return validator


def fluent_list_output(value):
    """
    Return stored json representation as a multilingual dict, if
    value is already a dict just pass it through.
    """
    if isinstance(value, dict):
        return value
    try:
        result = json.loads(value)
        return {k: v if isinstance(v, list) else [v] for k, v in list(result.items())}

    except ValueError:
        # plain string in the db, return as is so it can be migrated
        return value


def ignore_non_existent_organizations(value):

    existing_organizations = []

    if isinstance(value, str):
        orgs = [tag.strip()
                for tag in value.split(',')
                if tag.strip()]
    else:
        orgs = value

    for org in orgs:
        try:
            get_action('organization_show')({}, {'id': org})
            existing_organizations.append(org)
        except ObjectNotFound:
            pass

    return ','.join(existing_organizations)


def list_to_json_string(value):
    if value is not missing:
        if not isinstance(value, list):
            raise toolkit.Invalid('Provided value is not a list')
        str_value = json.dumps(value)
        return str_value


def json_string_to_list(value):
    if isinstance(value, str):
        if value == "":
            return []
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            log.warning("Stored value in database was not a json string")
            return value

    if not isinstance(value, list):
        log.warning("Stored value in database was not a list")
    return value


@scheming_validator
def debug(field, schema):
    from pprint import pformat

    def validator(key, data, errors, context):
        fields = {'field': field,
                  'key': key,
                  'data': data,
                  'errors': {k: v for k, v in errors.items() if v != []},
                  'context': context}
        log.debug(f'Debug validator: {pformat(fields)}')
    return validator
