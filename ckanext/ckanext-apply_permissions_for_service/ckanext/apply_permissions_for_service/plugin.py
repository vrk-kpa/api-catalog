import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from logic import action, auth
from flask import Blueprint

import views


class ApplyPermissionsForServicePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'applypermissionsforservice')

    # IBlueprint

    def get_blueprint(self):
        blueprint = Blueprint('apply_permissions_for_service', self.__module__, url_prefix=u'/apply_permissions_for_service')
        rules = [
            ('/', 'list_permission_applications', views.index),
            ('/new/<subsystem_id>', 'new_permission_application', views.new),
            ('/view/<application_id>', 'view_permission_application', views.view),
        ]
        for rule in rules:
            blueprint.add_url_rule(*rule)

        return blueprint

    # IActions

    def get_actions(self):
        return {'service_permission_application_list': action.get.service_permission_application_list,
                'service_permission_application_show': action.get.service_permission_application_show,
                'service_permission_application_create': action.create.service_permission_application_create,
                }

    # IAuthFunctions

    def get_auth_functions(self):
        return {'service_permission_application_list': auth.get.service_permission_application_list,
                'service_permission_application_show': auth.get.service_permission_application_show,
                'service_permission_application_create': auth.create.service_permission_application_create,
                }
