import ckan
from ckan.controllers.revision import RevisionController
from ckan.common import c, _

import logging

log = logging.getLogger(__name__)


def admin_only(context, data_dict=None):
    return {'success': False, 'msg': 'Access restricted to system administrators'}


class Apicatalog_RoutesPlugin(ckan.plugins.SingletonPlugin):
    ckan.plugins.implements(ckan.plugins.IRoutes, inherit=True)
    ckan.plugins.implements(ckan.plugins.IAuthFunctions)

    # IRoutes

    def before_map(self, m):
        controller = 'ckanext.apicatalog_routes.plugin:Apicatalog_RevisionController'
        m.connect('/revision/list', action='list', controller=controller)
        return m

    # IAuthFunctions

    def get_auth_functions(self):
        return {'user_list': admin_only,
                'revision_list': admin_only
                }


class Apicatalog_RevisionController(RevisionController):
    def list(self):
        context = {'model': ckan.model,
                   'user': c.user or c.author,
                   'auth_user_obj': c.userobj}
        try:
            ckan.logic.check_access('revision_list', context)
            return super(Apicatalog_RevisionController, self).list()
        except ckan.logic.NotAuthorized:
            ckan.lib.base.abort(401, _('Not authorized to see this page'))
