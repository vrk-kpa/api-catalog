import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import logic
import auth


class ApplyPermissionsForServicePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'applypermissionsforservice')


    # IActions

    def get_actions(self):
        return {
            'service_permission_application_create': logic.service_permission_application_create
        }

    # IAuthFunctions

    def get_auth_functions(self):
        return {
           'service_permission_application_create': auth.service_permission_application_create
        }