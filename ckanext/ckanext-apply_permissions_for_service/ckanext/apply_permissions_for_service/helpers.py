from ckan.plugins import toolkit
import ckan.lib.uploader as uploader


def service_permission_application_url(subsystem_id):
    settings = toolkit.get_action('service_permission_settings_show')({'ignore_auth': True},
                                                                      {'subsystem_id': subsystem_id})
    return settings.get('web') if settings.get('delivery_method') == 'web' else None


def service_permission_applications_enabled(subsystem_id):
    settings = toolkit.get_action('service_permission_settings_show')({'ignore_auth': True},
                                                                      {'subsystem_id': subsystem_id})
    return True if settings and settings.get('delivery_method', 'none') != 'none' else False

def get_application_attachment(filename):
    return open('{}/storage/uploads/apply_permission/{}'.format(uploader.get_storage_path(), filename), 'rb') 
