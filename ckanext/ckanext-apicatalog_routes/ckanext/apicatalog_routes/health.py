import ckan.lib.base as base
import pylons.config as config
import urllib2
import logging
import ckan.logic as logic
import datetime
from pprint import pformat
import ckan.model as model
get_action = logic.get_action
log = logging.getLogger(__name__)

SITE_URL_FAILURE_LOGMESSAGE = "Site URL '%s' failed to respond during health check."
HARVEST_FAILURE_LOGMESSAGE = "Harvester '%s' has errors:\n%s"
HARVEST_TIMEOUT_LOGMESSAGE = "Harvester '%s' is probably stuck:\n%s"
FAILURE_MESSAGE = "An error has occurred, check the server log for details"
SUCCESS_MESSAGE = "OK"

HARVEST_JOB_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
HARVEST_JOB_TIMEOUT = datetime.timedelta(days=1)

def check_url(url):
    try:
        response = urllib2.urlopen(url, timeout=30)
        return response.getcode() == 200
    except urllib2.URLError:
        return False


class HealthController(base.BaseController):
    check_site_urls = ['/']

    def check(self):
        result = True
        site_url = config.get('ckan.site_url')

        for url in self.check_site_urls:
            if not check_url("%s/%s" % (site_url, url)):
                log.warn(SITE_URL_FAILURE_LOGMESSAGE % url)
                result = False
        harvest_source_list = get_action('harvest_source_list')

        data_dict = {'return_last_job_status': True}
        context = {'model': model,
                   'ignore_auth': True}
        for harvest_source in harvest_source_list(context, data_dict):
            last_job_status = harvest_source.get('last_job_status')
            if last_job_status is not None:
                num_errors = last_job_status.get('stats', {}) .get('errored', 0)
                if num_errors > 0:
                    log.warn(HARVEST_FAILURE_LOGMESSAGE % (
                        harvest_source.get('title', ''),
                        pformat(harvest_source)))
                    result = False
                elif not last_job_status.get('finished'):
                    harvest_job_created = last_job_status.get('created')
                    created = datetime.datetime.strptime(harvest_job_created, HARVEST_JOB_TIMESTAMP_FORMAT)
                    now = datetime.datetime.now()

                    if now - created > HARVEST_JOB_TIMEOUT:
                        log.warn(HARVEST_TIMEOUT_LOGMESSAGE % (
                            harvest_source.get('title', ''),
                            pformat(harvest_source)))
                        result = False


        if result:
            base.abort(200, SUCCESS_MESSAGE)
        else:
            base.abort(503, FAILURE_MESSAGE)
