import subprocess
import sys
import json
import functools

print = functools.partial(print, flush=True)

def get_ingress_hosts():
    try:
        result = subprocess.run(
            ["kubectl", "get", "ingress", "-A", "-o", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            print(f"[ERROR] Failed to get ingress: {result.stderr}")
            sys.exit(1)

        ingress_data = json.loads(result.stdout)
        hosts = set()

        for item in ingress_data.get("items", []):
            rules = item.get("spec", {}).get("rules", [])
            for rule in rules:
                host = rule.get("host")
                if host:
                    hosts.add(host)

        return sorted(hosts)

    except Exception as e:
        print(f"[ERROR] Could not retrieve ingress hosts: {e}")
        sys.exit(1)

def get_ingress_ip():
    try:
        result = subprocess.run(
            ["kubectl", "get", "ingress", "-A", "-o", "json"],
            capture_output=True, text=True, timeout=10
        )
        ingress_data = json.loads(result.stdout)
        for item in ingress_data.get("items", []):
            addresses = item.get("status", {}).get("loadBalancer", {}).get("ingress", [])
            if addresses:
                ip = addresses[0].get("ip") or addresses[0].get("hostname")
                if ip:
                    return ip
    except Exception as e:
        print(f"[ERROR] Failed to extract Ingress IP: {e}")
    # Fallback to localhost if nothing is found
    print("[WARN] Falling back to 127.0.0.1 as Ingress IP.")
    return "127.0.0.1"

def check_url(host):
    try:
        ingress_ip = get_ingress_ip()
        result = subprocess.run(
            ["curl", "-s", "-L", "-o", "/dev/null", "-w", "%{http_code}", "-H", f"Host: {host}", f"http://{ingress_ip}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        status_code = result.stdout.strip()
        if status_code == "200":
            print(f"✅ {host} is accessible")
            return True
        else:
            print(f"❌ {host} returned status code {status_code}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ {host} timed out")
        return False
    except Exception as e:
        print(f"❌ {host} failed: {e}")
        return False

def main():
    print("🔍 Fetching Ingress hostnames...\n")
    hosts = get_ingress_hosts()

    if not hosts:
        print("⚠️ No ingress hosts found.")
        sys.exit(0)

    print("🧪 Curl-checking discovered Ingress URLs:\n")
    failed = False
    for host in hosts:
        if not check_url(host):
            failed = True

    if failed:
        print("\n❌ One or more endpoints failed.")
        sys.exit(1)

    print("\n✅ All endpoints are accessible.")
    sys.exit(0)

if __name__ == "__main__":
    main()
