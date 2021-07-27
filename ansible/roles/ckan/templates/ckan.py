#!/usr/lib/ckan/default/bin/python
import os
import sys
from pkg_resources import load_entry_point


paster_commands = ['create', 'help','make-config',
                   'points','post','request',
                   'serve','setup-app']
config = False


for num, arg in enumerate(sys.argv):
    if arg[:2] == '-i':
        instance = sys.argv[num + 1]
        sys.argv.pop(num)
        sys.argv.pop(num)
    if arg[:2] == '-c' or arg.startswith('--config'):
        config = True


if not config:
    try:
        config_file = '{{ ckan_ini }}'
        fh = open(config_file)
    except IOError as e:
        raise Exception('No {{ ckan_ini }}. '
                        'Either create one from production.ini.temp or use '
                        '-i instance_name or -c config_file')


if not config and len(sys.argv) > 1:
    if sys.argv[1] not in paster_commands:
        sys.argv.append('-c')
        sys.argv.append(config_file)
    # paster commands just accept config file as last arg
    if sys.argv[1] in ['serve', 'setup-app']:
        sys.argv.append(config_file)


sys.argv.insert(1, '--plugin=ckan')

if __name__ == '__main__':
    sys.exit(
        load_entry_point('PasteScript', 'console_scripts', 'paster')()
    )
