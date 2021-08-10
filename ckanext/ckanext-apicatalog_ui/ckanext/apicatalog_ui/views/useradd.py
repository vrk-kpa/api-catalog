from builtins import range
import random
import string

import ckan.plugins as p

from flask import Blueprint
from flask.views import MethodView
from ckan.model.user import User
from ckan.lib import mailer
from logging import getLogger
from ckan.common import g, _
from ckan import logic

log = getLogger(__name__)
useradd = Blueprint('admin_useradd', __name__, url_prefix=u'/ckan-admin')


def _generate_random_password():
    # From ckan.logic.action.create.user_invite
    # Choose a password. However it will not be used - the invitee will not be
    # told it - they will need to reset it
    while True:
        password = ''.join(random.SystemRandom().choice(
            string.ascii_lowercase + string.ascii_uppercase + string.digits)
            for _ in range(12))
        # Occasionally it won't meet the constraints, so check
        errors = {}
        logic.validators.user_password_validator(
            'password', {'password': password}, errors, None)
        if not errors:
            return password


@useradd.route('/useradd', endpoint='read', methods=['GET', 'POST'])
def read():
    context = {u'user': g.user, u'auth_user_obj': g.userobj}

    try:
        p.toolkit.check_access('admin_useradd', context, {})
    except logic.NotAuthorized:
        p.toolkit.abort(403, _(u'Not authorized to see this page'))
        return

    if p.toolkit.request.method == u'GET':
        return p.toolkit.render(u'admin/useradd.html', extra_vars={})

    elif p.toolkit.request.method == u'POST':
        data = logic.parse_params(p.toolkit.request.form)
        name = data.get('name')
        email = data.get('email')
        user_by_name = User.get(name)
        user_by_email = User.by_email(email)

        errors = {}
        error_summary = ''

        if not name:
            error_summary = _('User name is required.')
            errors['name'] = error_summary
        elif not email:
            error_summary = _('Email is required.')
            errors['email'] = error_summary
        elif user_by_name:
            error_summary = _('User name {} already exists.').format(name)
            errors['name'] = error_summary
        elif user_by_email:
            user_names = ', '.join(u.name for u in user_by_email)
            error_summary = _('Email address {} already has the following users: {}.').format(email, user_names)
            errors['email'] = error_summary
        else:
            try:
                password = _generate_random_password()
                user_dict = p.toolkit.get_action('user_create')(context, {
                    'name': name, 'email': email, 'password': password
                    })
                user = User.get(name)
                log.info('Creating user {} <{}>'.format(name, email))
                mailer.create_reset_key(user)
                mailer.send_reset_link(user)
            except mailer.MailerException:
                p.toolkit.get_action('user_delete')(context, {'id': name})
                error = _('Error sending password reset link to address {}.').format(email)
                errors['email'] = error
                log.error(error)
            except Exception as e:
                # We may have managed to create a user, try deleting it just in case
                try:
                    p.toolkit.get_action('user_delete')(context, {'id': name})
                except:
                    pass
                error = _('Error creating user {} <{}>.').format(name, email)
                errors[''] = error
                log.error(error)

        extra_vars = {
                'errors': errors ,
                'error_summary': error_summary,
                'success': not errors,
                'name': name,
                'email': email
                }
        return p.toolkit.render(u'admin/useradd.html', extra_vars)
