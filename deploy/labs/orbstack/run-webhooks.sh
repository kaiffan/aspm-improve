#!/usr/bin/env bash
set -euo pipefail
lab=$(cd "$(dirname "$0")" && pwd)
namespace=${ASPM_ORBSTACK_NAMESPACE:-aspm-lab-orbstack}
if [[ "$namespace" != aspm-lab-* ]]; then printf 'Expected an aspm-lab-* namespace\n' >&2; exit 2; fi
k=(kubectl --context orbstack -n "$namespace")
if [[ $(kubectl --context orbstack get namespace "$namespace" -o 'jsonpath={.metadata.labels.aspm-lab}') != true ]]; then
  printf 'Expected an explicitly labelled ASPM lab namespace\n' >&2
  exit 2
fi
"${k[@]}" rollout status deployment/aspm-aspm-web --timeout=2m >&2
pod=$("${k[@]}" get pods -l 'app.kubernetes.io/component=web,app.kubernetes.io/instance=aspm' \
  --field-selector status.phase=Running -o 'jsonpath={.items[0].metadata.name}')
if [[ -z "$pod" ]]; then printf 'ASPM web pod unavailable\n' >&2; exit 1; fi
c=("${k[@]}" exec -i "$pod" -c web --)
# Pipe credentials directly between lab processes. Do not write them into logs or ConfigMaps.
"${c[@]}" sh -ec 'umask 077; cat >/tmp/aspm-webhook-fixture.py' < "$lab/provision_webhook_smoke.py"
"${c[@]}" sh -ec 'umask 077; cat >/tmp/aspm-webhook-smoke.py' < "$lab/webhook_smoke.py"
"${c[@]}" python manage.py shell --verbosity 0 -c 'import runpy; runpy.run_path("/tmp/aspm-webhook-fixture.py", run_name="__main__")' \
  | "${c[@]}" python /tmp/aspm-webhook-smoke.py http://127.0.0.1:8080
