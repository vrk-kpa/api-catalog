## API Catalog (*Liityntäkatalogi*)

This repository provides the API catalog of the Finnish National Data Exchange Layer (*Kansallinen palveluväylä*). The catalog provides a search engine for the interaces available on the data exchange layer.

A demo of the catalog is available at [liityntakatalogi.qa.suomi.fi](http://liityntakatalogi.qa.suomi.fi/)

### Getting started

Prerequisites:

- [Vagrant](https://www.vagrantup.com/) (tested on 1.7.4)
- [VirtualBox](https://www.virtualbox.org/) (tested on 5.0.0)

Start up the vagrant:

    vagrant up

After [Ansible](http://www.ansible.com/) provisions the system, the service will be running in the virtual machine and is available from your host machine at http://10.100.10.10/

Admin user credentials are `admin:admin` and a regular user is `test:test`.

To reprovision the server (i.e. to run Ansible) again:

    vagrant provision

You can ssh into the server:

    vagrant ssh

And you can also run Ansible manually inside the virtual machine:

    vagrant ssh
    cd /src/ansible
    ansible-playbook -v -i inventories/vagrant deploy-all.yml

### Repository structure

    .
    ├── ansible
    │   ├── deploy-all.yml                  Top-level playbook for configuring complete service
    │   ├── inventories                     Target server lists (hostname, ssh user and key)
    │   │   ├── prod
    │   │   ├── qa
    │   │   └── vagrant
    │   ├── roles                           Main configuration
    │   └── vars                            Variables common for all roles
    │       ├── api-catalog-secrets         Passwords and other secrets (not included here)
    │       ├── common.yml                  Variables common for all roles and environments
    │       ├── environment-specific        Configuration specific for each deployment env
    │       │   ├── prod.yml
    │       │   ├── qa.yml
    │       │   └── vagrant.yml
    │       └── secrets-defaults.yml        Default passwords, used in Vagrant
    ├── ckanext                             Custom CKAN extensions
    │   ├── ckanext-apicatalog_scheming     Custom schema, additional fields
    │   ├── ckanext-apicatalog_ui           Template and style customizations
    │   └── ckanext-fluentall               Localization to all dataset fields
    ├── doc                                 Documentation
    └── Vagrantfile                         Configuration for local development environment

### Support / Contact / Contribution

Please file a [new issue](https://github.com/vrk-kpa/api-catalog/issues) at GitHub.

### Copying and License

This material is copyright (c) 2015 Population Register Centre.

CKAN-related content like [CKAN extensions](/ckanext) are licensed under the GNU Affero General Public License (AGPL) v3.0 whose full text may be found at: http://www.fsf.org/licensing/licenses/agpl-3.0.html

All other content in this repository is licensed under the MIT license.
