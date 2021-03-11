from ckan.plugins.toolkit import config, get_action
import requests
import logging
import datetime
import os
from pprint import pformat
import ckan.model as model
log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 3  # seconds


# Add default timeout
class TimeoutHTTPAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super(TimeoutHTTPAdapter, self).__init__(*args, **kwargs)


retry_strategy = requests.packages.urllib3.util.retry.Retry(
    total=3,
    backoff_factor=1
)

adapter = TimeoutHTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("http://", adapter)

SITE_URL_FAILURE_LOGMESSAGE = "Site URL '%s' failed to respond during health check."
HARVEST_FAILURE_LOGMESSAGE = "Harvester '%s' has errors:\n%s"
HARVEST_TIMEOUT_LOGMESSAGE = "Harvester '%s' is probably stuck:\n%s"
FAILURE_MESSAGE = "An error has occurred, check the server log for details"

HARVEST_JOB_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
HARVEST_JOB_TIMEOUT = datetime.timedelta(days=1)


def check_url(url, **kwargs):
    try:
        response = http.get(url, **kwargs)
        return response.status_code == 200
    except Exception as e:
        log.debug('%s responded with: %s', url, e)
        return False


def heartbeat():
    site_url = config.get('ckan.site_url')
    check_site_urls = ['/']

    for url in check_site_urls:
        if not check_url("%s/%s" % (site_url, url), verify=False):
            log.warn(SITE_URL_FAILURE_LOGMESSAGE % url)
            raise HealthError(FAILURE_MESSAGE)

    harvest_source_list = get_action('harvest_source_list')

    data_dict = {'return_last_job_status': True}
    context = {'model': model,
               'ignore_auth': True}

    for harvest_source in harvest_source_list(context, data_dict):
        last_job_status = harvest_source.get('last_job_status')

        if last_job_status is not None:
            num_errors = last_job_status.get('stats', {}).get('errored', 0)

            if num_errors > 0:
                log.warn(HARVEST_FAILURE_LOGMESSAGE % (
                    harvest_source.get('title', ''),
                    pformat(harvest_source)))
                raise HealthError(FAILURE_MESSAGE)

            elif not last_job_status.get('finished'):
                harvest_job_created = last_job_status.get('created')
                created = datetime.datetime.strptime(harvest_job_created, HARVEST_JOB_TIMESTAMP_FORMAT)
                now = datetime.datetime.now()

                if now - created > HARVEST_JOB_TIMEOUT:
                    log.warn(HARVEST_TIMEOUT_LOGMESSAGE % (
                        harvest_source.get('title', ''),
                        pformat(harvest_source)))
                    raise HealthError(FAILURE_MESSAGE)


def xroad_catalog_heartbeat():
    xroad_catalog_address = config.get('ckanext.xroad_integration.xroad_catalog_address', '')  # type: str
    xroad_catalog_certificate = config.get('ckanext.xroad_integration.xroad_catalog_certificate')
    xroad_client_id = config.get('ckanext.xroad_integration.xroad_client_id')
    xroad_client_certificate = config.get('ckanext.xroad_integration.xroad_client_certificate')

    if not xroad_catalog_address.startswith('http'):
        raise HealthError(FAILURE_MESSAGE)

    service = 'heartbeat'
    url = '{address}/{service}'.format(address=xroad_catalog_address, service=service)

    headers = {'X-Road-Client': xroad_client_id}

    certificate_args = {}
    if xroad_catalog_certificate and os.path.isfile(xroad_catalog_certificate):
        certificate_args['verify'] = xroad_catalog_certificate
    else:
        certificate_args['verify'] = False

    if xroad_client_certificate and os.path.isfile(xroad_client_certificate):
        certificate_args['cert'] = xroad_client_certificate

    if check_url(url, headers=headers, **certificate_args) is False:
        log.warn('Error checking xroad-catalog heartbeat')
        raise HealthError(FAILURE_MESSAGE)


class HealthError(Exception):
    def __init__(self, message):
        self.message = message
        super(HealthError, self).__init__(message)
