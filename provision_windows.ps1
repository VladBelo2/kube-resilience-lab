# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃    Kube Resilience Lab - Windows Provisioning   ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Write-Host "[OK] 🛠️  Starting Windows Provisioning..." -ForegroundColor Green

# Utility: Load config
$envConf = ".\env.conf"
if (-Not (Test-Path $envConf)) {
    Write-Host "[ERROR] env.conf not found!" -ForegroundColor Red
    exit 1
}
$envVars = Get-Content $envConf | Where-Object { $_ -match "=" } | ForEach-Object {
    $kv = $_ -split "=", 2
    @{ ($kv[0]) = $kv[1] }
} | ForEach-Object { $_ }

function IsEnabled($key) {
    return $envVars.ContainsKey($key) -and $envVars[$key].Trim().ToLower() -eq "true"
}

# Install Chocolatey if missing
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "[INFO] 🍫 Installing Chocolatey..." -ForegroundColor Cyan
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
}

# Function to install a package via choco if not already installed
function Ensure-ChocoPackage($name) {
    if (-not (choco list --local-only | Select-String -Pattern "^$name")) {
        Write-Host "[INFO] ➕ Installing $name..." -ForegroundColor Cyan
        choco install $name -y
    } else {
        Write-Host "[OK] ✅ $name already installed." -ForegroundColor Green
    }
}

# Install base tools
if (IsEnabled "INSTALL_DOCKER") {
    Ensure-ChocoPackage "docker-desktop"
}
if (IsEnabled "INSTALL_PYTHON") {
    Ensure-ChocoPackage "python"
}
if (IsEnabled "INSTALL_ANSIBLE") {
    Write-Host "[WARN] ⚠️  Ansible is not natively supported on Windows. Skipping..." -ForegroundColor Yellow
}
if (IsEnabled "INSTALL_KUBERNETES") {
    Ensure-ChocoPackage "k3d"
    Ensure-ChocoPackage "kubectl"
}

# Monitoring stack
if (IsEnabled "INSTALL_K8S_MONITORING") {
    Write-Host "[INFO] 📦 Deploying Prometheus & Grafana..." -ForegroundColor Cyan
    # Placeholder for deploying Docker Compose on Windows
    docker compose -f .\prometheus\docker-compose.yml up -d
}

# K8s Dashboard
if (IsEnabled "INSTALL_K8S_DASHBOARD") {
    Write-Host "[INFO] 🚀 Deploying Kubernetes Dashboard..." -ForegroundColor Cyan
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml
}

# Helm + Ingress
if (IsEnabled "INSTALL_HELM") {
    Ensure-ChocoPackage "helm"
}
if (IsEnabled "INSTALL_NGINX") {
    Write-Host "[INFO] 🌐 Installing NGINX Ingress..." -ForegroundColor Cyan
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.3/deploy/static/provider/cloud/deploy.yaml
}

# Ingress rules
if (IsEnabled "INSTALL_INGRESS_RULES") {
    Write-Host "[INFO] 🔁 Applying Ingress rules..." -ForegroundColor Cyan
    kubectl apply -f .\kubernetes\manifests\ingress.yaml
}

# Core Apps
if (IsEnabled "INSTALL_CORE_APPS") {
    Write-Host "[INFO] 🚀 Deploying Core Lab Apps..." -ForegroundColor Cyan
    kubectl apply -f .\kubernetes\manifests\
}

# Chaos Simulator
if (IsEnabled "ENABLE_CHAOS_SIMULATOR") {
    Write-Host "[INFO] ☢️ Deploying Chaos Simulator..." -ForegroundColor Cyan
    kubectl apply -f .\kubernetes\manifests\chaos-simulator.yaml
}

Write-Host "[OK] 🎉 Provisioning complete on Windows!" -ForegroundColor Green
