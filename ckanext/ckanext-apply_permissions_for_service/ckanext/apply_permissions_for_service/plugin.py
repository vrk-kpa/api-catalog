from __future__ import absolute_import
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.apply_permissions_for_service.cli as cli
from ckan.lib.plugins import DefaultTranslation
from .logic import action, auth
from flask import Blueprint

from . import views
from . import helpers


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
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'applypermissionsforservice')

    # IBlueprint

    def get_blueprint(self):

        return views.get_blueprints()

    # IActions

    def get_actions(self):
        return {'service_permission_application_list': action.get.service_permission_application_list,
                'service_permission_application_show': action.get.service_permission_application_show,
                'service_permission_application_create': action.create.service_permission_application_create,
                'service_permission_settings_show': action.get.service_permission_settings_show,
                'service_permission_settings_update': action.update.service_permission_settings_update,
                }

    # IAuthFunctions

    def get_auth_functions(self):
        return {'service_permission_application_list': auth.get.service_permission_application_list,
                'service_permission_application_show': auth.get.service_permission_application_show,
                'service_permission_application_create': auth.create.service_permission_application_create,
                'service_permission_settings': auth.get.service_permission_settings,
                }

    # ITemplateHelpers

    def get_helpers(self):
        return {'service_permission_application_url': helpers.service_permission_application_url,
                'service_permission_applications_enabled': helpers.service_permission_applications_enabled}

    # IClick

    def get_commands(self):
        return cli.get_commands()
