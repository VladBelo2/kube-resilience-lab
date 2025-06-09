Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"
  config.vm.hostname = "kube-lab"
  config.vm.network "private_network", ip: "192.168.56.120"
  config.vm.provider "virtualbox" do |vb|
    vb.memory = 8192
    vb.cpus = 4
  end

  config.vm.provision "file", source: "env.conf", destination: "/home/vagrant/env.conf"
  config.vm.provision "file", source: "grafana", destination: "/home/vagrant/kube-resilience-lab/grafana"
  config.vm.provision "file", source: "prometheus", destination: "/home/vagrant/kube-resilience-lab/prometheus"
  # config.vm.provision "file", source: "docker-compose.yml", destination: "/home/vagrant/kube-resilience-lab/docker-compose.yml"
  config.vm.provision "file", source: "kubernetes", destination: "/home/vagrant/kube-resilience-lab/kubernetes"
  config.vm.provision "file", source: "python/flask-metrics-app", destination: "/home/vagrant/flask-metrics-app"
  config.vm.provision "shell", path: "provision.sh"
end
