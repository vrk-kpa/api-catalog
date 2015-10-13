# -*- mode: ruby -*-
# vi: set ft=ruby :

# Pre-provisioner shell script installs Ansible into the guest and continues
# to provision rest of the system in the guest. Works also on Windows.
$script = <<SCRIPT
if [ ! -f /vagrant_bootstrap_done.info ]; then
  sudo apt-get update
  sudo apt-get -y dist-upgrade
  sudo apt-get -y install python-dev python-pip
  sudo pip install -U ansible
  sudo touch /vagrant_bootstrap_done.info
fi
cd /src/ansible && ansible-playbook -i inventories/vagrant deploy-all.yml
SCRIPT

VAGRANTFILE_API_VERSION = "2"
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.define "catalog" do |server|
    server.vm.box = "ubuntu/trusty64"
    server.vm.box_url = "https://vagrantcloud.com/ubuntu/boxes/trusty64"
    server.vm.network :private_network, ip: "10.100.10.10"
    server.vm.hostname = "api-catalog"

    case RUBY_PLATFORM
    when /mswin|msys|mingw|cygwin|bccwin|wince|emc/
      # Fix Windows file rights, otherwise Ansible tries to execute files
      server.vm.synced_folder "./", "/src", :mount_options => ["dmode=755","fmode=644"]
    else
      # Basic VM synced folder mount
      server.vm.synced_folder "", "/src"
    end

    server.vm.provision "shell", inline: $script
    server.vm.provider "virtualbox" do |vbox|
      vbox.gui = false
      vbox.memory = 2048
    end
  end
end
