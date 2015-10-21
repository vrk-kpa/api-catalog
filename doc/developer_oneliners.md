
### Deploy all configuration changes

    /src/ansible
    ansible-playbook -v -i inventories/vagrant deploy-all.yml

### Check the logs to see what went wrong

    sudo tail -n 1000 /var/log/apache2/ckan_default.error.log

### Run something with paster

    /usr/lib/ckan/default/bin/paster --plugin=ckan
    /usr/lib/ckan/default/bin/paster --plugin=ckan user --config=/etc/ckan/default/production.ini
    /usr/lib/ckan/default/bin/paster --plugin=ckan user --help --config=/etc/ckan/default/production.ini
    /usr/lib/ckan/default/bin/paster --plugin=ckan views create --config=/etc/ckan/default/production.ini

Note that `--help` seems to be a safer option than `help`. With some subcommands `help` does not seem to work, or produces less output.

### Run CKAN in debug mode

This will run CKAN in port 5000. Footer and header have useful template-related information.

    sudo nano /etc/ckan/default/production.ini
    # Set debug = true
    sudo service apache2 stop
    sudo cp /usr/lib/ckan/default/src/ckan/ckan/public/base/css/main.debug.min.css /usr/lib/ckan/default/src/ckan/ckan/public/base/css/main.debug.css
    sudo /usr/lib/ckan/default/bin/paster serve /etc/ckan/default/production.ini
