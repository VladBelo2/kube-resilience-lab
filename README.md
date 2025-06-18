# 🚀 Kube Resilience Lab

## Descriptions

A fully automated, cross-platform Kubernetes resilience lab using **K3s**, provisioned via **Vagrant**, with **Helm**, **Prometheus**, **Grafana**, **NGINX Ingress**, and real-world microservices.  
Simulate failures, auto-detect and remediate them, and monitor the entire system with beautiful dashboards — all via a **single cross-platform installer**.

---

## 🎯 Purpose

Designed for:
- **Site Reliability Engineers (SRE)**
- **DevOps engineers**
- **Kubernetes learners**

to simulate, observe, and automatically remediate production-like failures — all observable through clean dashboards and metrics.

---

## 🌟 Features

| Feature                        | Description                                                                 |
|--------------------------------|-----------------------------------------------------------------------------|
| ✅ GUI Installer               | Cross-platform PyQt5 wizard automates everything (IP, Vagrantfile, setup)   |
| ⚙️ K3s Cluster                 | Lightweight K8s using [K3s](https://k3s.io)                                 |
| 🧠 Pod Health Checks           | Real-time post-provisioning readiness validation                            |
| 📊 Prometheus + Grafana        | Installed via Helm with dashboards provisioned from repo                    |
| 🛠️ DevOps Toolbox              | Web-based ping, traceroute, DNS, and package checks                         |
| 🔁 Remediator Controller       | Auto-restarts failed pods using Prometheus as a trigger                     |
| 💣 Failure Simulator           | CronJob deletes a random pod every 2 minutes                                |
| 🌐 Ingress Routing             | Custom `.kube-lab.local` domains with clean access                          |
| 📦 Real Apps                   | Flask-based To-Do App, MicroFail App (CPU/Disk/Fail tests), Remediator      |

---

## 📦 Apps & Components

| Name                | Type          | Description |
|---------------------|---------------|-------------|
| 🐍 **MicroFail**    | Flask App     | Simulates crashes, CPU burn, disk fill, emits Prometheus metrics. |
| ✅ **Remediator**   | Python Daemon | Auto-heals pods when `up == 0`, using Prometheus metrics. |
| ✅ **To-Do App**    | Flask App     | Full CRUD + Prometheus metrics (total, active, completed tasks). |
| 🛠 **DevOps Utils** | Flask App     | UI to run `ping`, `traceroute`, `dig`, and check installed packages. |

---

## 🖼️ Architecture Overview

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                             Kube Resilience Lab                          │
├────────────┬─────────────────────────────────────────────────────────────┤
│ Vagrant VM │  Ubuntu 22.04 + K3s                                         │
│            ├──────────────┬─────────────────────────────────────────────┤
│            │ Helm         │ Prometheus, Grafana, Ingress Controller      │
│            │ Python Apps  │ To-Do App, MicroFail, Remediator, DevOps UI │
│            │ CronJob      │ Failure Simulator                            │
└────────────┴──────────────┴─────────────────────────────────────────────┘
```

---

## 📋 Requirements

- [Vagrant](https://www.vagrantup.com/) (>= 2.2)
- [VirtualBox](https://www.virtualbox.org/) (>= 7.0)
- [Python 3.8+](https://www.python.org/downloads/)
- OS support:
  - ✅ macOS
  - ✅ Linux (Ubuntu/Debian/Fedora)
  - ✅ Windows 10+ (PyQt5 GUI supported)
- PyQt5 ⭕️ Auto	Automatically installed if missing

---

## 🚀 Quickstart

### 1. Clone the Repo


```bash
git clone https://github.com/vladbelo2/kube-resilience-lab.git
cd kube-resilience-lab
```

### 2. Launch the Wizard

```bash
python3 launch.py
```

- Prompts for VM IP address (e.g. 192.168.56.120)

- Automatically edits Vagrantfile + env.conf

- Launches full provisioning (vagrant up)

- Displays real-time status and health checks

### 3. Add Local DNS Mappings
Edit your /etc/hosts (Linux/macOS) or C:\Windows\System32\drivers\etc\hosts:

The IP you input from the Wizard 
```markdown
192.168.56.120  k8s-dashboard.kube-lab.local prometheus.kube-lab.local grafana.kube-lab.local microfail.kube-lab.local todo.kube-lab.local

```

## 🧪 Chaos Simulator

A Kubernetes CronJob randomly deletes a pod every 2 minutes.

To disable:
``` bash
kubectl patch cronjob failure-simulator -p '{"spec": {"suspend": true}}'
```

Or set this in env.conf:
``` bash
ENABLE_CHAOS_SIMULATOR=false

```

---

## 🧠 Pod Health Verification
During provisioning, the wizard:

- Waits up to 3 minutes for all pods to be Running

- Re-checks every 10s

- Displays ✅/⚠️ icons with status

- Helps detect stuck or failed containers right away

---

## 🌐 Access the Lab


| Service           | URL                                      |
| ----------------- | ---------------------------------------- |
| 🧪 K8s Dashboard  | https://k8s-dashboard.kube-lab.local     |
| 🔍 Prometheus     | http://prometheus.kube-lab.local         |
| 📊 Grafana        | http://grafana.kube-lab.local            |
| 💥 MicroFail App  | http://microfail.kube-lab.local          |
| 📝 To-Do App      | http://todo.kube-lab.local               |
| 🛠 DevOps Tools   | http://devops.kube-lab.local             |

---

## 🔐 Dashboard Access Token

After setup, use the wizard's "📂 View Token" or run manually:

```bash
kubectl -n kubernetes-dashboard get secret static-admin-user-token -o jsonpath="{.data.token}" | base64 --decode
```

---

## 📊 Grafana Dashboards

All dashboards are pre-loaded using ConfigMap + Helm provisioning.

| Dashboard	         | Panels Included   |
| ------------------ | ----------------- |
| 📈 MicroFail App   | Crash count, CPU usage, memory, restarts |
| 📝 To-Do App	     | Task count (active, total, deleted) |
| 🧪 Remediator	     | Prometheus checks, restarts, failures, per-job stats |
| 🧠 K8s Node Health | Default via kube-prometheus-stack |

Dashboards live under: “Kube Lab Dashboards” folder in Grafana.

---

## 🧠 Smart Health Checks

During provisioning, the wizard:

- Waits for all pods to become Running

- Re-checks every 10s, up to 3 minutes

- Shows ✅/⚠️ status for each pod

---

## 📁 Folder Structure
```text
kube-resilience-lab/
├── grafana/
│   ├── dashboards/
│   └── provisioning/
├── kubernetes/
│   ├── helm/
│   ├── ingress/
│   ├── manifests/
│   ├── monitoring/
│   └── k8s-dashboard/
├── python/
│   └── apps/
│       ├── microfail-app/
│       ├── todo-app/
│       ├── remediator/
│       └── devops-utils/
├── screenshots/
├── env.conf
├── launch.py
├── Vagrantfile
├── provision.sh
└── README.md
```

---

## 🧩 Project Architecture

```text
PyQt5 GUI
   ↓
Vagrant + Ubuntu
   ↓
K3s Kubernetes
   ↓
Helm installs:
   - kube-prometheus-stack
   - ingress-nginx
   ↓
K8s Deployments:
   - microfail, todo, remediator, utils
   ↓
Prometheus scrapes all apps via ServiceMonitors
Grafana auto-loads dashboards via ConfigMap

```

---

## 📸 Screenshots

| Wizard Setup | Ingress Routing | K8s Dashboard |
|--------------|-----------------|----------------|
| ![Wizard](screenshots/wizard.png) | ![Ingress](screenshots/ingress.png) | ![Pods](screenshots/dashboard-pods.png) |

| Grafana Dashboard | DevOps Toolbox | To-Do App |
|-------------------|----------------|-----------|
| ![Grafana](screenshots/grafana-dashboard.png) | ![DevOps](screenshots/DevOps-ToolBox.png) | ![Todo](screenshots/Todo-App.png) |

---

## 🧭 Roadmap

| Phase	       | Goal            | 
| ------------ | ----------------|
| ✅ Phase 1	  | Auto-provision Grafana dashboards via Helm values + ConfigMap
| 🔄 Phase 2   | Add GitHub Actions to validate provisioning + test service health
| 💣 Phase 3   | Add more chaos: CPU spike, disk fill, kill Ingress, DNS failures
| 🧠 Phase 4   | Integrate Ansible for OS-level remediation (e.g. clear disk)
| 🌍 Phase 5   | Publish as GitHub template + full documentation + screenshots

---

## 📄 License

MIT License

---

## 👨‍💻 Author

Built by **Vlad Belo** with ❤️ and 🤖 AI-powered wizardry.

---

> Found it useful? ⭐ Star this repo to support the project and help more DevOps learners discover it.
