import sys
import subprocess
import webbrowser
import time
import os


# --- PyQt5 Auto-Installer ---
try:
    from PyQt5.QtWidgets import (
        QApplication, QWizard, QWizardPage, QLabel, QLineEdit, QVBoxLayout,
        QTextEdit, QPushButton, QMessageBox, QHBoxLayout, QComboBox, QCheckBox
    )
    from PyQt5.QtCore import Qt, QProcess, QTimer
except ImportError:
    print("📦 PyQt5 not found. Attempting to install it...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt5"])
        print("\033[32m✅ PyQt5 installed successfully. Restarting...\033[0m")
        # Re-run the script after install
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        print(f"\033[31m❌ Failed to install PyQt5: {e}\033[0m")
        sys.exit(1)

# --- Main Logic Begins After Successful Import ---
import os
import re


class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to Kube Resilience Lab!")
        self.setSubTitle("This wizard will guide you through setting up the lab.")

        layout = QVBoxLayout()
        description = QLabel("""
            <p>
                <b>🚀 Kube Resilience Lab</b>
                <br><br>
                Kube Resilience Lab is a fully automated via <b>Vagrant</b>, 
                cross-platform Kubernetes simulation environment designed for learning, resilience testing, and self-healing practice. 
                It uses <b>K3s</b>, <b>Prometheus</b>, <b>Grafana</b>, <b>Ingress</b>, <b>Helm</b>, and real apps to simulate failures, 
                auto-detect them, and heal itself — all observable via dashboards and metrics.
            </p>
            <p>
                <br><br>
                Ideal for <i>learning, observability, chaos testing, and automation.</i>
            </p>
        """)
        description.setWordWrap(True)
        layout.addWidget(description)
        self.setLayout(layout)

    def initializePage(self):
        wizard = self.wizard()
        wizard.setButtonLayout([
            QWizard.BackButton,
            QWizard.NextButton,
            QWizard.CancelButton,
        ])
        # wizard.setOption(QWizard.HaveCustomButton1, True)
        # wizard.setButtonText(QWizard.CustomButton1, "Cancel")
        # wizard.button(QWizard.CustomButton1).clicked.connect(wizard.close)


class IPInputPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Enter Private IP")
        self.setSubTitle("Provide the private IP for the VM (e.g., 192.168.56.120).")

        self.ip_input = QLineEdit()
        self.registerField("privateIP*", self.ip_input)

        self.warning = QLabel("")
        self.warning.setStyleSheet("color: red")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("📡 Private IP:"))
        layout.addWidget(self.ip_input)
        description = QLabel("""
            <p>
                Enter the IP address that will be assigned to the virtual machine. <br>
                Example: <code>192.168.56.120</code><br><br>
                This will be used for Ingress, Hostname Mapping, and External Access.
            </p>
        """)
        description.setWordWrap(True)
        layout.addWidget(self.warning)
        layout.addWidget(description)
        self.setLayout(layout)

    def validatePage(self):
        ip = self.ip_input.text().strip()
        if not ip:
            self.warning.setText("IP address cannot be empty.")
            return False

        if not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip):
            self.warning.setText("Invalid IP format.")
            return False

        try:
            # ✅ Smart update of env.conf (preserve other lines)
            env_conf_path = "env.conf"
            ip_line = f"IP_ADDRESS={ip}\n"
            updated = False

            # Read existing lines if file exists
            if os.path.exists(env_conf_path):
                with open(env_conf_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            else:
                lines = []

            # Write back lines, updating IP_ADDRESS or appending it
            with open(env_conf_path, "w", encoding="utf-8") as f:
                for line in lines:
                    if line.startswith("IP_ADDRESS="):
                        f.write(ip_line)
                        updated = True
                    else:
                        f.write(line)
                if not updated:
                    f.write(ip_line)

            # ✅ Update Vagrantfile
            with open("Vagrantfile", "r", encoding="utf-8") as f:
                lines = f.readlines()
            with open("Vagrantfile", "w", encoding="utf-8") as f:
                for line in lines:
                    if "config.vm.network" in line and "private_network" in line:
                        f.write(f'  config.vm.network "private_network", ip: "{ip}"\n')
                    else:
                        f.write(line)

            print(f"\033[32m✅ Updated IP to {ip} in Vagrantfile and env.conf\033[0m")

            return True

        except Exception as e:
            self.warning.setText(f"Failed to update Vagrantfile or env.conf: {str(e)}")
            return False


class VMResourcesPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Configure VM Resources")
        self.setSubTitle("Choose the amount of CPU and Memory to allocate to the lab VM.")

        layout = QVBoxLayout()

        # Memory selection
        layout.addWidget(QLabel("🧠 Memory (MB):"))
        self.memory_combo = QComboBox()
        for label, val in [
            ("512 MB", 512), ("1 GB", 1024), ("2 GB", 2048), ("4 GB", 4096),
            ("6 GB", 6144), ("8 GB", 8192), ("12 GB", 12288), ("16 GB", 16384)
        ]:
            self.memory_combo.addItem(label, val)
        self.memory_combo.setCurrentText("8 GB")
        layout.addWidget(self.memory_combo)

        # CPU selection
        layout.addWidget(QLabel("🧮 CPU Cores:"))
        self.cpu_combo = QComboBox()
        for i in [1, 2, 4, 6, 8]:
            self.cpu_combo.addItem(f"{i} CPU", i)
        self.cpu_combo.setCurrentText("4 CPU")
        layout.addWidget(self.cpu_combo)

        self.setLayout(layout)

    def validatePage(self):
        # Save selected values to env.conf and patch Vagrantfile
        memory = self.memory_combo.currentData()
        cpus = self.cpu_combo.currentData()

        try:
            # Update env.conf
            with open("env.conf", "a", encoding="utf-8") as f:
                f.write(f"VM_MEMORY={memory}\n")
                f.write(f"VM_CPUS={cpus}\n")

            # Update Vagrantfile
            with open("Vagrantfile", "r", encoding="utf-8") as f:
                lines = f.readlines()
            with open("Vagrantfile", "w", encoding="utf-8") as f:
                for line in lines:
                    if "vb.memory" in line:
                        f.write(f'    vb.memory = {memory}\n')
                    elif "vb.cpus" in line:
                        f.write(f'    vb.cpus = {cpus}\n')
                    else:
                        f.write(line)

            print(f"\033[32m✅ Updated Vagrantfile with {memory}MB RAM and {cpus} CPUs\033[0m")
            return True

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update Vagrantfile: {e}")
            return False


class InstallOptionsPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Select Installation Options")
        self.setSubTitle("Enable or disable specific components before provisioning.")

        self.options = {
            "INSTALL_KUBERNETES": QCheckBox("Kubernetes (K3s)"),
            "INSTALL_DOCKER": QCheckBox("Docker & Compose"),
            "INSTALL_ANSIBLE": QCheckBox("Ansible"),
            "INSTALL_PYTHON": QCheckBox("Python 3.x"),
            "INSTALL_CORE_APPS": QCheckBox("Core Lab Apps"),
            "INSTALL_K8S_DASHBOARD": QCheckBox("K8s Dashboard"),
            "INSTALL_HELM": QCheckBox("Helm"),
            "INSTALL_NGINX": QCheckBox("NGINX Ingress Controller"),
            "INSTALL_K8S_MONITORING": QCheckBox("Prometheus & Grafana Monitoring Stack"),
            "INSTALL_INGRESS_RULES": QCheckBox("Ingress Routing Rules"),
            "ENABLE_CHAOS_SIMULATOR": QCheckBox("Chaos Simulator (optional)")
        }

        # Set defaults
        for key, checkbox in self.options.items():
            if key == "ENABLE_CHAOS_SIMULATOR":
                checkbox.setChecked(False)
            else:
                checkbox.setChecked(True)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("🔧 Select which components to install:"))
        for checkbox in self.options.values():
            layout.addWidget(checkbox)

        self.setLayout(layout)

        # Connect dependency logic
        self.options["INSTALL_KUBERNETES"].stateChanged.connect(self.sync_dependencies)

    def sync_dependencies(self):
        k8s_enabled = self.options["INSTALL_KUBERNETES"].isChecked()
        dependent_keys = [
            "INSTALL_K8S_DASHBOARD", "INSTALL_NGINX",
            "INSTALL_K8S_MONITORING", "INSTALL_INGRESS_RULES",
            "INSTALL_HELM", "INSTALL_CORE_APPS", "ENABLE_CHAOS_SIMULATOR"
        ]
        for key in dependent_keys:
            checkbox = self.options[key]
            checkbox.setEnabled(k8s_enabled)
            if not k8s_enabled:
                checkbox.setChecked(False)

    def validatePage(self):
        try:
            env_path = "env.conf"

            # Load existing config if it exists
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            else:
                lines = []

            # Build a dict of existing values
            config = {}
            for line in lines:
                if "=" in line:
                    key, val = line.strip().split("=", 1)
                    config[key] = val

            # ✅ Update selected install options
            for key, checkbox in self.options.items():
                config[key] = "true" if checkbox.isChecked() else "false"

            # Write cleaned-up config
            with open(env_path, "w", encoding="utf-8") as f:
                for key in sorted(config.keys()):
                    f.write(f"{key}={config[key]}\n")

            print("\033[32m✅ env.conf updated with install options\033[0m")
            return True

        except Exception as e:
            print(f"\033[31m❌ Failed to update env.conf: {e}\033[0m")
            return False


class ProgressPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Provisioning VM")
        self.setSubTitle("Please wait while the lab is being set up...")

        self.layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: black; color: white;")
        self.layout.addWidget(self.log_output)
        self.setLayout(self.layout)

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.readyReadStandardError.connect(self.handle_output)
        self.process.finished.connect(self.process_finished)

    def initializePage(self):
        self.log_output.clear()
        self.log_output.append('<span style="color:green;">🚀 Starting provisioning script...\n</span>')

        # Use QTimer to defer execution until after page is fully shown
        QTimer.singleShot(0, self.setup_and_start_provision)

    def setup_and_start_provision(self):
        wizard = self.wizard()

        # Disable < Back and Next > buttons
        wizard.setButtonLayout([
            QWizard.Stretch,
            QWizard.CustomButton1,
            QWizard.BackButton,
            QWizard.NextButton
        ])
        wizard.button(QWizard.NextButton).setEnabled(False)
        wizard.button(QWizard.BackButton).setEnabled(False)

        # Add Cancel button
        wizard.setOption(QWizard.HaveCustomButton1, True)
        wizard.setButtonText(QWizard.CustomButton1, "Cancel")
        wizard.button(QWizard.CustomButton1).clicked.connect(self.cancel_setup)

        # Start provisioning process
        project_root = os.path.dirname(os.path.abspath(__file__))
        self.process.setWorkingDirectory(project_root)
        self.process.start("vagrant", ["up"])

    def handle_output(self):
        data = self.process.readAllStandardOutput().data().decode()
        err = self.process.readAllStandardError().data().decode()
        output = data + err

        for line in output.strip().splitlines():
            if "[OK]" in line:
                self.log_output.append(f'<span style="color:green;">{line}</span>')
            elif "[WARN]" in line:
                self.log_output.append(f'<span style="color:orange;">{line}</span>')
            elif "[ERROR]" in line:
                self.log_output.append(f'<span style="color:red;">{line}</span>')
            elif "[INFO]" in line:
                self.log_output.append(f'<span style="color:cyan;">{line}</span>')
            else:
                self.log_output.append(line)

        # self.log_output.append(output.strip())
        self.log_output.verticalScrollBar().setValue(
            self.log_output.verticalScrollBar().maximum()
        )

    def process_finished(self):
        wizard = self.wizard()
        if self.process.exitCode() == 0:
            self.log_output.append('<span style="color:green;">\n✅ Provisioning complete.\n</span>')
        else:
            self.log_output.append('<span style="color:orange;">\n ⚠ Provisioning finished with errors.\n</span>')
            self.log_output.append('<span style="color:orange;">🔍 Please scroll up and review any red or failed lines.n</span>')
            self.log_output.append('<span style="color: red;">❌ Provisioning had errors. See above for details.</span>')

        # 🧪 Get K8s Dashboard Token and save it to file
        try:
            token = subprocess.check_output(
                ["vagrant", "ssh", "-c", "kubectl -n kubernetes-dashboard get secret static-admin-user-token -o jsonpath='{.data.token}' | base64 --decode"],
                universal_newlines=True
            )
            with open("dashboard_token.txt", "w") as f:
                f.write(token.strip())
            print("\033[32m✅ Saved K8s Dashboard token to dashboard_token.txt\033[0m")
        except Exception as e:
            print(f"\033[31m❌ Failed to get dashboard token: {e}.\033[0m")

        # ✅ Check pod health before finishing
        self.log_output.append("\n🔍 Checking pod health (timeout: 3 minutes)...\n")
        QApplication.processEvents()
        try:
            start_time = time.time()
            unhealthy = {}

            while time.time() - start_time < 180:  # 3 minutes
                result = subprocess.run(
                    ["vagrant", "ssh", "-c", "kubectl get pods --no-headers"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                lines = result.stdout.strip().splitlines()
                all_healthy = True
                unhealthy.clear()

                for line in lines:
                    parts = line.split()
                    pod_name = parts[0]
                    status = parts[2] if len(parts) > 2 else "Unknown"
                    if status not in ("Running", "Completed"):
                        unhealthy[pod_name] = status
                        all_healthy = False
                        self.log_output.append(f'<span style="color:orange;">⚠ {pod_name}: {status}</span>')
                        QApplication.processEvents()
                    else:
                        self.log_output.append(f'<span style="color:green;">✅ {pod_name}: {status}</span>')
                        QApplication.processEvents()
                    
                if all_healthy:
                    self.log_output.append('<span style="color:green;"> \n ✅ All pods are healthy! \n </span>')
                    QApplication.processEvents()
                    break
                else:
                    self.log_output.append("⏳ Waiting 10s before rechecking...\n")
                    QApplication.processEvents()
                    time.sleep(10)

            if unhealthy:
                self.log_output.append("\n⏰ Timeout reached. These pods are not healthy:\n")
                QApplication.processEvents()
                for pod, status in unhealthy.items():
                    self.log_output.append(f"❌ {pod}: {status}")
                    QApplication.processEvents()
            else:
                self.log_output.append('<span style="color:green;"> \n✅ Pod readiness check passed.\n </span>')
                QApplication.processEvents()

        except Exception as e:
            self.log_output.append(f'<span style="color:red;">❌ Pod health check error: {e}</span>')
            QApplication.processEvents()

        # Enable navigation
        wizard.button(QWizard.NextButton).setEnabled(True)
        wizard.button(QWizard.BackButton).setEnabled(True)

        # Remove Cancel button
        wizard.setOption(QWizard.HaveCustomButton1, False)

    def cancel_setup(self):
        if self.process and self.process.state() == QProcess.Running:
            self.process.kill()
            self.process.waitForFinished()
        self.wizard().close()


class FinishPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Setup Complete!")
        self.setSubTitle("Everything is ready! Click the links below to visit services:")
        self.token_path = os.path.abspath("dashboard_token.txt")
        layout = QVBoxLayout()

        layout.addWidget(QLabel("🌐 Access the Lab"))

        links = QLabel("""
            <ul>
                <li><a href="https://k8s-dashboard.kube-lab.local">K8s Dashboard</a></li>
                <li><a href="http://prometheus.kube-lab.local/targets">Prometheus</a></li>
                <li><a href="http://grafana.kube-lab.local">Grafana</a></li>
                <li><a href="http://devops.kube-lab.local">DevOps Utils App</a></li> 
                <li><a href="http://todo.kube-lab.local">To-Do App</a></li>
                <li><a href="http://microfail.kube-lab.local">MicroFail App</a></li>
            </ul>
        """)
        links.setOpenExternalLinks(True)
        layout.addWidget(links)

        # View Token section (handled separately)
        self.token_label = QLabel("🔑 <b>K8s-Dashboard Token</b> (one-time):<br>")
        self.token_link = QLabel('<a href="#">📂 View Token</a>')
        self.token_link.setOpenExternalLinks(False)
        self.token_link.linkActivated.connect(self.open_token_file)

        layout.addWidget(self.token_label)
        layout.addWidget(self.token_link)
        self.setLayout(layout)
        
    def open_token_file(self):
        token_path = os.path.abspath("dashboard_token.txt")
        if os.path.exists(token_path):
            webbrowser.open(f"file://{token_path}")
        else:
            QMessageBox.warning(self, "Error", "Token file not found!")

    def cleanup_token(self):
        if os.path.exists(self.token_path):
            try:
                os.remove(self.token_path)
                print("\033[32m🧹 Token file deleted after finish.\033[0m")
            except Exception as e:
                print(f"\033[33m⚠ Failed to delete token file: {e}\033[0m")

    def initializePage(self):
        wizard = self.wizard()

        # Add Finish button as CustomButton1
        wizard.setOption(QWizard.HaveCustomButton1, True)
        wizard.setButtonText(QWizard.CustomButton1, "Finish")
        wizard.button(QWizard.CustomButton1).clicked.connect(wizard.close)

        # Move Back button left, Finish button right (default layout)
        wizard.setButtonLayout([
            QWizard.BackButton,
            QWizard.Stretch,
            QWizard.CustomButton1,  # Your Finish button
        ])


class KubeWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kube Resilience Lab Setup")
        self.setWizardStyle(QWizard.ModernStyle)

        self.addPage(WelcomePage())
        self.addPage(IPInputPage())
        self.addPage(VMResourcesPage())
        self.addPage(InstallOptionsPage())
        self.addPage(ProgressPage())
        self.addPage(FinishPage())
        self.resize(640, 480)

def main():
    app = QApplication(sys.argv)
    wizard = KubeWizard()

    # Connect Finish click to token cleanup
    for i in range(wizard.pageIds().__len__()):
        page = wizard.page(i)
        if isinstance(page, FinishPage):
            wizard.finished.connect(page.cleanup_token)
            break

    wizard.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
