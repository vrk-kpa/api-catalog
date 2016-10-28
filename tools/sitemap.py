#!/usr/bin/python3

from urllib import request, parse
from urllib.error import URLError
import ssl
import sys
import re

# Require absolute URLs inside hrefs
URL_REGEX_PATTERN = r'href="((http[s]?://|/)(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)"'
URL_REGEX = re.compile(URL_REGEX_PATTERN)

CRAWL_CONTENT_TYPE_WHITELIST_REGEX = re.compile(r'text/html')

CRAWL_URL_BLACKLIST_REGEX = re.compile(r'/activity/')

NO_COLOR = False
VERBOSITY = 2

ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
ssl_context.options &= ssl.CERT_NONE


class Style:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def info(string):
        if NO_COLOR:
            return string
        return "%s%s%s" % (Style.OK_BLUE, string, Style.ENDC)

    def warn(string):
        if NO_COLOR:
            return string
        return "%s%s%s" % (Style.WARNING, string, Style.ENDC)

    def error(string):
        if NO_COLOR:
            return string
        return "%s%s%s" % (Style.FAIL, string, Style.ENDC)

    def result(string):
        if NO_COLOR:
            return string
        return "%s%s%s" % (Style.OKGREEN, string, Style.ENDC)


def log(priority, string):
    if priority <= VERBOSITY:
        print(string)

class MapItem:
    code = 200
    children = []


def main():
    site_url = sys.argv[1]
    site_map = map_site(site_url)

    external_urls = get_external_children(site_url, site_map)
    for url in sorted(external_urls):
        try:
            request.urlopen(url)
            log(1, Style.result('EXT: %s' % url))
        except URLError as e:
            log(1, Style.error('EXT-ERROR: %d %s' % (e.code, url)))


def get_external_children(site_url, site_map):
    site_host = strip_path(site_url)
    external = set()

    for item in site_map.values():
        for child in item.children:
            if not child.startswith(site_host):
                external.add(child)

    return external


def map_site(site_url):
    site_map = {}

    to_crawl = [site_url]
    while to_crawl:
        next_crawl = to_crawl.pop(0)
        new_crawl = crawl(next_crawl, site_url, site_map)
        to_crawl += new_crawl

    return site_map


def crawl(url, site_host, site_map):
    if url in site_map:
        return []

    log(2, 'CRAWL: %s' % url)
    map_item = MapItem()
    site_map[url] = map_item

    if not url.startswith(site_host):
        log(2, Style.warn('SKIP: external %s' % url))
        return []

    if CRAWL_URL_BLACKLIST_REGEX.search(url):
        log(2, Style.warn('SKIP: blacklist %s' % url))
        return []

    try:
        response = request.urlopen(url, context=ssl_context)
    except URLError as e:
        log(2, Style.error('ERROR: %d %s' % (e.code, url)))
        map_item.code = e.code
        return []

    if not CRAWL_CONTENT_TYPE_WHITELIST_REGEX.search(response.info().get('content-type')):
        log(2, Style.warn('SKIP: content-type %s' % url))
        return []

    content = (
            response.read()
            .decode('utf-8')
            .replace(r'\n', '\n')
            .replace(r'\r', '\r'))

    for match in URL_REGEX.finditer(content):
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

if __name__ == '__main__':
    main()
