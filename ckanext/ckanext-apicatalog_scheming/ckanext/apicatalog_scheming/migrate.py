from collections import deque


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
