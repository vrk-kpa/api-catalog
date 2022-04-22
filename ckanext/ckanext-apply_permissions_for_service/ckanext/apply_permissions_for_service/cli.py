import click


@click.group()
def apply_permissions():
    'Database initialization for applying permissions for services'
    pass


def get_commands():
    return [apply_permissions]
