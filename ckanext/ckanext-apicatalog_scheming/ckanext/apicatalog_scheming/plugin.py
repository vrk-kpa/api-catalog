import uuid

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.common import config
import ckan.lib.navl.dictization_functions as dictization_functions

import validators


class Apicatalog_SchemingPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'apicatalog_scheming')

    def get_validators(self):
        return {
            'lower_if_exists': validators.lower_if_exists,
            'upper_if_exists': validators.upper_if_exists,
            'valid_resources': validators.valid_resources,
            'only_default_lang_required': validators.only_default_lang_required,
            'keep_old_value_if_missing': validators.keep_old_value_if_missing,
            'default_value': validators.default_value,
            "business_id_validator": validators.business_id_validator
            }

    def get_helpers(self):
        return {'scheming_field_only_default_required': scheming_field_only_default_required}


def scheming_field_only_default_required(field, lang):
    if (field
            and field.get('only_default_lang_required')
            and lang == config.get('ckan.locale_default', 'en')):
        return True
    return False
