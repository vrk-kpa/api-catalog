# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.define "catalog" do |server|
    server.vm.box = "bento/ubuntu-20.04"
    server.vm.network :private_network, ip: "10.100.10.10"
    server.vm.network :private_network, ip: "10.100.10.11"
    server.vm.hostname = "api-catalog"

    case RUBY_PLATFORM
    when /mswin|msys|mingw|cygwin|bccwin|wince|emc/
      # Fix Windows file rights, otherwise Ansible tries to execute files
      server.vm.synced_folder "./", "/vagrant", :mount_options => ["dmode=755","fmode=644"]
    else
      # Basic VM synced folder mount
      server.vm.synced_folder "", "/vagrant"
    end

    server.vm.provision "ansible_local" do |ansible|
       ansible.playbook = "ansible/deploy-all.yml"
       ansible.verbose = "v"
       ansible.inventory_path = "ansible/inventories/vagrant"
       ansible.config_file = "ansible/ansible.cfg"
       ansible.limit = "all"
       ansible.pip_install_cmd = "sudo apt-get install -y python3-distutils && curl -s https://bootstrap.pypa.io/pip/3.6/get-pip.py | sudo python3"
       ansible.install_mode = "pip"
    end
    server.vm.provider "virtualbox" do |vbox|
      vbox.gui = false
      vbox.memory = 2048
      vbox.customize ["modifyvm", :id, "--nictype1", "virtio"]
    end
  end
end
