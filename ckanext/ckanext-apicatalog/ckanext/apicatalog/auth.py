import logging

from ckan import authz
from ckan.plugins.toolkit import aslist

from ckan.logic.auth import get, update, get_resource_object
from ckan.plugins.toolkit import auth_allow_anonymous_access, _, chained_auth_function, check_access, NotAuthorized

from ckan.lib.base import config

log = logging.getLogger(__name__)


@auth_allow_anonymous_access
def package_show(context, data_dict):
    read_only_users = aslist(config.get('ckanext.apicatalog.readonly_users', []))

    if context.get('user') and context.get('user') in read_only_users:
        return {'success': True}

    return get.package_show(context, data_dict)


def read_members(context, data_dict):

    read_only_users = aslist(config.get('ckanext.apicatalog.readonly_users', []))

    if context.get('user') and context.get('user') in read_only_users:
        return {'success': True}

    if _is_member_editor(context):
        return {'success': True}

    return update.group_edit_permissions(context, data_dict)


def create_user_to_organization(context, data_dict=None):
    users_allowed_to_create_users = aslist(config.get('ckanext.apicatalog.allowed_user_creators', []))
    if context.get('user') and context.get('user') in users_allowed_to_create_users:
        return {"success": True}

    return {
        "success": False,
        "msg": _("User {user} not authorized to create users via the API").format(user=context.get('user'))
    }


@chained_auth_function
def user_create(next_auth, context, data_dict=None):
    users_allowed_to_create_users = aslist(config.get('ckanext.apicatalog.allowed_user_editors', []))
    if context.get('user') and context.get('user') in users_allowed_to_create_users:
        return {"success": True}

    try:
        dict_for_member_create = data_dict.copy()
        dict_for_member_create['id'] = dict_for_member_create.get('group_id')
        check_access('organization_member_create', context, dict_for_member_create)
        return {"success": True}
    except NotAuthorized:
        return next_auth(context, data_dict)


@chained_auth_function
@auth_allow_anonymous_access
def user_update(next_auth, context, data_dict=None):
    users_allowed_to_create_users = aslist(config.get('ckanext.apicatalog.allowed_user_editors', []))
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
@auth_allow_anonymous_access
def user_show(next_auth, context, data_dict=None):
    users_allowed_to_create_users = aslist(config.get('ckanext.apicatalog.allowed_user_editors', []))

    if context.get('user') and context.get('user') in users_allowed_to_create_users \
            and context['user_obj'].sysadmin is False:
        context['keep_email'] = True
        return {"success": True}

    return next_auth(context, data_dict)


def _is_member_editor(context):
    users_allowed_to_edit_members = aslist(config.get('ckanext.apicatalog.allowed_member_editors', []))
    return context.get('user') and context.get('user') in users_allowed_to_edit_members


@chained_auth_function
@auth_allow_anonymous_access
def group_show(next_auth, context, data_dict=None):
    return {"success": True} if _is_member_editor(context) else next_auth(context, data_dict)


@chained_auth_function
def member_create(next_auth, context, data_dict=None):
    return {"success": True} if _is_member_editor(context) else next_auth(context, data_dict)


@chained_auth_function
def organization_member_create(next_auth, context, data_dict=None):
    return {"success": True} if _is_member_editor(context) else next_auth(context, data_dict)


@chained_auth_function
def member_delete(next_auth, context, data_dict=None):
    return {"success": True} if _is_member_editor(context) else next_auth(context, data_dict)


@chained_auth_function
def organization_member_delete(next_auth, context, data_dict=None):
    return {"success": True} if _is_member_editor(context) else next_auth(context, data_dict)


@chained_auth_function
def user_invite(next_auth, context, data_dict=None):
    return {"success": True} if _is_member_editor(context) else next_auth(context, data_dict)


def resource_delete(context, data_dict=None):
    resource = get_resource_object(context, data_dict)

    # Only administrators can delete services
    if resource.extras.get('harvested_from_xroad'):
        return {'success': False}

    # Attachment update authorization implies delete authorization
    authorized = authz.is_authorized('resource_update', context, data_dict).get('success')

    if authorized:
        return {'success': True}
    else:
        return {'success': False}
