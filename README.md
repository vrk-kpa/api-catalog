# API Catalog

This repository provides the API catalog of the Finnish "service bus" (*Kansallinen palveluväylä*).

A demo is a available at [liityntakatalogi.palveluvayla.com](http://liityntakatalogi.palveluvayla.com/)

## Getting started

Prerequisites:

- [Vagrant](https://www.vagrantup.com/) (tested on 1.7.4)
- [VirtualBox](https://www.virtualbox.org/) (tested on 5.0.0)

Start up the vagrant:

    vagrant up

After [Ansible](http://www.ansible.com/) provisions the system, the service will be running in the virtual machine and is available from your host machine at http://10.100.10.10/

Admin user credentials are `admin:katalogi`.

To reprovision the server (i.e. to run Ansible) again:

    vagrant provision

You can ssh into the server:

    vagrant ssh

And you can also run Ansible manually:

    vagrant ssh
    cd /src/ansible
    ansible-playbook -v -i inventories/vagrant deploy-all.yml

## Development

Edit the following files:

- **style:** [ckanext-apicatalog_ui](ckanext/ckanext-apicatalog_ui) (reprovision ckan-extension)
- **localization:** [ckan.po](ansible/roles/ckan-translations/files/ckan.po) (reprovision ckan-translations)
- **schema:** [ckanext-apicatalog_scheming](ckanext/ckanext-apicatalog_scheming/ckanext/apicatalog_scheming/schemas/dataset.json) (reprovision ckan-extension)

To clean the database (destroys all data and recreates databases):

    vagrant ssh
    cd /src/ansible
    ansible-playbook -v -i inventories/vagrant vagrant-recreate-database.yml
