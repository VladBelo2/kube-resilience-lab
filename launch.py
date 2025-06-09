import sys
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWizard, QWizardPage, QLabel, QLineEdit, QVBoxLayout,
    QTextEdit, QPushButton, QMessageBox, QHBoxLayout
)
from PyQt5.QtCore import Qt, QProcess, QTimer
import re
import os

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
            self.error_label.setText("IP address cannot be empty.")
            return False

        # Basic IP format check (you can extend this)
        if not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip):
            self.error_label.setText("Invalid IP format.")
            return False

        # Modify Vagrantfile
        try:
            with open("Vagrantfile", "r") as f:
                lines = f.readlines()
            with open("Vagrantfile", "w") as f:
                for line in lines:
                    if "config.vm.network" in line and "private_network" in line:
                        f.write(f'  config.vm.network "private_network", ip: "{ip}"\n')
                    else:
                        f.write(line)
            print(f"✅ Updated Vagrantfile with IP: {ip}")
            return True
        except Exception as e:
            self.error_label.setText(f"Failed to update Vagrantfile: {str(e)}")
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
            <li><a href="http://k8s-dashboard.kube-lab.local">K8s Dashboard</a></li>
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
