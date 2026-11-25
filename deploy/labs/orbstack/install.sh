#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
lab="$root/deploy/labs/orbstack"
namespace=${ASPM_ORBSTACK_NAMESPACE:-aspm-lab-orbstack}
if [[ "$namespace" != aspm-lab-* ]]; then printf 'Expected an aspm-lab-* namespace\n' >&2; exit 2; fi
k=(kubectl --context orbstack)
case "${1:-}" in
  '') resume=false ;;
  --resume) resume=true ;;
  *) printf 'Usage: %s [--resume]\n' "$0" >&2; exit 2 ;;
esac
if [[ "$resume" == true ]]; then
  if [[ $("${k[@]}" get namespace "$namespace" -o 'jsonpath={.metadata.labels.aspm-lab}') != true ]]; then
    printf 'Refusing to reuse an unlabelled namespace\n' >&2
    exit 2
  fi
  "${k[@]}" -n "$namespace" get secret aspm-lab-postgres aspm-runtime -o name >/dev/null
else
"${k[@]}" create namespace "$namespace"
"${k[@]}" label namespace "$namespace" aspm-lab=true
# Create lab-specific credentials in memory. Do not emit manifest contents or values.
python3 - "$namespace" <<'PY' | "${k[@]}" -n "$namespace" apply -f -
import json
import secrets
import sys
namespace=sys.argv[1]
password=secrets.token_hex(24)
def secret(name, data):
    return {"apiVersion":"v1","kind":"Secret","metadata":{"name":name,"namespace":namespace},"type":"Opaque","stringData":data}
print(json.dumps({"apiVersion":"v1","kind":"List","items":[
    secret("aspm-lab-postgres", {"password":password}),
    secret("aspm-runtime", {
        "django-secret-key":secrets.token_urlsafe(64),
        "credential-aes-key":secrets.token_hex(32),
        "database-url":f"postgresql://aspm_lab:{password}@postgres:5432/aspm_lab",
        "broker-url":"redis://broker:6379/0",
        "cache-url":"redis://cache:6379/0",
    }),
]}))
PY
fi
pressure=$("${k[@]}" get node orbstack -o 'jsonpath={.status.conditions[?(@.type=="DiskPressure")].status}')
if [[ "$pressure" != False ]]; then
  printf 'OrbStack DiskPressure=%s. After it reports False, run %s --resume.\n' "$pressure" "$0" >&2
  exit 3
fi
# Only this lab's idempotent chown Job may have timed out while waiting for disk.
failed=$("${k[@]}" -n "$namespace" get job provision-volume-owners --ignore-not-found \
  -o 'jsonpath={.status.conditions[?(@.type=="Failed")].status}')
if [[ "$failed" == True ]]; then
  "${k[@]}" -n "$namespace" delete job provision-volume-owners
fi
"${k[@]}" -n "$namespace" apply -f "$lab/dependencies.yaml"
for workload in postgres broker cache; do
  "${k[@]}" -n "$namespace" rollout status deployment/"$workload" --timeout=240s
done
"${k[@]}" -n "$namespace" wait --for=condition=complete job/provision-volume-owners --timeout=240s
helm upgrade --install aspm "$root/deploy/helm/aspm" --kube-context orbstack -n "$namespace" \
  -f "$root/deploy/helm/aspm/values-dev.yaml" -f "$lab/values.yaml" --wait --timeout 8m
helm test aspm --kube-context orbstack -n "$namespace" --logs --timeout 2m
