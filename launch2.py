#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
from shutil import which


def is_command_available(cmd):
    return which(cmd) is not None


def install_homebrew():
    print("🔧 Installing Homebrew...")
    brew_cmd = ("/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
    subprocess.run(brew_cmd, shell=True, check=True)


def install_zenity_mac():
    if not is_command_available("brew"):
        install_homebrew()
    print("🔧 Installing Zenity via Homebrew...")
    subprocess.run(["brew", "install", "zenity"], check=True)


def zenity_info(msg):
    subprocess.run(["zenity", "--info", "--width=400", "--text", msg])


def zenity_welcome():
    result = subprocess.run([
        "zenity", "--question",
        "--width=250",
        "--title=Welcome",
        "--text=\U0001F44B  Welcome to: Kube Resilience Lab!\n\nClick Yes to begin setup.\""
    ])
    if result.returncode != 0:
        print("❌ User cancelled setup.")
        sys.exit(0)


def get_ip_with_zenity():
    while True:
        result = subprocess.run([
            "zenity", "--forms",
            "--title=\"Kube Lab Setup\"",
            "--text=\"Enter private IP (e.g. 192.168.56.120):\"",
            "--add-entry=IP Address",
            "--width=400",
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print("❌ Cancelled by user.")
            sys.exit(0)

        ip = result.stdout.strip()
        if ip:
            return ip
        else:
            subprocess.run([
                "zenity", "--error", "--width=200",
                "--text=\"IP address cannot be empty!\""
            ])


def update_vagrantfile(ip):
    updated = False
    with open("Vagrantfile", "r") as vf:
        lines = vf.readlines()

    with open("Vagrantfile", "w") as vf:
        for line in lines:
            if "config.vm.network" in line and "private_network" in line:
                vf.write(f'  config.vm.network "private_network", ip: "{ip}"')
                updated = True
            else:
                vf.write(line)

    if not updated:
        with open("Vagrantfile", "a") as vf:
            vf.write(f'  config.vm.network "private_network", ip: "{ip}"')

    print(f"✅ Vagrantfile updated with IP: {ip}")


def run_vagrant_up():
    print("🚀 Starting Vagrant VM...")
    subprocess.run(["vagrant", "up"])


def final_message():
    msg = (
        "\U0001F389 Setup complete!\n\n"
        "You can visit:\n\n"
        "\U0001F539 Kubernetes Dashboard:\nhttps://k8s-dashboard.kube-lab.local\n\n"
        "\U0001F539 Monitoring:\nhttp://prometheus.kube-lab.local\nhttp://grafana.kube-lab.local\n\n"
        "\U0001F539 Apps:\nhttp://flask.kube-lab.local\nhttp://todo.kube-lab.local"
    )
    subprocess.run(["zenity", "--info", "--width=450", "--height=400", "--text", msg])


def main():
    system = platform.system()

    if system == "Darwin":
        if not is_command_available("zenity"):
            install_zenity_mac()
        zenity_welcome()
        ip = get_ip_with_zenity()
    elif system == "Linux":
        if not is_command_available("zenity"):
            print("Please install Zenity: sudo apt install zenity")
            sys.exit(1)
        zenity_welcome()
        ip = get_ip_with_zenity()
    else:
        print("❌ Unsupported platform for GUI installer.")
        sys.exit(1)

    update_vagrantfile(ip)
    run_vagrant_up()
    final_message()


if __name__ == "__main__":
    main()
