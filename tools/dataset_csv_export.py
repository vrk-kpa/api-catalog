#!/usr/bin/python3

import requests
import csv
import sys
from optparse import OptionParser

usage = "usage: %prog <CKAN_URL>"
parser = OptionParser(usage=usage)
(opts, args) = parser.parse_args()
if len(args) != 1:
    parser.print_help()
    sys.exit(1)

CKAN_URL = args[0]
PACKAGE_SEARCH_URL = "%s/api/action/package_search" % CKAN_URL
SOLR_Q = ""

def json_get(url, headers={}):
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Got error from API: %s", response.text)

datasets = json_get("%s?rows=1000&q=%s" % (PACKAGE_SEARCH_URL, SOLR_Q))['result']['results']

if len(datasets) == 1000:
    print("Exactly 1000 datasets received. This script needs to be fixed to handle paging.")
    sys.exit(1)

fields = [
        'organization_title', 'organization_name', 'organization_description',
        'title', 'description', 'xroad_membercode', 'xroad_subsystemcode', 'resources', 
        'maintainer', 'maintainer_email', 'maintainer_phone'
        ]

writer = csv.DictWriter(sys.stdout, fields, quoting=csv.QUOTE_ALL)

writer.writeheader()
for dataset in datasets:
    values = {
            'title': dataset['title'],
            'description': dataset['notes'],
            'resources': ', '.join(r['name'] for r in dataset['resources']),
            'xroad_membercode': dataset['xroad_membercode'],
            'xroad_subsystemcode': dataset['xroad_subsystemcode'],
            'maintainer': dataset.get('maintainer', ''),
            'maintainer_email': dataset.get('maintainer_email', ''),
            'maintainer_phone': dataset.get('maintainer_phone', ''),
            'organization_title': dataset['organization']['title'],
            'organization_name': dataset['organization']['name'],
            'organization_description': dataset['organization']['description']
            }
    writer.writerow(values)
