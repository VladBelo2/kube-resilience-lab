import sys
import subprocess

# --- PyQt5 Auto-Installer ---
try:
    from PyQt5.QtWidgets import (
        QApplication, QWizard, QWizardPage, QLabel, QLineEdit, QVBoxLayout,
        QTextEdit, QPushButton, QMessageBox, QHBoxLayout
    )
    from PyQt5.QtCore import Qt, QProcess, QTimer
except ImportError:
    print("📦 PyQt5 not found. Attempting to install it...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt5"])
        print("✅ PyQt5 installed successfully. Restarting...")
        # Re-run the script after install
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        print(f"❌ Failed to install PyQt5: {e}")
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
        label = QLabel("This wizard will guide you through setting up the lab.")
        layout.addWidget(label)
        self.setLayout(layout)

    def initializePage(self):
        wizard = self.wizard()
        wizard.setOption(QWizard.HaveCustomButton1, True)
        wizard.setButtonText(QWizard.CustomButton1, "Cancel")
        wizard.button(QWizard.CustomButton1).clicked.connect(wizard.close)


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
        layout.addWidget(QLabel("Private IP:"))
        layout.addWidget(self.ip_input)
        layout.addWidget(self.warning)
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
                with open(env_conf_path, "r") as f:
                    lines = f.readlines()
            else:
                lines = []

            # Write back lines, updating IP_ADDRESS or appending it
            with open(env_conf_path, "w") as f:
                for line in lines:
                    if line.startswith("IP_ADDRESS="):
                        f.write(ip_line)
                        updated = True
                    else:
                        f.write(line)
                if not updated:
                    f.write(ip_line)

            # ✅ Update Vagrantfile
            with open("Vagrantfile", "r") as f:
                lines = f.readlines()
            with open("Vagrantfile", "w") as f:
                for line in lines:
                    if "config.vm.network" in line and "private_network" in line:
                        f.write(f'  config.vm.network "private_network", ip: "{ip}"\n')
                    else:
                        f.write(line)

            print(f"✅ Updated IP to {ip} in Vagrantfile and env.conf")
            return True

        except Exception as e:
            self.warning.setText(f"Failed to update Vagrantfile or env.conf: {str(e)}")
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
        self.log_output.append("🚀 Starting provisioning script...\n")

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
        self.log_output.append(output.strip())
        self.log_output.verticalScrollBar().setValue(
            self.log_output.verticalScrollBar().maximum()
        )

    def process_finished(self):
        wizard = self.wizard()
        self.log_output.append("\n✅ Provisioning complete.\n")

        # Enable navigation
        wizard.button(QWizard.NextButton).setEnabled(True)
        wizard.button(QWizard.BackButton).setEnabled(True)

        # Remove Cancel
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

        links = """
        <ul>
            <li><a href="https://k8s-dashboard.kube-lab.local">K8s Dashboard</a></li>
            <li><a href="http://prometheus.kube-lab.local">Prometheus</a></li>
            <li><a href="http://grafana.kube-lab.local">Grafana</a></li>
            <li><a href="http://flask.kube-lab.local">Flask App</a></li>
            <li><a href="http://todo.kube-lab.local">To-Do App</a></li>
        </ul>
        """
        label = QLabel(links)
        label.setOpenExternalLinks(True)

        layout = QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)

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
        self.addPage(ProgressPage())
        self.addPage(FinishPage())


def main():
    app = QApplication(sys.argv)
    wizard = KubeWizard()
    wizard.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
