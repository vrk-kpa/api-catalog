from pprint import pformat
import itertools
import json
import ckan.plugins.toolkit as toolkit
get_action = toolkit.get_action


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
        context = {'ignore_auth': True}
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
