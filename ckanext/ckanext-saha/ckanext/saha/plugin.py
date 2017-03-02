import ckan.plugins as plugins
import ckan.model as model
# import ckan.plugins.toolkit as toolkit
import urllib2
import re
import json
import datetime
import logging

from ckanext.saha.model import SahaOrganization
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

log = logging.getLogger('ckanext_saha')

class SahaPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)

    # IConfigurer

    def update_config(self, config_):
        log.info('Update config')
        self.api_url = config_.get('ckanext.saha.api_url')
        self.username = config_.get('ckanext.saha.username')
        self.password = config_.get('ckanext.saha.password')
        self.last_modified_date = '1900-01-01T00:00:00Z'

    def login(self):
        self.token = None
        if not (self.username and self.password and self.api_url):
            log.info('Not logging into SAHA, missing credentials or API URL')
            return False

        url = '%s/login' % self.api_url
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        data = '{"email": "%s", "password": "%s"}' % (self.username, self.password)
        request = urllib2.Request(url, data, headers)

        try:
            response = urllib2.urlopen(request)
            if response.getcode() != 200:
                log.warning('Error logging into SAHA: %s' % response.read())
                return False

            cookie_header = response.info().getheader('Set-Cookie')
            self.token = re.findall('.AspNet.ApplicationCookie=[^;]*', cookie_header)[0]

        except urllib2.URLError, e:
            log.warning('Error logging into SAHA: %s' % e)
            return False

        return True


    def update(self):
        if not self.api_url:
            log.info('Not updating SAHA organisations; missing API url.')
            return False

        if not self.token:
            log.info('Not updating SAHA organisations; not logged in.')
            return False

        log.info('Fetching SAHA organization info changed since %s' % self.last_modified_date)

        url = '%s/accounts?lastModifiedAfter=%s' % (self.api_url, self.last_modified_date)
        headers = {'Accept': 'application/json', 'Cookie': self.token}
        data = None
        request = urllib2.Request(url, data, headers)

        # Update time before request to avoid gaps in updates
        self.last_modified_date = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        try:
            response = urllib2.urlopen(request)
            if response.getcode() != 200:
                log.warning('Received error when logging into SAHA')
                return

            accounts = json.load(response)

            for account in accounts:
                org = model.Session.query(SahaOrganization).get(account['id']) or SahaOrganization()
                for prop in ('id', 'modifiedDate', 'organizationName',
                             'organizationUnit', 'businessId'):
                    setattr(org, prop, account.get(prop, getattr(org, prop)))

                if org.businessId and not org.groupId:
                    try:
                        ckan_org = (model.Session.query(model.Group.id)
                                    .filter(model.Group.id.like('%%.%%.%s' % org.businessId))
                                    .filter(model.Group.state == 'active')
                                    .filter(model.Group.type == 'organization')
                                    .one())
                        log.info('Found matching business ID: %s = %s' % (org.businessId, ckan_org))
                        org.groupId = ckan_org
                    except NoResultFound:
                        log.debug('Found no matching organizations for businessId %s' % org.businessId)
                    except MultipleResultsFound:
                        log.warning('Found multiple matching organizations for businessId %s' % org.businessId)

                org.save()


        except urllib2.URLError, e:
            log.warning('Error fetching SAHA organizations: %s' % e)
            return

        return True
