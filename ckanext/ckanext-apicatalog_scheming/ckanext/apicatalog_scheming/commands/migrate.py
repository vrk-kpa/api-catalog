# -*- coding: utf-8 -*-

import sys
import itertools
import json

from ckan.common import config
from ckan.lib.cli import CkanCommand
import ckan.plugins.toolkit as toolkit
get_action = toolkit.get_action


class Migrate(CkanCommand):
    '''Migrate

   Usage:

   migrate notes_translated
       - Populate notes_translated from translated notes

   migrate title_translated
       - Populate title_translated from translated titles
    '''

    summary = __doc__.split('\n')[0]
    usage = __doc__

    def __init__(self, name):
        super(Migrate, self).__init__(name)
        self.parser.add_option('--dry-run', dest='dry_run',
                               action='store_true', default=False,
                               help='Print changes without making them')
    def command(self):
        self._load_config()
        if len(self.args) == 0:
            self.parser.print_usage()
            sys.exit(1)
        cmd = self.args[0]

        if cmd == 'notes_translated':
            self.notes_translated()

        elif cmd == 'title_translated':
            self.title_translated()


    def notes_translated(self):
        default_locale = config.get('ckan.locale_default', 'en')
        package_patches = []
        resource_patches = []
        for package in package_generator('*:*', 1000):
            try:
                notes = json.loads(package.get('notes'))
                if isinstance(notes, dict):
                    patch = {
                            'id': package['id'],
                            'notes': notes.get(default_locale, ''),
                            'notes_translated': notes
                            }
                    package_patches.append(patch)
            except:
                pass

            for resource in package.get('resources', []):
                try:
                    description = json.loads(resource.get('description'))
                    if isinstance(description, dict):
                        patch = {
                                'id': resource['id'],
                                'description': description.get(default_locale, ''),
                                'description_translated': description
                                }
                        resource_patches.append(patch)
                except:
                    pass

        self.apply_patches(package_patches, resource_patches)


    def title_translated(self):
        locales = config.get('ckan.locales_offered', ['en']).split()
        package_patches = []
        resource_patches = []
        for package in package_generator('*:*', 1000):
            try:
                if type(package.get('title_translated')) is dict:
                    continue
                title = package.get('title')
                patch = {
                        'id': package['id'],
                        'title': title,
                        'title_translated': {locale.split('_')[0]: title for locale in locales}
                        }
                package_patches.append(patch)
            except:
                pass

        self.apply_patches(package_patches, resource_patches)


    def apply_patches(self, package_patches, resource_patches):
        if not package_patches and not resource_patches:
            print 'Nothing to do.'
        elif self.options.dry_run:
            print '\n'.join('%s' % p for p in package_patches)
            print '\n'.join('%s' % p for p in resource_patches)
        else:
            package_patch = get_action('package_patch')
            resource_patch = get_action('resource_patch')
            context = {'ignore_auth': True}
            for patch in package_patches:
                package_patch(context, patch)
            for patch in resource_patches:
                resource_patch(context, patch)


def package_generator(query, page_size):
    context = {'ignore_auth': True}
    package_search = get_action('package_search')

    for index in itertools.count(start=0, step=page_size):
        data_dict = {'include_private': True, 'rows': page_size, 'q': query, 'start': index}
        packages = package_search(context, data_dict).get('results', [])
        for package in packages:
            yield package
        else:
            return

