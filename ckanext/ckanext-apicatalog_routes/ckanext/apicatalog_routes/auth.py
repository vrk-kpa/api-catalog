import logging

from ckan import authz

log = logging.getLogger(__name__)

from ckan.logic.auth import get, update
from ckan.plugins.toolkit import check_access, auth_allow_anonymous_access, _, chained_auth_function

from ckan.lib.base import config
from ckan.common import c


@auth_allow_anonymous_access
def package_show(context, data_dict):
    read_only_users = config.get('ckanext.apicatalog_routes.readonly_users', [])

    if context.get('user') and context.get('user') in read_only_users:
        return {'success': True}

    return get.package_show(context, data_dict)

def read_members(context, data_dict):

    if 'id' not in data_dict and 'group' not in context:
        data_dict['id'] = c.group_dict['id']
    read_only_users = config.get('ckanext.apicatalog_routes.readonly_users', [])

    if context.get('user') and context.get('user') in read_only_users:
        return {'success': True}

    return update.group_edit_permissions(context, data_dict)

def create_user_to_organization(context, data_dict=None):
    users_allowed_to_create_users = config.get('ckanext.apicatalog_routes.allowed_user_creators', [])
    if context.get('user') and context.get('user') in users_allowed_to_create_users:
        return {"success": True}

    return {
        "success": False,
        "msg": _("User {user} not authorized to create users via the API").format(user=context.get('user'))
    }

@chained_auth_function
def user_create(next_auth, context, data_dict=None):
    users_allowed_to_create_users = config.get('ckanext.apicatalog_routes.allowed_user_editors', [])
    if context.get('user') and context.get('user') in users_allowed_to_create_users:
        return {"success": True}

    return next_auth(context, data_dict)

@chained_auth_function
def user_update(next_auth, context, data_dict=None):
    users_allowed_to_create_users = config.get('ckanext.apicatalog_routes.allowed_user_editors', [])
    if context.get('user_obj'):
        sysadmin_field = context.get('user_obj').sysadmin
    else:
        sysadmin_field = data_dict.get('sysadmin')

    # In edit form, only user id is supplied
    if not sysadmin_field:
        sysadmin_field = authz.is_sysadmin(data_dict['id'])

    if context.get('user') and context.get('user') in users_allowed_to_create_users \
            and sysadmin_field is False:
        return {"success": True}

    return next_auth(context, data_dict)

@chained_auth_function
def user_show(next_auth, context, data_dict=None):
    users_allowed_to_create_users = config.get('ckanext.apicatalog_routes.allowed_user_editors', [])

    if context.get('user') and context.get('user') in users_allowed_to_create_users \
            and context['user_obj'].sysadmin is False:
        context['keep_email'] = True
        return {"success": True}

    return next_auth(context, data_dict)