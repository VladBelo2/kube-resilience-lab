# 🚀 Kube Resilience Lab

A self-contained Kubernetes resilience lab using K3s, provisioned via Vagrant, with Prometheus, Grafana, Ingress, and real-world apps. Fully automated with a GUI wizard (launch.py), focused on simulating and observing failures.


Designed for:
- Site Reliability Engineers (SRE)
- DevOps learners
- Kubernetes practitioners
- Chaos Engineering simulations
- Students and professionals

---

## 🌟 Features

- ✅ One-click cross-platform installer (macOS/Linux/Windows)
- ⚙️ K3s Kubernetes cluster with monitoring stack
- 📊 Prometheus & Grafana dashboards auto-configured
- 📦 Two Flask apps: 
  - `/metrics` generator
  - To-Do CRUD app with Prometheus integration
- 🌐 Ingress routing with custom `.kube-lab.local` domains
- 🔁 Self-healing pod behavior simulations

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

### 3. Update Hosts File
Add this to /etc/hosts (Linux/macOS) or C:\Windows\System32\drivers\etc\hosts (Windows):

The IP you input from the Wizard 
(e.g. 192.168.56.120) flask.kube-lab.local todo.kube-lab.local prometheus.kube-lab.local grafana.kube-lab.local k8s-dashboard.kube-lab.local


---

## ✅ STEP 3: Access URLs

```markdown
---

## 🌐 Access the Lab

| Service       | URL                                      |
| ------------- | ---------------------------------------- |
| K8s Dashboard | http://k8s-dashboard.kube-lab.local      |
| Prometheus    | http://prometheus.kube-lab.local         |
| Grafana       | http://grafana.kube-lab.local            |
| Flask App     | http://flask.kube-lab.local              |
| To-Do App     | http://todo.kube-lab.local               |
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
│   └── dashboards/
│       ├── flask_metrics.json
│       └── flask_metrics.json
│   └── provisioning/
│       └── dashboards/
│           └── flask_dashboard.yml
│       └── datasources/
│           └── prometheus.yml
├── kubernetes/
│   └── ingress/
│       ├── ingress-flask.yaml
│       ├── ingress-grafana.yaml
│       ├── ingress-k8s-dashboard.yaml
│       ├── ingress-prometheus.yaml
│       └── ingress-todo.yaml
│   └── k8s-dashboard/
│       └── admin-user.yaml
│   └── manifests/
│       ├── flask-app.yml
│       ├── grafana-deployment.yaml
│       ├── grafana-service.yaml
│       ├── prometheus-config.yaml
│       ├── prometheus-deployment.yaml
│       ├── prometheus-service.yaml
│       ├── todo-app-deployment.yaml
│       └── todo-app-service.yaml
├── prometheus/
│   └── prometheus.yml
├── python/
│   └── flask-metrics-app/
│       ├── app.py
│       ├── Dockerfile
│       └── requirements.txt
│   └── flask-todo-app/
│       ├── app.py
│       ├── Dockerfile
│       ├── requirements.txt
│       └── templates/
│           └── index.html
├── .gitignore
├── env.conf
├── Vagrantfile
├── provision.sh
├── launch.py
└── README.md
```
---

## ✅ STEP 4: Optional CI + Next Features + License

```markdown
---

## 🧪 Coming Soon

- 🔁 Chaos Toolkit Integration
- 📦 More Flask services (auth, DB integration)
- 📊 Push metrics to InfluxDB
- 🔄 GitHub Actions CI for `vagrant up` validation

---
```
<!-- ## 📄 License

MIT License

--- -->

## 👨‍💻 Author

Built by **Vlad Belo** with 🤖 AI-powered assistance

---

> Found it useful? ⭐ Star the repo and share with fellow DevOps learners!

