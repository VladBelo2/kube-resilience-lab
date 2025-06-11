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
```markdown
(e.g. 192.168.56.120) flask.kube-lab.local todo.kube-lab.local prometheus.kube-lab.local grafana.kube-lab.local k8s-dashboard.kube-lab.local
```

### Extra Tip:
By default, there is an active Cronjob for failure-simulate to randomally delete pod and recreate it immediately.
To stop the cronjob for failure-simulator run the following inside the VM:
```bash
kubectl patch cronjob failure-simulator -p '{"spec" : {"suspend" : true }}
```

Or you can set the env.conf variable ENABLE_CHAOS_SIMULATOR=false and run the provision.sh again.

---

## 🌐 Access URLs

Access the Lab:

| Service       | URL                                      |
| ------------- | ---------------------------------------- |
| K8s Dashboard | https://k8s-dashboard.kube-lab.local     |
| Prometheus    | http://prometheus.kube-lab.local         |
| Grafana       | http://grafana.kube-lab.local            |
| Flask App     | http://flask.kube-lab.local              |
| To-Do App     | http://todo.kube-lab.local               |

---

## 🔑 Accessing Kubernetes Dashboard

Run this command inside the VM to get your login token:

```bash
kubectl -n kubernetes-dashboard get secret static-admin-user-token -o jsonpath="{.data.token}" | base64 --decode
```

📝 Or use the installer wizard and click 📂 View Token after setup.

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
│       ├── dashboards/
│       └── datasources/
├── kubernetes/
│   ├── ingress/
│   ├── k8s-dashboard/
│   └── manifests/
├── prometheus/
├── python/
│   ├── flask-metrics-app/
│   └── flask-todo-app/
├── .gitignore
├── env.conf
├── Vagrantfile
├── provision.sh
├── launch.py
└── README.md
```
---

## Optional CI + Next Features

```markdown
 🧪 Coming Soon

- 🔁 Chaos Toolkit Integration
- 📦 More Flask services (auth, DB integration)
- 📊 Push metrics to InfluxDB
- 🔄 GitHub Actions CI for `vagrant up` validation
```

<!-- ## 📄 License

MIT License

--- -->

## 👨‍💻 Author

Built by **Vlad Belo** with 🤖 AI-powered assistance

---

> Found it useful? ⭐ Star the repo and share with fellow DevOps learners!

test PR