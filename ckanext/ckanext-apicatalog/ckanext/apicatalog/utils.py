import ckan.plugins.toolkit as toolkit
import itertools
from typing import List, Dict, Any

ResourceDict = Dict[str, Any]


def package_generator(context, query='*:*', page_size=1000, dataset_type='dataset'):
    package_search = toolkit.get_action('package_search')

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


def organization_generator(context, options={}, page_size=None):
    if page_size is None:
        # Default value for ckan.group_and_organization_list_max is 25
        page_size = toolkit.config.get('ckan.group_and_organization_list_max', 25)

    organization_list = toolkit.get_action('organization_search')

    data_dict = options.copy()
    del data_dict['include_extras']
    del data_dict['all_fields']

    # Loop through all items. Each page has {page_size} items.
    # Stop iteration when all items have been looped.
    for index in itertools.count(start=0, step=page_size):
        data_dict.update({'rows': page_size, 'start': index})
        organizations = organization_list(context, data_dict)

        # Empty page, previous must have been the last one
        if not organizations.get('results', None):
            return

        for organization in organizations.get('results', None):
            yield organization

        # Incomplete page, must be the last one
        if len(organizations.get('results', [])) < page_size:
            return


def filter_allowed_resources(resources: List[ResourceDict], organization_id: str, user_name: str) -> List[ResourceDict]:
    if user_name:
        user_orgs = [{'name': o['name'], 'id': o['id']} for o in toolkit.get_action('organization_list_for_user')(
            {'ignore_auth': True},
            {'id': user_name, 'permission': 'read'})]
    else:
        user_orgs = []

    user_in_organization = any(o.get('id', None) == organization_id for o in user_orgs)

    def is_not_removed(resource: Dict) -> bool:
        return resource.get('xroad_removed') is not True

    def is_public(resource: Dict) -> bool:
        return resource.get('access_restriction_level', '') in ('', 'public')

    def is_private(resource: Dict) -> bool:
        return resource.get('access_restriction_level', '') == 'private'

    def in_allowed_organizations(resource: Dict) -> bool:
        orgs: List[str] = resource.get('allowed_organizations', '').split(',')
        return any(o.get('name') in orgs for o in user_orgs)

    def is_allowed(resource):
        return is_public(resource) or (
                is_private(resource) and (
                    user_in_organization
                    or in_allowed_organizations(resource)))

    return [resource for resource in resources if is_not_removed(resource) and is_allowed(resource)]
