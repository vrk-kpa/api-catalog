#!/usr/bin/python3

from optparse import OptionParser
from urllib import request, parse
from urllib.error import URLError, HTTPError
import ssl
import re


ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
ssl_context.options &= ssl.CERT_NONE


class Settings:
    SINGLETON = None

    def __init__(self):
        self.url_pattern = r'href="((http[s]?://|/)(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)"'
        self.crawl_content_type_whitelist_pattern = r'text/html'
        self.crawl_url_blacklist_pattern = r'/activity/'
        self.no_color = False
        self.verbosity = 2

    # Options singleton
    @classmethod
    def instance(cls):
        if Settings.SINGLETON is None:
            Settings.SINGLETON = Settings()
        return Settings.SINGLETON


class Style:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    @classmethod
    def colored(cls, string, color):
        return string if Settings.instance().no_color else ("%s%s%s" % (color, string, Style.ENDC))

    def info(string):
        return Style.colored(string, Style.OK_BLUE)

    def warn(string):
        return Style.colored(string, Style.WARNING)

    def error(string):
        return Style.colored(string, Style.FAIL)

    def result(string):
        return Style.colored(string, Style.OKGREEN)


def log(priority, string):
    if priority <= Settings.instance().verbosity:
        print(string)


class MapItem:
    def __init__(self):
        self.code = 200
        self.children = []


def main():
    settings = Settings.instance()
    usage = "usage: %prog [options] site_url"
    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--content-type-regex", metavar="REGEX", dest="content_type_regex",
                      help="whitelist regex for content-type of crawled nodes",
                      default=settings.crawl_content_type_whitelist_pattern)
    parser.add_option("-b", "--url-blacklist-regex", metavar="REGEX", dest="url_blacklist_regex",
                      help="blacklist regex for URLs of crawled nodes",
                      default=settings.crawl_url_blacklist_pattern)
    parser.add_option("-v", action="count", dest="verbosity", default=0,
                      help="output verbosity")
    parser.add_option("--no-color", action="store_true", dest="no_color")

    (opts, args) = parser.parse_args()

    if len(args) != 1:
        parser.print_help()
        return

    site_url = args[0]
    settings.crawl_content_type_whitelist_pattern = opts.content_type_regex
    settings.crawl_url_blacklist_pattern = opts.url_blacklist_regex
    settings.verbosity = opts.verbosity
    settings.no_color = opts.no_color

    site_map = map_site(site_url)

    external_urls = get_external_children(site_url, site_map)
    for url in sorted(external_urls):
        try:
            request.urlopen(url)
            log(1, Style.result('EXT: %s' % url))
        except HTTPError as e:
            referrers = find_referrers(url, site_map)
            log(0, Style.error('EXT-ERROR-HTTP: %d %s' % (e.code, url)))
            log(0, Style.error('\n'.join('  REF: %s' % r for r in referrers)))
        except URLError as e:
            referrers = find_referrers(url, site_map)
            log(0, Style.error('EXT-ERROR: %s %s' % (e.reason, url)))
            log(0, Style.error('\n'.join('  REF: %s' % r for r in referrers)))


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


def map_site(site_url):
    site_map = {}
    settings = Settings.instance()
    crawl_url_blacklist_regex = re.compile(settings.crawl_url_blacklist_pattern)
    crawl_content_type_whitelist_regex = re.compile(settings.crawl_content_type_whitelist_pattern)
    url_regex = re.compile(settings.url_pattern)

    to_crawl = [site_url]
    while to_crawl:
        next_crawl = to_crawl.pop(0)
        new_crawl = crawl(next_crawl, site_url, site_map,
                          crawl_url_blacklist_regex,
                          crawl_content_type_whitelist_regex,
                          url_regex)
        to_crawl += new_crawl

    return site_map


def crawl(url, site_host, site_map,
          crawl_url_blacklist_regex,
          crawl_content_type_whitelist_regex,
          url_regex):
    if url in site_map:
        return []

    log(2, 'CRAWL: %s' % url)
    map_item = MapItem()
    site_map[url] = map_item

    if not url.startswith(site_host):
        log(2, Style.warn('SKIP: external %s' % url))
        return []

    if crawl_url_blacklist_regex.search(url):
        log(2, Style.warn('SKIP: blacklist %s' % url))
        return []

    try:
        response = request.urlopen(url, context=ssl_context)
    except URLError as e:
        log(2, Style.error('ERROR: %d %s' % (e.code, url)))
        map_item.code = e.code
        return []

    if not crawl_content_type_whitelist_regex.search(response.info().get('content-type')):
        log(2, Style.warn('SKIP: content-type %s' % url))
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


if __name__ == '__main__':
    main()
