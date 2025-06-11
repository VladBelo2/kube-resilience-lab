# 🚀 Kube Resilience Lab

A self-contained Kubernetes resilience lab using K3s, provisioned via Vagrant, with Prometheus, Grafana, Ingress, and real-world apps. Fully automated with a cross-platform GUI wizard (launch.py) focused on simulating, observing, and auto-healing pod failures.


Designed for:
- Site Reliability Engineers (SRE)
- DevOps learners
- Kubernetes practitioners
- Chaos Engineering simulations
- Students and professionals

---

## 🌟 Features

- ✅ One-click cross-platform installer (macOS/Linux/Windows)
- ⚙️ K3s Kubernetes cluster with live monitoring
- 📊 Prometheus & Grafana dashboards auto-configured
- 🔄 Chaos simulator cronjob to simulate pod crashes
- 🔁 Remediator auto-heals broken deployments
- 🧪 Grafana dashboards with custom metrics
- 📦 Two Flask apps: 
  - `/metrics` generator
  - To-Do CRUD app with Prometheus integration
- 🌐 Ingress routing with custom `.kube-lab.local` domains
- 🛠️ Real-time pod health checks during install

---

## 📦 Current Apps

| App Name      | Description                              | URL                              |
|---------------|------------------------------------------|----------------------------------|
| MicroFail App | Basic `/metrics` endpoint                | http://microfail.kube-lab.local  |
| To-Do App     | CRUD + Prometheus metrics                | http://todo.kube-lab.local       |
| Remediator    | Self-healing controller using Prometheus | internal                         |

---

## 📋 Requirements

- [Vagrant](https://www.vagrantup.com/) (>= 2.2)
- [VirtualBox](https://www.virtualbox.org/) (>= 7.0)
- [Python 3.8+](https://www.python.org/downloads/)
- OS support:
  - ✅ macOS (w/ Homebrew + Zenity fallback)
  - ✅ Linux (Ubuntu, Debian, Fedora, Arch)
  - ✅ Windows 10+ (w/ PyQt5 or CLI fallback)

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

- Prompts for a private IP (e.g. 192.168.56.120)

- Edits Vagrantfile dynamically

- Runs full provisioning (vagrant up)

- Supports GUI wizard (PyQt5) with embedded terminal

### 3. Add Local DNS Mappings
Edit your /etc/hosts (Linux/macOS) or C:\Windows\System32\drivers\etc\hosts:

The IP you input from the Wizard 
```markdown
192.168.56.120  k8s-dashboard.kube-lab.local prometheus.kube-lab.local grafana.kube-lab.local microfail.kube-lab.local todo.kube-lab.local

```

## 🧪 Chaos Simulator

By default, a CronJob deletes one random pod every few minutes to simulate failure.
To pause this chaos:
``` bash
kubectl patch cronjob failure-simulator -p '{"spec": {"suspend": true}}'
```

Or set in env.conf:
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

## 🌐 Access URLs

Access the Lab:

| Service        | URL                                      |
| -------------- | ---------------------------------------- |
| K8s Dashboard  | https://k8s-dashboard.kube-lab.local     |
| Prometheus     | http://prometheus.kube-lab.local         |
| Grafana        | http://grafana.kube-lab.local            |
| MicroFail App  | http://microfail.kube-lab.local          |
| To-Do App      | http://todo.kube-lab.local               |

---

## 🔐 Dashboard Access Token

After setup, use the wizard's "📂 View Token" or run manually:

```bash
kubectl -n kubernetes-dashboard get secret static-admin-user-token -o jsonpath="{.data.token}" | base64 --decode
```

---

## 📸 Screenshots

> Add these to a `screenshots/` folder and update URLs once uploaded to GitHub.

| Wizard Setup | Ingress Routing |
| ------------ | ----------------|
| ![](screenshots/wizard.png) | ![](screenshots/urls.png) |

---

## 📁 Folder Structure
```text
kube-resilience-lab/
├── grafana/
│   ├── dashboards/
│   └── provisioning/
├── kubernetes/
│   ├── ingress/
│   ├── manifests/
│   └── k8s-dashboard/
├── prometheus/
│   └── prometheus.yml
├── python/

│   └── apps/
│       ├── todo-app/
│       ├── microfail-app/
│       └── remediator/
├── env.conf
├── launch.py
├── Vagrantfile
├── provision.sh
└── README.md
```
---

## 🚧 Roadmap / Next Features

🧱 Third App: Add a real DevOps-oriented Flask microservice

💥 Inject HTTP 500, CPU, memory, disk pressure

🔄 Extend remediator.py to detect new failure types

📈 Add more Grafana panels and alerts

🔔 Alertmanager Slack/Discord webhook integration

🤖 GitHub Actions to validate provisioning

🧹 Auto cleanup, reset, and snapshot commands

<!-- ## 📄 License

MIT License

--- -->

## 👨‍💻 Author

Built by **Vlad Belo** with ❤️ and 🤖 AI-powered wizardry.

---

> Found it useful? ⭐ Star the repo and share with fellow DevOps learners!
