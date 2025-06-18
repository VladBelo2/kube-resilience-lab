#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────
# Load config toggles
echo "[OK] 📜 Loading env.conf toggles..."
if [ -f /home/vagrant/env.conf ]; then
  sed -i 's/\r$//' /home/vagrant/env.conf
  . /home/vagrant/env.conf
  echo "[DEBUG] Loaded env.conf successfully"
  echo "[DEBUG] INSTALL_KUBERNETES=$INSTALL_KUBERNETES"
else
  echo "[ERROR] env.conf not found!" >&2
  exit 1
fi

# ─────────────────────────────────────────────
echo "[OK] 📦 Installing base packages..."
apt update && apt install -y \
  curl wget git unzip gnupg lsb-release ca-certificates jq \
  net-tools iputils-ping dnsutils software-properties-common sudo

# ─────────────────────────────────────────────
if [ "$INSTALL_DOCKER" = "true" ]; then
  echo "[OK] 🐳 Installing Docker & Compose..."
  apt install -y docker.io
  systemctl enable docker
  usermod -aG docker vagrant
  curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
  chmod +x /usr/local/bin/docker-compose
fi

# ─────────────────────────────────────────────
# 🔐 Create sudo user
echo "[OK] 🔐 Creating a sudo user with SSH access..."
USERNAME="labuser"
PASSWORD="labuser123"
if ! id "$USERNAME" >/dev/null 2>&1; then
  echo "[OK] 👤 Creating user '$USERNAME'..."
  adduser --disabled-password --gecos "" "$USERNAME"
  echo "$USERNAME:$PASSWORD" | chpasswd
  usermod -aG sudo,docker "$USERNAME"
  echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME
fi

# 🔧 Fix any cloud-init configs that override PasswordAuthentication
echo "[OK] 🔧 Configuring SSH for password login..."
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
for file in /etc/ssh/sshd_config.d/*.conf; do
  sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' "$file" || true
done
systemctl restart ssh

# ─────────────────────────────────────────────
if [ "$INSTALL_ANSIBLE" = "true" ]; then
  echo "[OK] 📦 Installing Ansible..."
  apt install -y ansible
fi

if [ "$INSTALL_PYTHON" = "true" ]; then
  echo "[OK] 🐍 Installing Python..."
  apt install -y python3 python3-pip
  pip3 install --upgrade pip
fi

# ─────────────────────────────────────────────
if [ "$INSTALL_KUBERNETES" = "true" ]; then
  echo "[OK] ⚙️ Installing K3s..."
  curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644
  # chmod 600 /etc/rancher/k3s/k3s.yaml

  echo "[INFO] ⏳ Waiting for /etc/rancher/k3s/k3s.yaml to exist..."
  until [ -f /etc/rancher/k3s/k3s.yaml ]; do
    sleep 2
  done

  mkdir -p /home/vagrant/.kube
  cp /etc/rancher/k3s/k3s.yaml /home/vagrant/.kube/config
  chown vagrant:vagrant /home/vagrant/.kube/config
  chmod 600 /home/vagrant/.kube/config

  echo 'export KUBECONFIG=$HOME/.kube/config' >> /home/vagrant/.bashrc
fi

# ─────────────────────────────────────────────
echo "[OK] 📁 Syncing project structure..."
mkdir -p /home/vagrant/kube-resilience-lab
# cp -r /vagrant/* /home/vagrant/kube-resilience-lab
chown -R vagrant:vagrant /home/vagrant/kube-resilience-lab

# ─────────────────────────────────────────────
if [ "$INSTALL_CORE_APPS" = "true" ]; then
  echo "[OK] 🚀 Deploying core apps..."

  for file in /home/vagrant/kube-resilience-lab/kubernetes/manifests/*-{deployment,service}.yaml; do
    echo "[INFO] 📦 Applying $file"
    kubectl apply -f "$file"
  done
fi

# ─────────────────────────────────────────────
if [ "$INSTALL_K8S_DASHBOARD" = "true" ]; then
  echo "[OK] 🧪 Installing K8s Dashboard..."
  sudo -u vagrant kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml
  sudo -u vagrant kubectl apply -f /home/vagrant/kube-resilience-lab/kubernetes/k8s-dashboard/admin-user.yml
  kubectl -n kubernetes-dashboard create sa static-admin-user --dry-run=client -o yaml | kubectl apply -f -
  kubectl create clusterrolebinding static-admin-user-binding \
    --clusterrole=cluster-admin \
    --serviceaccount=kubernetes-dashboard:static-admin-user \
    --dry-run=client -o yaml | kubectl apply -f -
  kubectl apply -f /vagrant/kubernetes/manifests/static-admin-user-token.yaml || true
  echo "[INFO] ⏳ Waiting for token..."
  sleep 8
  STATIC_TOKEN=$(kubectl -n kubernetes-dashboard get secret static-admin-user-token -o jsonpath="{.data.token}" | base64 --decode)
fi

# ─────────────────────────────────────────────
if [ "$INSTALL_HELM" = "true" ]; then
  echo "[OK] 📦 Installing Helm..."
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
  echo "[OK] 🌐 Installing NGINX Ingress Controller..."
  export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
  helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
  helm repo update
  helm install nginx-ingress ingress-nginx/ingress-nginx --namespace ingress-nginx --create-namespace
  echo "[INFO] ⏳ Waiting for Ingress service..."
  until kubectl -n ingress-nginx get svc nginx-ingress-ingress-nginx-controller &>/dev/null; do sleep 2; done
  echo "[INFO] ⏳ Waiting for Ingress Controller pod..."
  kubectl wait --namespace ingress-nginx --for=condition=Ready pod \
    --selector=app.kubernetes.io/component=controller \
    --timeout=120s
  echo "[INFO] 🌐 Patching NGINX Ingress external IP..."
  kubectl patch svc nginx-ingress-ingress-nginx-controller -n ingress-nginx \
    -p "{\"spec\": {\"externalIPs\": [\"$IP_ADDRESS\"]}}"
fi

# ─────────────────────────────────────────────
if [ "$INSTALL_K8S_MONITORING" = "true" ]; then
  echo "[OK] 🚀 Installing kube-prometheus-stack via Helm..."
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
  helm repo update
  kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
  helm install monitoring prometheus-community/kube-prometheus-stack \
    --namespace monitoring \
    -f /home/vagrant/kube-resilience-lab/kubernetes/helm/kube-prometheus-values.yaml

  echo "[OK] 📡 Applying ServiceMonitors..."
  kubectl apply -f /home/vagrant/kube-resilience-lab/kubernetes/monitoring/servicemonitors/

  echo "[OK] 📊 Creating Grafana dashboards ConfigMap..."
  kubectl apply -f /home/vagrant/kube-resilience-lab/kubernetes/monitoring/kube-lab-dashboards-configmap.yaml
fi

# ─────────────────────────────────────────────
if [ "$INSTALL_INGRESS_RULES" = "true" ]; then
  echo "[OK] 🌐 Applying Ingress rules..."
  for file in /home/vagrant/kube-resilience-lab/kubernetes/ingress/*.yaml; do
    echo "[INFO] 🔹 Applying $file"
    sudo -u vagrant kubectl apply -f "$file"
  done
fi

# ─────────────────────────────────────────────
echo "[OK] ⚙️ Applying failure-simulator CronJob..."
kubectl apply -f /home/vagrant/kube-resilience-lab/kubernetes/manifests/failure-simulator.yaml

# Wait for CronJob to exist before patching
until kubectl get cronjob failure-simulator &>/dev/null; do
  echo "[INFO] ⏳ Waiting for CronJob 'failure-simulator'..."
  sleep 3
done

if [ "$ENABLE_CHAOS_SIMULATOR" = "true" ]; then
  echo "[OK] 🔁 Enabling Chaos Simulator CronJob..."
  kubectl patch cronjob failure-simulator -p '{"spec" : {"suspend" : false }}'
else
  echo "⏸️ Disabling Chaos Simulator CronJob..."
  kubectl patch cronjob failure-simulator -p '{"spec" : {"suspend" : true }}'
fi

# ─────────────────────────────────────────────
echo "[OK] ✅ Setup complete!"
echo "[OK] 🧪 K8s Dashboard:  https://k8s-dashboard.kube-lab.local"
echo "[OK] 🔍 Prometheus:     http://prometheus.kube-lab.local"
echo "[OK] 📊 Grafana:        http://grafana.kube-lab.local"
echo "[OK] 🧾 To-Do App:      http://todo.kube-lab.local"
echo "[OK] 🐍 MicroFail App:  http://microfail.kube-lab.local"
echo "[OK] 🛠️ DevOps ToolBox: http://devops.kube-lab.local/"
echo "[OK] 🔑 K8s Dashboard Token:"
echo ""
echo "$STATIC_TOKEN"
echo ""
echo "📎 Add to /etc/hosts (macOS/Linux) or C:\\Windows\\System32\\drivers\\etc\\hosts (Windows):"
echo "$IP_ADDRESS k8s-dashboard.kube-lab.local prometheus.kube-lab.local grafana.kube-lab.local todo.kube-lab.local microfail.kube-lab.local"
echo ""
echo "To disable chaos: kubectl patch cronjob failure-simulator -p '{\"spec\" : {\"suspend\" : true }}'"
