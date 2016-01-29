import ckan
from ckan.controllers.feed import FeedController
from ckan.common import c, _, json
from pylons import config

import logging

log = logging.getLogger(__name__)

class Apicatalog_FeedPlugin(ckan.plugins.SingletonPlugin):
    ckan.plugins.implements(ckan.plugins.IRoutes, inherit=True)

    # IRoutes

    def before_map(self, m):
        controller = 'ckanext.apicatalog_routes.feed:Apicatalog_FeedController'
        m.connect('/feeds/dataset.atom', action='general', controller=controller)
        m.connect('/feeds/custom.atom', action='custom', controller=controller)
        return m

class Apicatalog_FeedController(FeedController):
    def output_feed(self, results, feed_title, feed_description,
                    feed_link, feed_url, navigation_urls, feed_guid):

        for pkg in results:
            description = pkg.get('notes', '')
            if isinstance(description, dict):
                description = json.dumps(description, ensure_ascii=False).encode('utf-8')
            pkg['notes'] = description

        return super(Apicatalog_FeedController, self).output_feed(results, feed_title,
                        feed_description, feed_link, feed_url, navigation_urls, feed_guid)
