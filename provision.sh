#!/bin/bash
set -e

# ─────────────────────────────────────────────
# Load config toggles
echo "📜 Loading env.conf toggles..."
source /home/vagrant/env.conf

# ─────────────────────────────────────────────
echo "📦 Installing base packages..."
apt update && apt install -y \
  curl wget git unzip gnupg lsb-release ca-certificates \
  net-tools iputils-ping dnsutils software-properties-common sudo

# ─────────────────────────────────────────────
if [ "$INSTALL_DOCKER" = "true" ]; then
  echo "🐳 Installing Docker & Compose..."
  apt install -y docker.io
  systemctl enable docker
  usermod -aG docker vagrant
  curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
  chmod +x /usr/local/bin/docker-compose
fi

# ─────────────────────────────────────────────
# 🔐 Create sudo user
echo "🔐 Creating a sudo user with SSH access..."
USERNAME="labuser"
PASSWORD="labuser123"
if ! id "$USERNAME" >/dev/null 2>&1; then
    echo "👤 Creating user '$USERNAME'..."
    adduser --disabled-password --gecos "" "$USERNAME"
    echo "$USERNAME:$PASSWORD" | chpasswd
    usermod -aG sudo,docker "$USERNAME"
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME
fi

# 🔧 Fix any cloud-init configs that override PasswordAuthentication
echo "🔧 Configuring SSH for password login..."
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
for file in /etc/ssh/sshd_config.d/*.conf; do
  sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' "$file" || true
done
systemctl restart ssh

# ─────────────────────────────────────────────
if [ "$INSTALL_ANSIBLE" = "true" ]; then
  echo "📦 Installing Ansible..."
  apt install -y ansible
fi

if [ "$INSTALL_PYTHON" = "true" ]; then
  echo "🐍 Installing Python..."
  apt install -y python3 python3-pip
  pip3 install --upgrade pip
fi

# ─────────────────────────────────────────────
if [ "$INSTALL_KUBERNETES" = "true" ]; then
  echo "⚙️  Installing K3s..."
  # Install K3s with readable kubeconfig
  curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644

  # Set up kubeconfig for the vagrant user
  mkdir -p /home/vagrant/.kube
  cp /etc/rancher/k3s/k3s.yaml /home/vagrant/.kube/config
  chown vagrant:vagrant /home/vagrant/.kube/config
  chmod 600 /home/vagrant/.kube/config

  # Automatically set KUBECONFIG for future sessions
  echo 'export KUBECONFIG=$HOME/.kube/config' >> /home/vagrant/.bashrc
fi

# ─────────────────────────────────────────────
echo "📁 Syncing project structure..."
mkdir -p /home/vagrant/kube-resilience-lab
cp -r /vagrant/* /home/vagrant/kube-resilience-lab
chown -R vagrant:vagrant /home/vagrant/kube-resilience-lab

# ─────────────────────────────────────────────
if [ "$INSTALL_K8S_DASHBOARD" = "true" ]; then
  echo "🧪 Installing Kubernetes Dashboard..."
  sudo -u vagrant kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml
  echo "🔒 Creating admin user..."
  sudo -u vagrant kubectl apply -f /home/vagrant/kube-resilience-lab/kubernetes/k8s-dashboard/admin-user.yml
  echo "🔑 Creating and displaying dashboard token..."
  TOKEN=$(sudo kubectl -n kubernetes-dashboard create token admin-user)
  # echo -e "\n📎 Dashboard Token:\n\n$TOKEN\n"
fi

# ─────────────────────────────────────────────
if [ "$INSTALL_FLASK_METRICS" = "true" ]; then
  echo "🚀 Deploying Flask app using Docker Hub image..."
  sudo -u vagrant kubectl apply -f /home/vagrant/kube-resilience-lab/kubernetes/manifests/flask-app.yml
fi

# ─────────────────────────────────────────────
if [ "$INSTALL_HELM" = "true" ]; then
  echo "📦 Installing Helm..."
  HELM_VERSION="v3.14.4"

  curl -fsSL https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz -o helm.tar.gz
  tar -xzf helm.tar.gz
  mv linux-amd64/helm /usr/local/bin/helm
  chmod +x /usr/local/bin/helm
  rm -rf linux-amd64 helm.tar.gz

  helm version
fi

# ─────────────────────────────────────────────
if [ "$INSTALL_NGINX" = "true" ]; then
  echo "🌐 Installing NGINX Ingress Controller..."

  export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

  helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
  helm repo update
  helm install nginx-ingress ingress-nginx/ingress-nginx --namespace ingress-nginx --create-namespace

  # Wait for the service to be available
  echo "⏳ Waiting for Ingress Controller service..."
  until kubectl -n ingress-nginx get svc nginx-ingress-ingress-nginx-controller &>/dev/null; do
    sleep 2
  done

  # Wait for the ingress controller pod to be Ready
  echo "⏳ Waiting for Ingress Controller pod to be ready..."
  kubectl wait --namespace ingress-nginx \
    --for=condition=Ready pod \
    --selector=app.kubernetes.io/component=controller \
    --timeout=120s

  # Patch to expose it on external IP
  echo "🌐 Patching NGINX Ingress to expose via external IP $IP_ADDRESS..."
  kubectl patch svc nginx-ingress-ingress-nginx-controller \
    -n ingress-nginx \
    -p "{\"spec\": {\"externalIPs\": [\"$IP_ADDRESS\"]}}"
fi

# ─────────────────────────────────────────────
if [ "$INSTALL_K8S_MONITORING" = "true" ]; then
  echo "📦 Creating Grafana ConfigMaps..."

  declare -A configmaps=(
    ["grafana-datasources"]="/home/vagrant/kube-resilience-lab/grafana/provisioning/datasources/prometheus.yml"
    ["grafana-dashboards"]="/home/vagrant/kube-resilience-lab/grafana/provisioning/dashboards/flask_dashboards.yml"
    ["flask-dashboard-json"]="/home/vagrant/kube-resilience-lab/grafana/dashboards/flask_metrics.json"
    ["todo-dashboard-json"]="/home/vagrant/kube-resilience-lab/grafana/dashboards/todo_metrics.json"
  )

  for name in "${!configmaps[@]}"; do
    file="${configmaps[$name]}"
    if [ -f "$file" ]; then
      kubectl create configmap "$name" \
        --from-file="$file" \
        --dry-run=client -o yaml | kubectl apply -f -
      echo "✔️ Created ConfigMap: $name"
    else
      echo "⚠️ Skipped missing file for ConfigMap: $name → $file"
    fi
  done

  echo "📈 Deploying Prometheus & Grafana to K8s..."
  for file in /home/vagrant/kube-resilience-lab/kubernetes/manifests/*.yaml; do
    echo "🔹 Applying $file"
    sudo -u vagrant kubectl apply -f "$file"
  done
fi

# ─────────────────────────────────────────────
if [ "$INSTALL_INGRESS_RULES" = "true" ]; then
  echo "🌐 Creating Ingress rules..."
  for file in /home/vagrant/kube-resilience-lab/kubernetes/ingress/*.yaml; do
    echo "🔹 Applying $file"
    sudo -u vagrant kubectl apply -f "$file"
  done
fi

# ─────────────────────────────────────────────
# ✅ Success
echo "✅ Setup complete!"
# Display IPs
# all_ips=$(ip -o -4 addr show | awk '!/127.0.0.1/ && !/docker/ {print $2, $4}' | cut -d/ -f1)
# nat_ip=""
# bridged_ip=""

# while read -r iface ip; do
#   [[ "$ip" == 10.0.2.* ]] && nat_ip=$ip
#   [[ "$ip" == 192.168.* ]] && bridged_ip=$ip
# done <<< "$all_ips"

# echo ""
# echo "✅ VM is ready!"
# [[ -n "$nat_ip" ]] && echo "🌐 NAT IP:      $nat_ip (vagrant@)"
# [[ -n "$bridged_ip" ]] && {
#   echo "📡 Wi-Fi IP:    $bridged_ip"
echo "🔍 Prometheus:    http://prometheus.kube-lab.local"
echo "📊 Grafana:       http://grafana.kube-lab.local"
echo "🧪 K8s Dashboard: https://k8s-dashboard.kube-lab.local"
echo "🐍 Flask App:     http://flask.kube-lab.local"
echo "🧾 To-Do App:     http://todo.kube-lab.local/"
echo "🔑 K8s Dashboard Token:"
echo ""
echo "$TOKEN"
echo ""
echo "📎 Add this to your macOS /etc/hosts:"
echo "$IP_ADDRESS flask.kube-lab.local grafana.kube-lab.local prometheus.kube-lab.local k8s-dashboard.kube-lab.local todo.kube-lab.local"
# }
