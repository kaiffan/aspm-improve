#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
chart="$root/deploy/helm/aspm"
output=${1:?Usage: validate-chart.sh OUTPUT_DIRECTORY}
mkdir -p "$output"
python3 "$chart/tests/generate_schema.py"
python3 "$chart/tests/generate_readme.py"
python3 -m unittest discover -s "$chart/tests" -p 'test_*.py'
for profile in default dev staging production.example; do
  options=()
  if [[ "$profile" != default ]]; then options=(-f "$chart/values-$profile.yaml"); fi
  helm lint "$chart" "${options[@]}"
  helm template qualification "$chart" "${options[@]}" > "$output/helm-$profile.yaml"
  kubeconform -strict -summary -kubernetes-version 1.31.0 "$output/helm-$profile.yaml"
done
helm template qualification "$chart" --set tests.enabled=true --set ingress.enabled=true --set hpa.enabled=true > "$output/helm-extended.yaml"
kubeconform -strict -summary -kubernetes-version 1.31.0 "$output/helm-extended.yaml"
helm package "$chart" -d "$output"
