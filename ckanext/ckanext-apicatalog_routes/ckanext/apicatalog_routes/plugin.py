from pylons import config
import ckan
from ckan.controllers.revision import RevisionController
from ckan.controllers.user import UserController
from ckan.controllers.organization import OrganizationController
from ckan.common import c, _, request, response
import ckan.model as model
import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.authz as authz
import ckan.logic as logic
import ckan.lib.helpers as h
import ckan.lib.authenticator as authenticator
import ckan.lib.base as base
import ckan.lib.csrf_token as csrf_token
import ckan.lib.mailer as mailer

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

def set_repoze_user(user_id):
    '''Set the repoze.who cookie to match a given user_id'''
    if 'repoze.who.plugins' in request.environ:
        rememberer = request.environ['repoze.who.plugins']['friendlyform']
        identity = {'repoze.who.userid': user_id}
        response.headerlist += rememberer.remember(request.environ, identity)

class Apicatalog_RoutesPlugin(ckan.plugins.SingletonPlugin):
    ckan.plugins.implements(ckan.plugins.IRoutes, inherit=True)
    ckan.plugins.implements(ckan.plugins.IAuthFunctions)

    # IRoutes

    def before_map(self, m):
        controller = 'ckanext.apicatalog_routes.plugin:Apicatalog_RevisionController'
        m.connect('/revision', action='index', controller=controller)
        m.connect('/revision/list', action='list', controller=controller)
        m.connect('/revision/diff/{id}', action='diff', controller=controller)

        user_controller = 'ckanext.apicatalog_routes.plugin:Apicatalog_UserController'

        m.connect('user_edit', '/user/edit/{id:.*}', action='edit', controller=user_controller, ckan_icon='cog')
        m.connect('/user/reset', action='request_reset', controller=user_controller)

        health_controller = 'ckanext.apicatalog_routes.health:HealthController'
        m.connect('/health', action='check', controller=health_controller)

        organization_controller = 'ckanext.apicatalog_routes.plugin:Apicatalog_OrganizationController'
        m.connect('organizations_index', '/organization', controller=organization_controller, action='index')

        return m

    # IAuthFunctions

    def get_auth_functions(self):
        return {'user_list': admin_only,
                'revision_index': admin_only,
                'revision_list': admin_only,
                'revision_diff': admin_only,
                'package_revision_list': admin_only
                }


def auth_context():
    return {'model': ckan.model,
            'user': c.user or c.author,
            'auth_user_obj': c.userobj}


class Apicatalog_RevisionController(RevisionController):

    def index(self):
        try:
            ckan.logic.check_access('revision_index', auth_context())
            return super(Apicatalog_RevisionController, self).index()
        except ckan.logic.NotAuthorized:
            ckan.lib.base.abort(403, _('Not authorized to see this page'))

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

    def _save_new(self, context):
        try:
            data_dict = logic.clean_dict(unflatten(
                logic.tuplize_dict(logic.parse_params(request.params))))
            context['message'] = data_dict.get('log_message', '')
            captcha.check_recaptcha(request)
            user = get_action('user_create')(context, data_dict)
        except NotAuthorized:
            abort(401, _('Unauthorized to create user %s') % '')
        except NotFound, e:
            abort(404, _('User not found'))
        except DataError:
            abort(400, _(u'Integrity Error'))
        except captcha.CaptchaError:
            error_msg = _(u'Bad Captcha. Please try again.')
            h.flash_error(error_msg)
            return self.new(data_dict)
        except ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.new(data_dict, errors, error_summary)
        if not c.user:
            # log the user in programatically
            set_repoze_user(data_dict['name'])
            h.redirect_to(controller='user', action='me', __ckan_no_root=True)
        else:
            # #1799 User has managed to register whilst logged in - warn user
            # they are not re-logged in as new user.
            h.flash_success(_('User "%s" is now registered but you are still '
                            'logged in as "%s" from before') %
                            (data_dict['name'], c.user))
            return render('user/logout_first.html')

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
        c.show_email_notifications = h.converters.asbool(
                config.get('ckan.activity_streams_email_notifications'))
        c.form = render(self.edit_user_form, extra_vars=vars)

        return render('user/edit.html')

    # copy paste from ckan 2.5.1 with modification requiring password to change the email
    def _save_edit(self, id, context):
        try:
            if id in (c.userobj.id, c.userobj.name):
                current_user = True
            else:
                current_user = False
            old_username = c.userobj.name

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
            if current_user and data_dict['name'] != old_username:
                # Changing currently logged in user's name.
                # Update repoze.who cookie to match
                set_repoze_user(data_dict['name'])
            h.redirect_to(controller='user', action='read', id=data_dict['name'])
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

    # Copied from ckan 2.5.2
    # removed searching user names
    def request_reset(self):
        context = {'model': model, 'session': model.Session, 'user': c.user,
                   'auth_user_obj': c.userobj}
        data_dict = {'id': request.params.get('user')}
        try:
            check_access('request_reset', context)
        except NotAuthorized:
            abort(401, _('Unauthorized to request reset password.'))

        if request.method == 'POST':
            id = request.params.get('user')

            context = {'model': model,
                       'user': c.user}

            data_dict = {'id': id}
            user_obj = None
            try:
                user_dict = get_action('user_show')(context, data_dict)
                user_obj = context['user_obj']
            except NotFound:
                # Show success regardless of outcome to prevent scanning
                h.flash_success(_('Please check your inbox for '
                                  'a reset code.'))

            if user_obj:
                try:
                    mailer.send_reset_link(user_obj)
                    h.flash_success(_('Please check your inbox for '
                                      'a reset code.'))
                    h.redirect_to('/')
                except mailer.MailerException, e:
                    h.flash_error(_('Could not send reset link: %s') %
                                  unicode(e))
        return render('user/request_reset.html')

class Apicatalog_OrganizationController(OrganizationController):
    def index(self):
        group_type = self._guess_group_type()

        page = h.get_page_number(request.params) or 1
        items_per_page = 21

        context = {'model': model, 'session': model.Session,
                   'user': c.user, 'for_view': True,
                   'with_private': False}

        q = c.q = request.params.get('q', '')
        sort_by = c.sort_by_selected = request.params.get('sort')
        if sort_by is None:
            sort_by = c.sort_by_selected = 'title asc'
        try:
            self._check_access('site_read', context)
            self._check_access('group_list', context)
        except NotAuthorized:
            abort(403, _('Not authorized to see this page'))

        # pass user info to context as needed to view private datasets of
        # orgs correctly
        if c.userobj:
            context['user_id'] = c.userobj.id
            context['user_is_admin'] = c.userobj.sysadmin

        data_dict_global_results = {
            'all_fields': False,
            'q': q,
            'sort': sort_by,
            'type': group_type or 'group',
        }
        global_results = self._action('group_list')(context,
                                                    data_dict_global_results)

        data_dict_page_results = {
            'all_fields': True,
            'q': q,
            'sort': sort_by,
            'type': group_type or 'group',
            'limit': items_per_page,
            'offset': items_per_page * (page - 1),
        }
        page_results = self._action('group_list')(context,
                                                  data_dict_page_results)

        c.page = h.Page(
            collection=global_results,
            page=page,
            url=h.pager_url,
            items_per_page=items_per_page,
        )

        c.page.items = page_results
        return render(self._index_template(group_type),
                      extra_vars={'group_type': group_type})
