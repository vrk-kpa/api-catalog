import re
from ckan.common import _
import ckan.lib.navl.dictization_functions as df
from ckan.common import config
import ckan.plugins.toolkit as toolkit
import json

missing = toolkit.missing

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

            from pprint import pformat
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
    from ckan.logic import get_action
    def validator(key, data, errors, context):

        if 'package' not in context:
            return

        data_dict = flatten_dict(get_action('package_show')(context, {'id': context['package'].id}))

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
    if len(business_id) is 6:
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
        raise toolkit.Invalid(_("Business id verification number does match business id."))

