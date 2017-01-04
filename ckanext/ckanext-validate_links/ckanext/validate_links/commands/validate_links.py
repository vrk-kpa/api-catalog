# -*- coding: utf-8 -*-

import sys
from urllib2 import urlopen, URLError, HTTPError
import urlparse as parse
import re

from ckan.lib.cli import CkanCommand
from ckanext.validate_links.model import define_tables, LinkValidationResult, LinkValidationReferrer
import ckan.model as model
import ckan.lib.mailer as mailer
from ckan.common import config


if sys.version_info >= (2, 7, 9):
    import ssl
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    ssl_context.options &= ssl.CERT_NONE


class ValidateLinks(CkanCommand):
    '''ValidateLinks

   Usage:

   links initdb
       - Creates the necessary database tables
    '''

    summary = __doc__.split('\n')[0]
    usage = __doc__

    def __init__(self, name):
        super(ValidateLinks, self).__init__(name)
        define_tables()

    def command(self):
        self._load_config()
        if len(self.args) == 0:
            self.parser.print_usage()
            sys.exit(1)
        cmd = self.args[0]

        if cmd == 'initdb':
            self.initdb()
        elif cmd == 'crawl':
            self.crawl()

    def initdb(self):
        from ckanext.validate_links.model import setup as db_setup
        db_setup()

    def crawl(self):
        site_url = config.get('ckan.site_url')
        crawl_url_blacklist_regex = re.compile(r'/activity/')
        crawl_content_type_whitelist_regex = re.compile(r'text/html')
        url_regex = re.compile(r'href="((http[s]?://|/)(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)"')
        site_map = {}
        to_crawl = [site_url]
        while to_crawl:
            next_crawl = to_crawl.pop(0)
            new_crawl = crawl(next_crawl, site_url, site_map,
                              crawl_url_blacklist_regex,
                              crawl_content_type_whitelist_regex,
                              url_regex)
            to_crawl += new_crawl

        external_urls = get_external_children(site_url, site_map)
        url_errors = {}
        for url in sorted(external_urls):
            try:
                urlopen(url)
            except HTTPError as e:
                referrers = find_referrers(url, site_map)
                url_errors[url] = referrers
            except URLError as e:
                referrers = find_referrers(url, site_map)
                url_errors[url] = referrers

        for url, referrers in url_errors.iteritems():
            result = LinkValidationResult()
            result.type = u'error'
            result.url = url
            result.referrers = []

            for referrer_url in referrers:
                referrer = LinkValidationReferrer()
                referrer.result_id = result.id
                referrer.url = referrer_url
                result.referrers.append(referrer)

            model.Session.add(result)
        model.Session.commit()

        if url_errors:
            from ckan.model.user import User
            admin = User.get('admin')
            mailer.mail_user(admin, 'URL errors', '\n\n'.join('%s\n%s' % (u, '\n'.join('  - %s' % r for r in rs)) for u, rs in url_errors.iteritems()))


def find_referrers(url, site_map):
    results = []

    for referrer, item in site_map.items():
        for child in item.children:
            if child == url:

                results.append(referrer)
                break

    return results


def get_external_children(site_url, site_map):
    site_host = strip_path(site_url)
    external = set()

    for item in site_map.values():
        for child in item.children:
            if not child.startswith(site_host):
                external.add(child)

    return external


class MapItem:
    def __init__(self):
        self.code = 200
        self.children = []


def crawl(url, site_host, site_map,
          crawl_url_blacklist_regex,
          crawl_content_type_whitelist_regex,
          url_regex):
    if url in site_map:
        return []

    map_item = MapItem()
    site_map[url] = map_item

    if not url.startswith(site_host):
        return []

    if crawl_url_blacklist_regex.search(url):
        return []

    try:
        if sys.version_info >= (2, 7, 9):
            response = urlopen(url, context=ssl_context)
        else:
            response = urlopen(url)
    except URLError as e:
        map_item.code = e.code
        return []

    if not crawl_content_type_whitelist_regex.search(response.info().get('content-type')):
        return []

    content = (
            response.read()
            .decode('utf-8')
            .replace(r'\n', '\n')
            .replace(r'\r', '\r'))

    for match in url_regex.finditer(content):
        child = match.group(1)
        if child.startswith('/'):
            child = parse.urljoin(site_host, child)

        child = strip_query(child)

        if child not in map_item.children:
            map_item.children.append(child)

    return map_item.children


def strip_path(url):
    parsed = parse.urlparse(url)
    return parse.urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))


def strip_query(url):
    parsed = parse.urlparse(url)
    return parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
