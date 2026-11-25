#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
chart="$root/deploy/helm/aspm"
output=${1:?Usage: validate-chart.sh OUTPUT_DIRECTORY}
mkdir -p "$output"
python3 "$chart/tests/generate_schema.py"
python3 "$chart/tests/generate_readme.py"
python3 -m unittest discover -s "$chart/tests" -p 'test_*.py'
validate_manifest() {
  if [[ -n "${ASPM_KUBE_SCHEMA_LOCATION:-}" ]]; then
    kubeconform -strict -summary -kubernetes-version 1.31.0 -schema-location "$ASPM_KUBE_SCHEMA_LOCATION" "$1"
  else
    kubeconform -strict -summary -kubernetes-version 1.31.0 "$1"
  fi
}
helm lint "$chart"
helm template qualification "$chart" > "$output/helm-default.yaml"
validate_manifest "$output/helm-default.yaml"
for profile in dev staging production.example; do
  helm lint "$chart" -f "$chart/values-$profile.yaml"
  helm template qualification "$chart" -f "$chart/values-$profile.yaml" > "$output/helm-$profile.yaml"
  validate_manifest "$output/helm-$profile.yaml"
done
helm template qualification "$chart" --set tests.enabled=true --set ingress.enabled=true --set hpa.enabled=true > "$output/helm-extended.yaml"
validate_manifest "$output/helm-extended.yaml"
helm package "$chart" -d "$output"
