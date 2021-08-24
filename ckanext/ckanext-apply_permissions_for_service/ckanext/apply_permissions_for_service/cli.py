import click


@click.group()
def apply_permissions():
    'Database initialization for applying permissions for services'
    pass


@apply_permissions.command()
def init():
    import ckan.model as model
    from ckanext.apply_permissions_for_service.model import init_table
    init_table(model.meta.engine)


def get_commands():
    return [apply_permissions]
