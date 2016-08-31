import ckan.lib.base as base


class HealthController(base.BaseController):
    def check(self):
        base.abort(200, "I'm a healthy teapot")
