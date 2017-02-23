import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


def admin_only(context, data_dict=None):
    return {'success': False, 'msg': 'Access restricted to system administrators'}


class Validate_LinksPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IAuthFunctions)

    # IConfigurer

    def update_config(self, config):
        toolkit.add_ckan_admin_tab(config, 'admin_broken_links', 'Broken links')
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'validate_links')

    def before_map(self, m):
        controller = 'ckanext.validate_links.broken_links:AdminBrokenLinksController'
        m.connect('admin_broken_links', '/adminbrokenlinks', action='read', controller=controller)
        return m

    def get_auth_functions(self):
        return {'admin_broken_links': admin_only}
