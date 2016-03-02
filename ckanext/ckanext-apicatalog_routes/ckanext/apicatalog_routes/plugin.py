from pylons import config
import ckan
from ckan.controllers.revision import RevisionController
from ckan.controllers.user import UserController
from ckan.common import c, _, request
import ckan.model as model
import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.authz as authz
import ckan.logic as logic
import ckan.lib.helpers as h
import ckan.lib.authenticator as authenticator
import ckan.lib.base as base
import ckan.lib.csrf_token as csrf_token

abort = base.abort
render = base.render
check_access = ckan.logic.check_access
NotAuthorized = ckan.logic.NotAuthorized
NotFound = ckan.logic.NotFound
get_action = ckan.logic.get_action

unflatten = dictization_functions.unflatten
DataError = dictization_functions.DataError

UsernamePasswordError = logic.UsernamePasswordError
ValidationError = logic.ValidationError

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
        m.connect('/revision/diff/{id}', action='diff', controller=controller)

        user_controller = 'ckanext.apicatalog_routes.plugin:Apicatalog_UserController'

        m.connect('user_edit', '/user/edit/{id:.*}', action='edit', controller=user_controller, ckan_icon='cog')
        return m

    # IAuthFunctions

    def get_auth_functions(self):
        return {'user_list': admin_only,
                'revision_list': admin_only,
                'revision_diff': admin_only,
                'package_revision_list': admin_only
                }


def auth_context():
    return {'model': ckan.model,
            'user': c.user or c.author,
            'auth_user_obj': c.userobj}


class Apicatalog_RevisionController(RevisionController):

    def list(self):
        try:
            ckan.logic.check_access('revision_list', auth_context())
            return super(Apicatalog_RevisionController, self).list()
        except ckan.logic.NotAuthorized:
            ckan.lib.base.abort(403, _('Not authorized to see this page'))

    def diff(self, id=None):
        try:
            ckan.logic.check_access('revision_diff', auth_context())
            return super(Apicatalog_RevisionController, self).diff(id=id)
        except ckan.logic.NotAuthorized:
            ckan.lib.base.abort(403, _('Not authorized to see this page'))

class Apicatalog_UserController(UserController):

    # Copy paste from ckan 2.5.1 to get to the _save_edit function
    def edit(self, id=None, data=None, errors=None, error_summary=None):
        context = {'save': 'save' in request.params,
                   'schema': self._edit_form_to_db_schema(),
                   'model': model, 'session': model.Session,
                   'user': c.user, 'auth_user_obj': c.userobj
                   }
        if id is None:
            if c.userobj:
                id = c.userobj.id
            else:
                abort(400, _('No user specified'))
        data_dict = {'id': id}

        try:
            check_access('user_update', context, data_dict)
        except NotAuthorized:
            abort(401, _('Unauthorized to edit a user.'))

        if (context['save']) and not data:
            return self._save_edit(id, context)

        try:
            old_data = get_action('user_show')(context, data_dict)

            schema = self._db_to_edit_form_schema()
            if schema:
                old_data, errors = \
                    dictization_functions.validate(old_data, schema, context)

            c.display_name = old_data.get('display_name')
            c.user_name = old_data.get('name')

            data = data or old_data

        except NotAuthorized:
            abort(401, _('Unauthorized to edit user %s') % '')
        except NotFound:
            abort(404, _('User not found'))

        user_obj = context.get('user_obj')

        if not (authz.is_sysadmin(c.user)
                or c.user == user_obj.name):
            abort(401, _('User %s not authorized to edit %s') %
                  (str(c.user), id))

        errors = errors or {}
        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}

        self._setup_template_variables({'model': model,
                                        'session': model.Session,
                                        'user': c.user or c.author},
                                       data_dict)

        c.is_myself = True
        c.show_email_notifications = h.asbool(
                config.get('ckan.activity_streams_email_notifications'))
        c.form = render(self.edit_user_form, extra_vars=vars)

        return render('user/edit.html')

    # copy paste from ckan 2.5.1 with modification requiring password to change the email
    def _save_edit(self, id, context):
        try:
            data_dict = logic.clean_dict(unflatten(
                    logic.tuplize_dict(logic.parse_params(request.params))))
            context['message'] = data_dict.get('log_message', '')
            data_dict['id'] = id

            csrf_token.validate(data_dict.get('csrf-token', ''))

            # ONLY DIFFERENCE IS HERE
            if (data_dict['password1'] and data_dict['password2']) or data_dict['email']:
                identity = {'login': c.user,
                            'password': data_dict['old_password']}
                auth = authenticator.UsernamePasswordAuthenticator()

                if auth.authenticate(request.environ, identity) != c.user:
                    raise UsernamePasswordError

            # MOAN: Do I really have to do this here?
            if 'activity_streams_email_notifications' not in data_dict:
                data_dict['activity_streams_email_notifications'] = False

            user = get_action('user_update')(context, data_dict)
            h.flash_success(_('Profile updated'))
            h.redirect_to(controller='user', action='read', id=user['name'])
        except NotAuthorized:
            abort(401, _('Unauthorized to edit user %s') % id)
        except NotFound, e:
            abort(404, _('User not found'))
        except DataError:
            abort(400, _(u'Integrity Error'))
        except ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.edit(id, data_dict, errors, error_summary)
        except UsernamePasswordError:
            errors = {'oldpassword': [_('Password entered was incorrect')]}
            error_summary = {_('Old Password'): _('incorrect password')}
            return self.edit(id, data_dict, errors, error_summary)
        except csrf_token.CsrfTokenValidationError:
            h.flash_error(_('Security token error, please try again'))
            return self.edit(id, data_dict, {}, {})
