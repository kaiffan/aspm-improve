#!/usr/bin/env bash
set -euo pipefail
if [[ ${1:-} == --help || $# != 7 ]]; then
  echo 'Usage: prepare-lab.sh CONTEXT aspm-lab-NEW STORAGE_CLASS POSTGRES_IMAGE VALKEY_IMAGE DJANGO_IMAGE NGINX_IMAGE'
  echo 'Creates independent PostgreSQL, broker/cache, PVCs, Secrets and lab values. Exit 0 on success, 1 on command failure, 2 on usage error.'
  [[ ${1:-} == --help ]] && exit 0
  exit 2
fi
context=$1 namespace=$2
if [[ ! "$namespace" =~ ^aspm-lab-[a-z0-9-]+$ ]]; then
  echo 'Choose a new aspm-lab-* namespace.' >&2; exit 2
fi
port=${ASPM_LAB_PORT:-18739}
[[ "$port" =~ ^[1-9][0-9]{0,4}$ ]] && (( port <= 65535 )) || { echo 'Invalid ASPM_LAB_PORT' >&2; exit 2; }
set -C
out="./values-$namespace.yaml"
if [[ -e "$out" ]]; then echo "Values already exist: $out" >&2; exit 2; fi
root=$(cd "$(dirname "$0")/.." && pwd)
k=(kubectl --context "$context" -n "$namespace")
"${k[@]}" create namespace "$namespace"
"${k[@]}" label namespace "$namespace" aspm-lab=true
python3 - "$namespace" <<'PY' | "${k[@]}" create -f -
import json
import secrets
import sys

def obj(name, data):
    return {"apiVersion": "v1", "kind": "Secret", "metadata": {"name": name, "namespace": sys.argv[1]},
            "type": "Opaque", "stringData": data}

password = secrets.token_hex(24)
print(json.dumps({"apiVersion": "v1", "kind": "List", "items": [
    obj("aspm-lab-postgres", {"password": password}),
    obj("aspm-runtime", {"django-secret-key": secrets.token_urlsafe(64), "credential-aes-key": secrets.token_hex(32),
                         "database-url": f"postgresql://aspm_lab:{password}@postgres:5432/aspm_lab",
                         "broker-url": "redis://broker:6379/0", "cache-url": "redis://cache:6379/0"}),
]}))
PY
python3 - "$root/config/lab-dependencies.yaml" "$3" "$4" "$5" "$6" <<'PY' | "${k[@]}" create -f -
from pathlib import Path
import json
import sys

template, *values = sys.argv[1:]
data = Path(template).read_text()
for key, value in zip(("LAB_STORAGE_CLASS", "LAB_POSTGRES_IMAGE", "LAB_VALKEY_IMAGE", "LAB_DJANGO_IMAGE"), values, strict=True):
    data = data.replace(key, json.dumps(value))
print(data)
PY
for service in postgres broker cache; do
  "${k[@]}" rollout status "deployment/$service" --timeout=4m
done
"${k[@]}" wait --for=condition=complete job/provision-volume-owners --timeout=4m
python3 - "$6" "$7" "$port" "$root/DELIVERY_MANIFEST.json" >"$out" <<'PY'
import json
import sys
from pathlib import Path

def image(value):
    repo, sep, digest = value.partition("@")
    if sep:
        return {"repository": repo, "digest": digest}
    repo, tag = value.rsplit(":", 1)
    return {"repository": repo, "tag": tag, "pullPolicy": "IfNotPresent"}

print(json.dumps({
    "image": image(sys.argv[1]), "nginxImage": image(sys.argv[2]),
    "config": {"DD_ALLOWED_HOSTS": "localhost,127.0.0.1", "DD_SITE_URL": f"http://127.0.0.1:{sys.argv[3]}",
               "DD_ASPM_WEBHOOKS_ENABLED": "True", "DD_ASPM_GIT_SHA": json.loads(Path(sys.argv[4]).read_text())["application_sha"]},
    "tests": {"enabled": True}, "worker": {"readinessProbeEnabled": True},
    "networkPolicy": {"egress": [{"to": [{"podSelector": {"matchExpressions": [
        {"key": "aspm-lab-service", "operator": "In", "values": ["postgres", "broker", "cache"]}]}}],
        "ports": [{"protocol": "TCP", "port": 5432}, {"protocol": "TCP", "port": 6379}]}]},
}, indent=2))
PY
printf 'Lab values written to %s\n' "$out"
