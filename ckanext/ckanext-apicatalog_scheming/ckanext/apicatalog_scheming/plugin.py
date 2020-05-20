import uuid

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.common import config
import ckan.lib.navl.dictization_functions as dictization_functions

import validators
from schema import create_user_to_organization_schema

ValidationError = toolkit.ValidationError
get_action = toolkit.get_action
_validate = dictization_functions.validate


class Apicatalog_SchemingPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions)

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

    def get_actions(self):
        return {
            "create_user_to_organization": create_user_to_organization
        }

def create_user_to_organization(context, data_dict):

    def _generate_password():
        out = ''
        for n in xrange(8):
            out += str(uuid.uuid4())
        return out

    model = context['model']
    schema = context.get('schema') or create_user_to_organization_schema()
    session = context['session']

    data, errors = _validate(data_dict, schema, context)

    if errors:
        session.rollback()
        raise ValidationError(errors)

    data['password'] = _generate_password()
    user = get_action('user_create')(context, data)
    return {
        "name": user['name'] ,
        "email": user['email']
    }





def scheming_field_only_default_required(field, lang):
    if (field
            and field.get('only_default_lang_required')
            and lang == config.get('ckan.locale_default', 'en')):
        return True
    return False
