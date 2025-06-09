#!/usr/bin/env python3
import os
import platform
import sys

HOSTS_LINE_TEMPLATE = "{ip} flask.kube-lab.local grafana.kube-lab.local prometheus.kube-lab.local k8s-dashboard.kube-lab.local todo.kube-lab.local\n"

def get_hosts_file():
    if platform.system() == "Windows":
        return r"C:\Windows\System32\drivers\etc\hosts"
    else:
        return "/etc/hosts"

def has_entry(content, ip):
    return ip in content and "kube-lab.local" in content

def add_hosts_entry(ip):
    if not ip:
        print("❌ No IP provided to update hosts file.")
        return False

    hosts_path = get_hosts_file()
    line_to_add = HOSTS_LINE_TEMPLATE.format(ip=ip)

    try:
        with open(hosts_path, "r") as f:
            content = f.read()
            if has_entry(content, ip):
                print("✅ Hosts entry already exists.")
                return True

        with open(hosts_path, "a") as f:
            f.write("\n" + line_to_add)
        print("✅ Hosts entry added.")
        return True
    except PermissionError:
        print(f"❌ Permission denied to write to {hosts_path}")
        return False
    except Exception as e:
        print(f"❌ Failed to update hosts file: {e}")
        return False
