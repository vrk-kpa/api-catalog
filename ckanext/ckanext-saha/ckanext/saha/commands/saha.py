import sys

from ckan.lib.cli import CkanCommand
from ckanext.saha.model import define_tables
from ckanext.saha.plugin import SahaPlugin


class SahaCommand(CkanCommand):
    '''SahaCommand

   Usage:

   saha initdb
       - Initialize SAHA tables

   saha update
       - Updates organization data from SAHA
    '''

    summary = __doc__.split('\n')[0]
    usage = __doc__

    def __init__(self, name):
        super(SahaCommand, self).__init__(name)
        define_tables()

    def command(self):
        self._load_config()
        if len(self.args) == 0:
            self.parser.print_usage()
            sys.exit(1)
        cmd = self.args[0]

        if cmd == 'initdb':
            self.initdb()
        elif cmd == 'update':
            self.update()

    def initdb(self):
        from ckanext.saha.model import setup as db_setup
        print('Initializing SAHA tables...')
        db_setup()

    def update(self):
        print('Updating SAHA tables...')
        plugin = SahaPlugin()
        if plugin.login():
            if plugin.update():
                print('Updating SAHA tables...')
            else:
                print('ERROR: Could not get update information')
        else:
            print('ERROR: Could not log into SAHA')
