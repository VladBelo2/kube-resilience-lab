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

.kube-resilience-lab/
├── .github/workflows/ # CI/CD workflows
├── ansible/ # Playbooks for remediation
├── python/ # Exporters and scripts
├── prometheus/ # Prometheus config & rules
├── grafana/ # Dashboard JSON files
├── kubernetes/ # YAML manifests
└── README.md # Project overview

