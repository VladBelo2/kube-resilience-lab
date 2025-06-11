Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"
  config.vm.hostname = "kube-lab"
  config.vm.network "private_network", ip: "192.168.56.120"
  config.vm.provider "virtualbox" do |vb|
    vb.memory = 8192
    vb.cpus = 4
  end

  # 🧾 Configs and project structure
  config.vm.provision "file", source: "env.conf", destination: "/home/vagrant/env.conf"
  config.vm.provision "file", source: "kubernetes", destination: "/home/vagrant/kube-resilience-lab/kubernetes"
  # config.vm.provision "file", source: "grafana", destination: "/home/vagrant/kube-resilience-lab/grafana"

  # 🐍 Python apps
  config.vm.provision "file", source: "python/apps/microfail-app", destination: "/home/vagrant/microfail-app"
  config.vm.provision "file", source: "python/apps/todo-app", destination: "/home/vagrant/todo-app"
  config.vm.provision "file", source: "python/apps/remediator", destination: "/home/vagrant/remediator"
  config.vm.provision "file", source: "python/apps/devops-utils", destination: "/home/vagrant/devops-utils"

  # 🔧 Shell provisioner
  config.vm.provision "shell", path: "provision.sh"
end
