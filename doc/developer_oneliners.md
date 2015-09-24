
Deploy all configuration changes

    /src/ansible
    ansible-playbook -v -i inventories/vagrant deploy-all.yml

Check the logs to figure out what went wrong

    sudo tail -n 1000 /var/log/apache2/ckan_default.error.log
