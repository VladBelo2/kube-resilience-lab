import sys
import subprocess
import webbrowser
import time
import os
import platform
import json
from validate_env import validate_env


# --- PyQt5 Auto-Installer ---
try:
    from PyQt5.QtWidgets import (
        QApplication, QWizard, QWizardPage, QLabel, QLineEdit, QVBoxLayout,
        QTextEdit, QPushButton, QMessageBox, QHBoxLayout, QComboBox, QCheckBox, QSizePolicy
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


# Check if running on Windows or macOS/Linux
IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    print("🪟 Detected Windows host.")
else:
    print("🐧 Detected macOS/Linux host.")

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
            QWizard.Stretch,
            QWizard.BackButton,
            QWizard.NextButton,
            QWizard.CancelButton,
        ])


class IPInputPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Enter Private IP")
        self.setSubTitle("Provide the private IP for the VM (e.g., 192.168.56.120).")
        self.has_validated = False

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
        if self.wizard().provisioning_finished:
            return True
        
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
            self.has_validated = True
            return True

        except Exception as e:
            self.warning.setText(f"Failed to update Vagrantfile or env.conf: {str(e)}")
            return False


class VMResourcesPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Configure VM Resources")
        self.setSubTitle("Choose the amount of CPU and Memory to allocate to the lab VM.")
        self.has_validated = False

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
        if self.wizard().provisioning_finished:
            return True

        memory = self.memory_combo.currentData()
        cpus = self.cpu_combo.currentData()

        try:
            env_conf_path = "env.conf"
            config = {}

            # Load existing env.conf (if exists)
            if os.path.exists(env_conf_path):
                with open(env_conf_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line:
                            key, val = line.strip().split("=", 1)
                            config[key] = val

            # ✅ Update values
            config["VM_MEMORY"] = str(memory)
            config["VM_CPUS"] = str(cpus)

            # Write clean config back
            with open(env_conf_path, "w", encoding="utf-8") as f:
                for key in sorted(config.keys()):
                    f.write(f"{key}={config[key]}\n")

            # ✅ Update Vagrantfile
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

            print(f"\033[32m✅ Updated Vagrantfile with {memory}[MB] RAM and {cpus} CPUs\033[0m")
            self.has_validated = True
            return True

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update Vagrantfile: {e}")
            return False


class InstallOptionsPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Select Installation Options")
        self.setSubTitle("Enable or disable specific components before provisioning.")
        self.has_validated = False
        self.options = {}
        self.features = []

        # Load features from JSON
        try:
            with open("features.json", "r", encoding="utf-8") as f:
                features = json.load(f)

            # Validate structure
            seen_keys = set()
            for i, feat in enumerate(features):
                if "key" not in feat or "label" not in feat:
                    raise ValueError(f"Feature at index {i} is missing 'key' or 'label'")
                if feat["key"] in seen_keys:
                    raise ValueError(f"Duplicate key detected: {feat['key']}")
                seen_keys.add(feat["key"])

                # Optionally, validate types
                if not isinstance(feat["key"], str) or not isinstance(feat["label"], str):
                    raise ValueError(f"Feature at index {i} has invalid types")
                if "default" in feat and not isinstance(feat["default"], bool):
                    raise ValueError(f"'default' must be a boolean in feature {feat['key']}")
                if "depends_on" in feat and not isinstance(feat["depends_on"], list):
                    raise ValueError(f"'depends_on' must be a list in feature {feat['key']}")

            self.features = features

        except Exception as e:
            QMessageBox.critical(self, "features.json Error", f"⚠️ features.json is invalid:\n\n{str(e)}")
            sys.exit(1)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("🔧 Select which components to install:"))

        for feature in self.features:
            key = feature["key"]
            label = feature["label"]
            default = feature.get("default", True)

            checkbox = QCheckBox(label)
            checkbox.setChecked(default)
            self.options[key] = checkbox
            layout.addWidget(checkbox)

        self.setLayout(layout)

        # Dependency logic
        for feature in self.features:
            if "depends_on" in feature:
                for parent_key in feature["depends_on"]:
                    self.options[parent_key].stateChanged.connect(self.sync_dependencies)

        self.sync_dependencies()

    def sync_dependencies(self):
        config = {k: cb.isChecked() for k, cb in self.options.items()}
        for feature in self.features:
            key = feature["key"]
            depends_on = feature.get("depends_on", [])
            checkbox = self.options[key]

            enabled = all(config.get(dep, False) for dep in depends_on)
            checkbox.setEnabled(enabled)
            if not enabled:
                checkbox.setChecked(False)

    def validatePage(self):
        if self.wizard().provisioning_finished:
            return True

        # 🔍 Run env validation before saving install options
        result = validate_env()
        if result["status"] == "error":
            QMessageBox.critical(self, "Validation Error", result["message"])
            return False

        real_extras = result["real_extras"]
        missing = result["missing"]

        print(f"\033[36m[Validation] 🔍 safe_extras: {result['safe_extras']}\033[0m")
        print(f"\033[36m[Validation] 🔍 real_extras: {real_extras}\033[0m")
        print(f"\033[36m[Validation] 🔍 missing: {missing}\033[0m")

        if real_extras or missing:
            msg = "🚨 <b>Mismatch detected between <code>features.json</code> and <code>env.conf</code></b><br><br>"
            if real_extras:
                msg += f"<b>Unexpected keys:</b> {', '.join(real_extras)}<br>"
            if missing:
                msg += f"<b>Missing keys:</b> {', '.join(missing)}<br>"
            msg += "<br>Would you like to fix this?"

            dialog = QMessageBox(self)
            dialog.setWindowTitle("Validate env.conf")
            dialog.setTextFormat(Qt.RichText)
            dialog.setIcon(QMessageBox.Warning)
            dialog.setText(msg)
            dialog.addButton("Fix Now", QMessageBox.AcceptRole)
            dialog.addButton("Continue Anyway", QMessageBox.DestructiveRole)
            dialog.addButton("Cancel", QMessageBox.RejectRole)
            choice = dialog.exec()

            if choice == 0:  # Fix Now
                try:
                    # Load features.json again for defaults
                    with open("features.json", "r", encoding="utf-8") as f:
                        features = json.load(f)
                    defaults = {f["key"]: str(f.get("default", "false")).lower() for f in features}

                    # Load current env.conf
                    env_path = "env.conf"
                    config = {}
                    if os.path.exists(env_path):
                        with open(env_path, "r", encoding="utf-8") as f:
                            for line in f:
                                if "=" in line:
                                    key, val = line.strip().split("=", 1)
                                    config[key] = val

                    # Add missing keys using defaults
                    for key in missing:
                        config[key] = defaults.get(key, "false")
                        print(f"\033[32m[FIXED] Added missing key: {key}={config[key]}\033[0m")

                    # Write updated env.conf
                    with open(env_path, "w", encoding="utf-8") as f:
                        for key in sorted(config.keys()):
                            f.write(f"{key}={config[key]}\n")

                    QMessageBox.information(self, "Fix Complete", "✅ Missing keys were added to env.conf automatically.")
                except Exception as e:
                    QMessageBox.critical(self, "Fix Failed", f"❌ Could not fix env.conf:\n\n{e}")
                    return False

            elif choice == 1:  # Continue Anyway
                pass
            elif choice == 2:  # Cancel
                return False

        # ✅ Save install options to env.conf
        try:
            env_conf_path = "env.conf"
            config = {}

            if os.path.exists(env_conf_path):
                with open(env_conf_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line:
                            key, val = line.strip().split("=", 1)
                            config[key] = val

            for key, checkbox in self.options.items():
                config[key] = "true" if checkbox.isChecked() else "false"

            with open(env_conf_path, "w", encoding="utf-8") as f:
                for key in sorted(config.keys()):
                    f.write(f"{key}={config[key]}\n")

            print("\033[32m✅ env.conf updated with install options\033[0m")
            self.has_validated = True
            return True

        except Exception as e:
            print(f"\033[31m❌ Failed to update env.conf: {e}\033[0m")
            return False


class ProgressPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Provisioning VM")
        self.setSubTitle("Please wait while the lab is being set up...")
        self.provisioning_started = False

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
        if self.provisioning_started:
            return # Don't run provisioning again
        
        self.provisioning_started = True
        self.log_output.clear()
        self.log_output.append('<span style="color:green;">🚀 Starting provisioning script...\n</span>')

        wizard = self.wizard()

        # 🛑 Disable navigation
        wizard.button(QWizard.BackButton).setEnabled(False)
        wizard.button(QWizard.NextButton).setEnabled(False)

        # ✅ Ensure Cancel stays enabled
        wizard.button(QWizard.CancelButton).setEnabled(True)

        # Start provisioning after UI is ready
        QTimer.singleShot(0, self.setup_and_start_provision)

    def setup_and_start_provision(self):
        # Start provisioning process
        project_root = os.path.dirname(os.path.abspath(__file__))
        self.process.setWorkingDirectory(project_root)
        self.process.start("vagrant", ["up"])

        wizard = self.wizard()
        wizard.button(QWizard.BackButton).setEnabled(False)
        wizard.button(QWizard.NextButton).setEnabled(False)

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
        self.wizard().provisioning_finished = True

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

        # Enable Back always
        wizard.button(QWizard.BackButton).setEnabled(True)

        # ✅ Only enable Next if provisioning succeeded
        if self.process.exitCode() == 0:
            wizard.button(QWizard.NextButton).setEnabled(True)
        else:
            wizard.button(QWizard.NextButton).setEnabled(False)

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
        self.token_link = QLabel('<a href="#">📂 View Token</a><br>')
        self.token_link.setOpenExternalLinks(False)
        self.token_link.linkActivated.connect(self.open_token_file)

        layout.addWidget(self.token_label)
        layout.addWidget(self.token_link)

        # 📌 Button to update hosts file
        self.update_hosts_btn = QPushButton("📌 Update hosts file for routing")
        self.update_hosts_btn.clicked.connect(self.run_update_hosts_script)
        self.update_hosts_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.update_hosts_btn)

        self.setLayout(layout)
        
    def open_token_file(self):
        token_path = os.path.abspath("dashboard_token.txt")
        if os.path.exists(token_path):
            webbrowser.open(f"file://{token_path}")
        else:
            QMessageBox.warning(self, "Error", "Token file not found!")

    def run_update_hosts_script(self):
        update_script = os.path.abspath("python/update_hosts.py")

        if not os.path.exists(update_script):
            QMessageBox.warning(self, "Missing Script", "❌ update_hosts.py not found in current directory.")
            return

        system = platform.system()

        if system == "Windows":
            # Run in new admin cmd window
            try:
                subprocess.run([
                    "powershell", "-Command",
                    f'Start-Process cmd -ArgumentList \'/k python "{update_script}"\' -Verb runAs'
                ])
            except Exception as e:
                QMessageBox.critical(self, "Error", f"❌ Could not launch update_hosts.py as admin:\n{e}")
                
        elif system == "Darwin":
            # macOS: run in Terminal with sudo and a message
            try:
                subprocess.Popen([
                    "osascript", "-e",
                    f'''
                    tell application "Terminal"
                        activate
                        do script "cd \\"{os.getcwd()}\\"; clear; echo '🔐 Enter sudo password to update hosts file:'; sudo python3 \\"{update_script}\\""
                    end tell
                    '''
                ])
            except Exception as e:
                QMessageBox.critical(self, "Error", f"❌ Could not launch Terminal:\n{e}")

        else:
            # Linux: attempt to run in terminal with sudo
            try:
                subprocess.Popen([
                    "x-terminal-emulator", "-e",
                    f'sudo python3 "{update_script}"'
                ])
            except FileNotFoundError:
                # Fallback if x-terminal-emulator not found
                try:
                    subprocess.Popen([
                        "gnome-terminal", "--", "bash", "-c",
                        f'sudo python3 "{update_script}"; exec bash'
                    ])
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"❌ Could not launch update_hosts.py:\n{e}")

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
            QWizard.Stretch,
            QWizard.BackButton,
            QWizard.CustomButton1,  # Your Finish button
        ])


class KubeWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kube Resilience Lab Setup")
        self.setWizardStyle(QWizard.ModernStyle)
        self.provisioning_finished = False

        self.setButtonLayout([
            QWizard.BackButton,
            QWizard.NextButton,
            QWizard.Stretch,
            QWizard.CancelButton
        ])

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
