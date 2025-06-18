import os
import platform
import sys
import ctypes
import subprocess

HOSTS_ENTRIES = [
    "prometheus.kube-lab.local",
    "grafana.kube-lab.local",
    "k8s-dashboard.kube-lab.local",
    "devops.kube-lab.local",
    "todo.kube-lab.local",
    "microfail.kube-lab.local"
]

def is_admin():
    if platform.system() == "Windows":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        return os.geteuid() == 0

def get_ip_from_env():
    try:
        with open("env.conf", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("IP_ADDRESS="):
                    return line.strip().split("=")[1]
    except:
        pass
    return None

def update_hosts_file(ip, domains):
    system = platform.system()
    if system == "Windows":
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
    elif system in ["Linux", "Darwin"]:
        hosts_path = "/etc/hosts"
    else:
        print("❌ Unsupported OS")
        return False

    try:
        with open(hosts_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Build desired entry line
        entry_line = f"{ip}  {' '.join(domains)}\n"

        # Check if already present
        if any(ip in line and all(domain in line for domain in domains) for line in lines):
            print("✅ Hosts file already contains required entries.")
            return True

        # Append to hosts file
        with open(hosts_path, "a", encoding="utf-8") as f:
            f.write("\n# Kube Resilience Lab domains\n")
            f.write(entry_line)

        print(f"✅ Added to hosts file:\n{entry_line}")
        return True

    except Exception as e:
        print(f"❌ Failed to update hosts file: {e}")
        return False

def main():
    if not is_admin():
        print("⚠️ Please run this script as administrator/root to modify your hosts file.")
        if platform.system() == "Windows":
            print("💡 Right-click this script and choose 'Run as Administrator'.")
        else:
            print("💡 Try: sudo python3 update_hosts.py")
        sys.exit(1)

    ip = get_ip_from_env()
    if not ip:
        print("❌ Could not read IP_ADDRESS from env.conf.")
        sys.exit(1)

    if update_hosts_file(ip, HOSTS_ENTRIES):
        print("🚀 Hosts file updated successfully.")
    else:
        print("❌ Failed to update hosts file.")

if __name__ == "__main__":
    main()
