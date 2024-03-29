from __future__ import absolute_import
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation

from ckanext.apply_permissions_for_service import cli, views, helpers
from ckanext.apply_permissions_for_service.logic import action, auth


class ApplyPermissionsForServicePlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IClick)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')

    # IBlueprint

    def get_blueprint(self):

        return views.get_blueprints()

    # IActions

    def get_actions(self):
        return {'service_permission_application_list': action.service_permission_application_list,
                'service_permission_application_show': action.service_permission_application_show,
                'service_permission_application_create': action.service_permission_application_create,
                'service_permission_settings_show': action.service_permission_settings_show,
                'service_permission_settings_update': action.service_permission_settings_update,
                }

    # IAuthFunctions

    def get_auth_functions(self):
        return {'service_permission_application_list': auth.service_permission_application_list,
                'service_permission_application_show': auth.service_permission_application_show,
                'service_permission_application_create': auth.service_permission_application_create,
                'service_permission_settings': auth.service_permission_settings,
                }

    # ITemplateHelpers

    def get_helpers(self):
        return {'service_permission_application_url': helpers.service_permission_application_url,
                'service_permission_applications_enabled': helpers.service_permission_applications_enabled}

    # IClick

    def get_commands(self):
        return cli.get_commands()
