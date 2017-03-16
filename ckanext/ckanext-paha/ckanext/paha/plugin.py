import ckan
import ckan.lib.base as base
import ckan.logic as logic
import ckan.plugins as plugins
from ckan.common import c, _
import logging
import json

get_action = logic.get_action
log = logging.getLogger(__name__)


class PahaPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)

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

    def get_actions(self):
        return {'paha_read_organization': paha_read_organization}


def require_paha_key(whitelist):
    def fn(context, data_dict=None):
        key = context.get('auth_user_obj').apikey
        if whitelist and key in whitelist:
            return {'success': True}
        else:
            return {'success': False}

    return fn


def check_access(privilege):
    ckan.logic.check_access(privilege, {
        'model': ckan.model,
        'user': c.user or c.author,
        'auth_user_obj': c.userobj})


@logic.side_effect_free
def paha_read_organization(context, data_dict):
    try:
        check_access('paha_read_organization')
        organization = get_action('organization_show')({'ignore_auth': True}, {
            'id': data_dict['id'],
            'include_datasets': True,
            'include_dataset_count': True
            })

        if len(organization['packages']) != organization['package_count']:
            log.warning('Organization has over 1000 packages, returning only a truncated list')

        result = [{
            'id': d['id'],
            'title': d['title'],
            'private': d['private']
            } for d in organization['packages']]

        return result

    except ckan.logic.NotAuthorized:
        base.abort(403, _('Not authorized to see this page'))
