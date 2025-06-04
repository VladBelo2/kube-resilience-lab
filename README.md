# 🧪 KubeResilience Lab

A self-healing Kubernetes lab that simulates real-world failures and automatically remediates them using Ansible, Python, and GitHub Actions — all monitored via Prometheus and Grafana.

## 🚀 Features

- Pod crash simulation and auto-recovery
- CPU/disk/network failure injection
- Prometheus metrics for detection
- Grafana dashboards for observability
- Ansible playbooks for remediation
- GitHub Actions CI/CD and Chaos pipelines

## 📁 Project Structure

```text
kube-resilience-lab/
├── .github/workflows/       # GitHub Actions CI/CD pipelines
├── ansible/                 # Remediation playbooks
├── python/
│   └── custom_exporters/    # Prometheus exporters and utility scripts
├── prometheus/
│   └── rules/               # Alerting and recording rules
├── grafana/
│   └── dashboards/          # Dashboard JSON configs
├── kubernetes/
│   └── manifests/           # K8s deployment files
└── README.md                # Project documentation

