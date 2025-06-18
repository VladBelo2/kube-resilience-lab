import json

SAFE_EXTRA_KEYS = {"IP_ADDRESS", "VM_MEMORY", "VM_CPUS"}

def validate_env(features_file="features.json", env_file="env.conf"):
    try:
        with open(features_file, "r") as f:
            features = json.load(f)
        feature_keys = {feature["key"] for feature in features}
    except Exception as e:
        return {"status": "error", "message": f"Failed to read features.json: {e}"}

    try:
        with open(env_file, "r") as f:
            env_lines = f.readlines()
        env_keys = {line.split("=")[0].strip() for line in env_lines if "=" in line}
    except FileNotFoundError:
        env_keys = set()

    extra_keys = env_keys - feature_keys
    missing_keys = feature_keys - env_keys

    safe_extras = [k for k in extra_keys if k in SAFE_EXTRA_KEYS]
    real_extras = [k for k in extra_keys if k not in SAFE_EXTRA_KEYS]

    return {
        "status": "ok",
        "safe_extras": safe_extras,
        "real_extras": real_extras,
        "missing": list(missing_keys),
        "all_env_keys": list(env_keys),
        "all_feature_keys": list(feature_keys)
    }

if __name__ == "__main__":
    from pprint import pprint
    result = validate_env()
    pprint(result)