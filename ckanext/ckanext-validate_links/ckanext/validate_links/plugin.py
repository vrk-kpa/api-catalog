import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.validate_links.cli as cli
import ckanext.validate_links.views as views
from ckan.lib.plugins import DefaultTranslation

from .model import define_tables
from .helpers import organization_has_broken_links


def admin_only(context, data_dict=None):
    return {'success': False, 'msg': 'Access restricted to system administrators'}


class Validate_LinksPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.ITranslation)

    # IConfigurer

    def update_config(self, config):
        define_tables()
        toolkit.add_ckan_admin_tab(config, 'admin_broken_links.read', 'Broken links')
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'validate_links')

    # IBlueprint

    def get_blueprint(self):
        return views.get_blueprint()

    # IAuthFunctions

    def get_auth_functions(self):
        return {'admin_broken_links': admin_only}

    # IClick

    def get_commands(self):
        return cli.get_commands()

    # ITemplateHelpers

    def get_helpers(self):
        return {'organization_has_broken_links': organization_has_broken_links}
