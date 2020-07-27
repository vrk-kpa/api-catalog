import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation
from logic import action, auth
from flask import Blueprint

import views


class ApplyPermissionsForServicePlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.ITranslation)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'applypermissionsforservice')

    # IBlueprint

    def get_blueprint(self):
        blueprint = Blueprint('apply_permissions_for_service', self.__module__, url_prefix=u'/apply_permissions_for_service')
        blueprint.add_url_rule('/', 'list_permission_applications', views.index),
        blueprint.add_url_rule('/new/<subsystem_id>', 'new_permission_application', views.new, methods=['GET', 'POST'])
        blueprint.add_url_rule('/view/<application_id>', 'view_permission_application', views.view),
        blueprint.add_url_rule('/manage/<subsystem_id>', 'manage_permission_applications', views.manage),

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
