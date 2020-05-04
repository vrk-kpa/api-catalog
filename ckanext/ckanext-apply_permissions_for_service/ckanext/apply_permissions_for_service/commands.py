import ckan.plugins as p

class ApplyPermissionsCommand(p.toolkit.CkanCommand):
    """
    Database initialization for applying permissions for services

    Usage:

        paster apply_permissions init
            - Creates the database table for storing requests.
    """


    summary = __doc__.split('\n')[0]
    usage = __doc__
    min_args = 0

    def __init__(self, name):
        super(ApplyPermissionsCommand, self).__init__(name)


    def command(self):

        if not self.args or self.args[0] in ['--help', '-h', 'help']:
            print ApplyPermissionsCommand.__doc__
            return

        cmd = self.args[0]
        self._load_config()

        if cmd == 'init':
            self.init_db()

    def init_db(self):
        import ckan.model as model
        from ckanext.apply_permissions_for_service.model import init_table
        init_table(model.meta.engine)