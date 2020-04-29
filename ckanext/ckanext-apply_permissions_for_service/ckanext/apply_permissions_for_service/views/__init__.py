import ckan.plugins as plugins

def index():
    return plugins.toolkit.render('apply_permissions_for_service/index.html')

def new():
    return plugins.toolkit.render('apply_permissions_for_service/new.html')

def view(application_id):
    extra_vars = {'application_id': application_id}
    return plugins.toolkit.render('apply_permissions_for_service/view.html', extra_vars=extra_vars)

