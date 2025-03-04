# -*- coding: utf-8 -*-

from builtins import str
from builtins import object
import sys
from urllib.request import urlopen, build_opener
from urllib.error import URLError, HTTPError
import urllib.parse as parse
import re
from typing import Optional

from ckanext.validate_links.model import LinkValidationResult, LinkValidationReferrer, clear_tables
import ckan.model as model
import ckan.lib.mailer as mailer
from ckan.common import config
from ckan.plugins import toolkit
import click

import ssl
ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
ssl_context.options &= ssl.CERT_NONE


def get_commands():
    return [links]


@click.group()
def links():
    'Validate links in datasets'
    pass


@links.command()
def clear():
    clear_tables()


@links.command()
def crawl():
    clear_tables()

    site_url = config.get('ckan.site_url')
    crawl_url_blacklist_regex = re.compile(r'/activity/')
    crawl_content_type_whitelist_regex = re.compile(r'text/html')
    url_regex = re.compile(r'href="((http[s]?://|/)(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)"')
    url_blacklist = config.get('ckanext.validate_links.url_blacklist', "").split()
    site_map = {}
    to_crawl = [site_url]
    while to_crawl:
        next_crawl = to_crawl.pop(0)
        new_crawl = _crawl(next_crawl, site_url, site_map,
                           crawl_url_blacklist_regex,
                           crawl_content_type_whitelist_regex,
                           url_regex)
        to_crawl += new_crawl

    external_urls = get_external_children(site_url, site_map, url_blacklist)
    url_errors = {}
    opener = build_opener()
    opener.addheaders = [('User-Agent', 'Liityntakatalogi link validator')]
    for url in sorted(external_urls):
        try:
            opener.open(url)
        except HTTPError as e:
            referrers = find_referrers(url, site_map)
            url_errors[url] = {"referrers": referrers, "reason": str(e.reason)}
        except URLError as e:
            referrers = find_referrers(url, site_map)
            url_errors[url] = {"referrers": referrers, "reason": str(e.reason)}

    for url, errors in url_errors.items():
        result = LinkValidationResult()
        result.type = u'error'
        result.url = url
        result.reason = errors['reason']
        result.referrers = []

        for referrer_url in errors['referrers']:
            referrer = LinkValidationReferrer()
            referrer.result_id = result.id
            referrer.url = referrer_url
            referrer.organization = determine_relevant_organization(referrer_url)
            result.referrers.append(referrer)

        model.Session.add(result)
    model.Session.commit()

    if url_errors:
        from ckan.model.user import User
        admin = User.get('admin')
        mailer.mail_user(admin, 'URL errors', '\n\n'.join('%s\n%s' % (u, '\n'.join('  - %s' % r for r in rs))
                                                          for u, rs in url_errors.items()))


def find_referrers(url, site_map):
    results = []

    for referrer, item in list(site_map.items()):
        for child in item.children:
            if child == url:

                results.append(referrer)
                break

    return results


def get_external_children(site_url, site_map, url_blacklist):
    site_host = strip_path(site_url)
    external = set()

    for item in list(site_map.values()):
        for child in item.children:
            if not child.startswith(site_host) and child not in url_blacklist:
                external.add(child)

    return external


# Cache regex patterns to avoid compiling them for every referrer url
DATASET_PATTERN = None
ORGANIZATION_PATTERN = None


def determine_relevant_organization(url: str) -> Optional[str]:
    global DATASET_PATTERN, ORGANIZATION_PATTERN
    if DATASET_PATTERN is None or ORGANIZATION_PATTERN is None:
        site_url = toolkit.config.get('ckan.site_url')
        locales = toolkit.aslist(toolkit.config.get('ckan.locales_offered', ['en']))
        optional_locale = '(?:/(?:{}))?'.format('|'.join(locales))
        dataset_index = toolkit.url_for('dataset_search')
        organization_index = toolkit.url_for('organization_index')
        DATASET_PATTERN = re.compile(f'{site_url}{optional_locale}{dataset_index}([^/]+)(?:/([^/]+))?')
        ORGANIZATION_PATTERN = re.compile(f'{site_url}{optional_locale}{organization_index}([^/]+)(?:/([^/]+))?')

    dataset_match = DATASET_PATTERN.match(url)

    if dataset_match:
        if dataset_match[2] not in ('resource', None, ''):
            dataset_name = dataset_match[2]
        else:
            dataset_name = dataset_match[1]
        dataset = toolkit.get_action('package_show')({'ignore_auth': True}, {'name_or_id': dataset_name})
        return (dataset or {}).get('owner_org')

    organization_match = ORGANIZATION_PATTERN.match(url)

    if organization_match:
        organization_name = organization_match[2] or organization_match[1]
        return organization_name


class MapItem(object):
    def __init__(self):
        self.code = 200
        self.children = []


def _crawl(url, site_host, site_map,
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
