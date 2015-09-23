# Liityntäkatalogi

Kansallisen palveluväylän liityntäkatalogi

Demo is a available at [liityntakatalogi.palveluvayla.com/](http://liityntakatalogi.palveluvayla.com/)

## Getting started

Prerequisites:

- Vagrant (tested on 1.7.4)
- VirtualBox (tested on 5.0.0)

Start up the vagrant:

    vagrant up

The service will be available from your host machine at http://10.100.10.10/

Admin user credentials are `admin:katalogi`.

To reprovision the server (run ansible) again:

    vagrant provision

## Development

Edit the following files:

- **style:** [main.min.css](css/main.min.css)
- **localization:** [ckan.po](ansible/roles/ckan/files/katalogi/ckan.po) (requires reprovisioning)
- **schema:** [ckan_dataset.json.j2](ansible/roles/ckan/templates/ckan_dataset.json.j2) (requires reprovisioning)

To clean the database:

    vagrant ssh
    cd /src/ansible
    sh clean-database.sh
