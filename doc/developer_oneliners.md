
Deploy all configuration changes

    /src/ansible
    ansible-playbook -v -i inventories/vagrant deploy-all.yml

Check the logs to figure out what went wrong

    sudo tail -n 1000 /var/log/apache2/ckan_default.error.log

Run something with paster

    /usr/lib/ckan/default/bin/paster --plugin=ckan
    /usr/lib/ckan/default/bin/paster --plugin=ckan user --config=/etc/ckan/default/production.ini
    /usr/lib/ckan/default/bin/paster --plugin=ckan user --help --config=/etc/ckan/default/production.ini
    /usr/lib/ckan/default/bin/paster --plugin=ckan views create --config=/etc/ckan/default/production.ini

Note that `--help` seems to be a safer option than `help`. With some subcommands `help` does not seem to work, or produces less output.
