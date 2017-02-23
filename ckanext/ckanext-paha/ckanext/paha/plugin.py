import ckan
import ckan.lib.base as base
import ckan.plugins as plugins
from ckan.common import c, _
import logging

log = logging.getLogger(__name__)


def require_paha_key(whitelist):
    def fn(context, data_dict=None):
        key = context.get('auth_user_obj').apikey
        if whitelist and key in whitelist:
            return {'success': True}
        else:
            return {'success': False}

    return fn


class PahaPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IAuthFunctions)

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.key_whitelist = []

    # IConfigurer

    def update_config(self, config_):
        self.key_whitelist = config_.get('ckanext.paha.key_whitelist')

    # IRoutes

    def before_map(self, m):
        controller = 'ckanext.paha.plugin:PahaController'
        m.connect('paha_read_organization', '/paha/read_organization/{id}',
                  action='read_organization', controller=controller)
        return m

    def get_auth_functions(self):
        return {'paha_read_organization': require_paha_key(self.key_whitelist)}


def check_access(privilege):
    ckan.logic.check_access(privilege, {
        'model': ckan.model,
        'user': c.user or c.author,
        'auth_user_obj': c.userobj})


class PahaController(base.BaseController):
    def read_organization(self, id):
        try:
            check_access('paha_read_organization')
            base.abort(200)
        except ckan.logic.NotAuthorized:
            base.abort(403, _('Not authorized to see this page'))

