# -*- mode: ruby -*-
# vi: set ft=ruby :
require 'fileutils'
#require "vagrant/plugin"

Vagrant.configure("2") do |config|
  config.ssh.insert_key = false
  config.ssh.forward_agent = true

  config.vm.box = "bento/centos-8"

  FileUtils.mkdir_p ".vagrant/cache/yum"
  config.vm.synced_folder ".vagrant/cache/yum", "/var/cache/yum"

  FileUtils.mkdir_p ".vagrant/cache/pip"
  config.vm.synced_folder ".vagrant/cache/pip", "/root/.cache/pip"

  if ENV['VAGRANT_IP']
    config.vm.network "private_network", ip: ENV['VAGRANT_IP']
  else
    config.vm.network "private_network", type: "dhcp"
  end

  config.vm.provider "virtualbox" do |vb|
    vb.gui = ENV['VAGRANT_GUI']
    vb.memory = "1024"
    vb.cpus = 2
  end
end
