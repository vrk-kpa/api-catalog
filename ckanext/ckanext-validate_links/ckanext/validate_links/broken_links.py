import ckan.lib.base as base
import ckanext.validate_links.model as links_model
import ckan.model as model
from datetime import datetime, timedelta


class AdminBrokenLinksController(base.BaseController):
    def read(self):
        links_model.define_tables()
        a_week_ago = datetime.today().date() - timedelta(weeks=1)
        results = (
                model.Session.query(links_model.LinkValidationResult)
                .filter(links_model.LinkValidationResult.timestamp > a_week_ago)
                .all()
                )

        template = 'admin/broken_links.html'
        vars = {'results': results}
        return base.render(template, extra_vars=vars)
