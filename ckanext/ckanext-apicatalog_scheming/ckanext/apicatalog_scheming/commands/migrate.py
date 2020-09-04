# -*- coding: utf-8 -*-

import sys
import itertools
import json
import re
from pprint import pformat

from ckan.common import config
import click
from ckan.lib.cli import load_config, paster_click_group, click_config_option
import ckan.plugins.toolkit as toolkit
get_action = toolkit.get_action

from collections import deque


#
# Commands
#

content_group = paster_click_group(
    summary=u'Content modification tools'
)

@content_group.command(
    u'migrate',
    help=u'Migrates site content from one version to another'
)
@click_config_option
@click.argument('current_version')
@click.argument('target_version')
@click.option(u'--dryrun', is_flag=True)
@click.option(u'--path-index', type=int)
@click.pass_context
def migrate(ctx, config, current_version, target_version, dryrun, path_index):

    load_config(config or ctx.obj['config'])
    m = Migrate()

    for v1, v2, step in migrations():
        m.add(v1, v2, step)

    plans = m.plan(current_version, target_version)

    if not plans:
        print('No migration paths found from {} to {}'.format(current_version, target_version))
        sys.exit(1)
    elif len(plans) > 1:
        if path_index is None:
            print('Multiple migration paths found from {} to {}.'.format(current_version, target_version))
            print('Run this command again with the option --path-index <your selection>')
            for i, plan in enumerate(plans):
                print('{}: {}'.format(i, ' -> '.join(plan_to_path(plan))))
            sys.exit(1)

        plan = plans[int(path_index)]
    else:
        plan = plans[0]

    print('Using migration path: {}'.format(' -> '.join(plan_to_path(plan))))

    if dryrun:
        print('Performing a dry run')

    for v1, v2, step in plan:
        print('Migrating from {} to {}'.format(v1, v2))
        step(ctx, config, dryrun)

    print('Finished migration successfully')


#
# Migrations
#

def migrations():
    return [('1.49.0', '1.50.0', no_changes),
            ('1.50.0', '1.51.0', migrate_1_50_0_to_1_51_0),
            ('1.51.0', '1.52.0', no_changes),
            ('1.52.0', '1.53.0', migrate_1_52_0_to_1_53_0),
            ('1.53.0', '1.54.0', no_changes),
            ('1.54.0', '1.54.1', no_changes),
            ('1.54.1', '1.55.0', migrate_1_54_1_to_1_55_0),
            ]


#
# Migration step functions
#

def no_changes(*args, **kwargs):
    pass

def migrate_1_50_0_to_1_51_0(ctx, config, dryrun):
    organization_patches = [{'id': org['id'],
                             'title_translated': {'fi': org['title']},
                             'description_translated': {'fi': org['description']}}
                            for org in org_generator()]
    apply_patches(organization_patches=organization_patches, dryrun=dryrun)


def migrate_1_52_0_to_1_53_0(ctx, config, dryrun):
    package_patches = []
    resource_patches = []
    organization_patches = []

    for dataset in package_generator():
        package_patches.append({'id': dataset['id'],
                                'keywords': {'fi': [tag['display_name']
                                             for tag in dataset.get('tags', [])]}})
        for resource in dataset.get('resources', []):
            harvested_from_xroad = True if resource.get('xroad_servicecode') else False
            resource_patches.append({'id': resource['id'],
                                     'harvested_from_xroad': harvested_from_xroad})

    for org in org_generator():
        if org.get('description_translated') != {'fi': ""} \
                and org.get('description_translated') != {'fi': "", 'sv': "", 'en': ""}:
            organization_patches.append({'id': org['id'], 'description_translated_modified_in_catalog': True})

    apply_patches(package_patches=package_patches, resource_patches=resource_patches,
                  organization_patches=organization_patches, dryrun=dryrun)


def migrate_1_54_1_to_1_55_0(ctx, config, dryrun):
    def is_json_object(s):
        if isinstance(s, dict):
            return True
        try:
            return isinstance(json.loads(s), dict)
        except ValueError:
            return False

    organization_patches = [{'id': org['id'],
                             'email_address': {lang: [org['email_address']]
                                               for lang in ['fi', 'sv', 'en']}}
                            for org in org_generator()
                            if 'email_address' in org
                            and not is_json_object(org['email_address'])]
    apply_patches(organization_patches=organization_patches, dryrun=dryrun)


#
# Utilities
#

def breadth_first_search(graph, start, end):
  visited = set()
  queue = deque([(start, [start])])
  results = []
  while queue:
    node, path = queue.popleft()
    if node == end:
      results.append(path)
      continue
    if node in visited:
      continue
    visited.add(node)
    for child in graph.get(node, []):
      queue.append((child, path + [child]))
  return results


class Migrate:
  def __init__(self):
    self.callbacks = {}
    self.graph = {}

  def add(self, version_from, version_to, callback):
    self.graph.setdefault(version_from, []).append(version_to)
    self.callbacks.setdefault(version_from, {})[version_to] = callback

  def plan(self, version_from, version_to):
    paths = breadth_first_search(self.graph, version_from, version_to)
    plans = []
    for path in paths:
      plan = [(path[i-1], path[i], self.callbacks[path[i-1]][path[i]])
              for i in range(1, len(path))]
      plans.append(plan)
    return plans


def plan_to_path(plan):
    return [plan[0][0]] + [v2 for v1, v2, step in plan]


def apply_patches(package_patches=[], resource_patches=[], organization_patches=[], dryrun=False):
    if not (package_patches or resource_patches or organization_patches):
        print('No patches to process.')
    elif dryrun:
        if package_patches:
            print('Package patches:')
            print('\n'.join(pformat(p) for p in package_patches))
        if resource_patches:
            print('Resource patches:')
            print('\n'.join(pformat(p) for p in resource_patches))
        if organization_patches:
            print('Organization patches:')
            print('\n'.join(pformat(p) for p in organization_patches))
    else:
        package_patch = get_action('package_patch')
        resource_patch = get_action('resource_patch')
        organization_patch = get_action('organization_patch')
        context = {'ignore_auth': True, 'allow_partial_update': True}
        for patch in package_patches:
            try:
                print("Migrating package %s" % patch['id'])
                package_patch(context, patch)
            except toolkit.ValidationError as e:
                print("Migration failed for package %s reason:" % patch['id'])
                print(e)
        for patch in resource_patches:
            try:
                print("Migrating resource %s" % patch['id'])
                resource_patch(context, patch)
            except toolkit.ValidationError as e:
                print("Migration failed for resource %s, reason" % patch['id'])
                print(e)
        for patch in organization_patches:
            try:
                print("Migrating organization %s" % patch['id'])
                organization_patch(context, patch)
            except toolkit.ValidationError as e:
                print("Migration failed for organization %s reason:" % patch['id'])
                print(e)


def package_generator(query='*:*', page_size=1000, context={'ignore_auth': True}, dataset_type='dataset'):
    package_search = get_action('package_search')

    # Loop through all items. Each page has {page_size} items.
    # Stop iteration when all items have been looped.
    for index in itertools.count(start=0, step=page_size):
        data_dict = {'include_private': True, 'rows': page_size, 'q': query, 'start': index,
                     'fq': '+dataset_type:' + dataset_type}
        data = package_search(context, data_dict)
        packages = data.get('results', [])
        for package in packages:
            yield package

        # Stop iteration all query results have been looped through
        if data["count"] < (index + page_size):
            return


def org_generator():
    context = {'ignore_auth': True}
    org_list = get_action('organization_list')
    orgs = org_list(context, {'all_fields': True, 'include_extras': True})
    for org in orgs:
        yield org
