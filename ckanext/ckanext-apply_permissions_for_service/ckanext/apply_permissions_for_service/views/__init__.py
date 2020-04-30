import ckan.plugins as plugins

# FIXME: use plugins toolkit
from ckan.common import g

def index():
    context = {u'user': g.user, u'auth_user_obj': g.userobj}
    data_dict = {}
    applications = plugins.toolkit.get_action('service_permission_application_list')(context, data_dict)
    extra_vars = {'applications': applications}
    return plugins.toolkit.render('apply_permissions_for_service/index.html', extra_vars=extra_vars)

def new():
    context = {u'user': g.user, u'auth_user_obj': g.userobj}
    data_dict = {}
    return plugins.toolkit.render('apply_permissions_for_service/new.html')

def view(application_id):
    context = {u'user': g.user, u'auth_user_obj': g.userobj}
    data_dict = {'application_id': application_id}
    application = plugins.toolkit.get_action('service_permission_application_show')(context, data_dict)
    extra_vars = {'application': application}
    return plugins.toolkit.render('apply_permissions_for_service/view.html', extra_vars=extra_vars)

