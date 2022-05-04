import ckan.plugins as plugins
from ckanext.pages.interfaces import IPagesSchema


class Apicatalog_PagesPlugin(plugins.SingletonPlugin):
    plugins.implements(IPagesSchema)

    # IPagesSchema
    def update_pages_schema(self, schema):
        schema.update({
            'title_fi': [],
            'title_sv': [],
            'title_en': [],
            'content_fi': [],
            'content_sv': [],
            'content_en': [],
            'submenu_order': []
            })
        return schema
