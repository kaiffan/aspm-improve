#!/usr/bin/env bash
# Explicit lab context/namespace are required. This script never deletes a namespace or PVC.
set -euo pipefail
context=${ASPM_LAB_CONTEXT:?Set a dedicated Kubernetes lab context}
namespace=${ASPM_LAB_NAMESPACE:?Set a dedicated lab namespace}
values=${ASPM_LAB_VALUES:?Set a reviewed values file with existing Secrets/PVCs/dependency rules}
root=$(cd "$(dirname "$0")/../.." && pwd)
if [[ "$namespace" != aspm-lab-* ]]; then echo 'Namespace must start with aspm-lab-' >&2; exit 2; fi
kubectl --context "$context" get namespace "$namespace" -o jsonpath='{.metadata.labels.aspm-lab}' | python3 -c 'import sys; assert sys.stdin.read()=="true", "Lab ownership label is missing"'
helm upgrade --install aspm "$root/deploy/helm/aspm" --kube-context "$context" -n "$namespace" -f "$values" --set tests.enabled=true --wait --timeout 35m
helm test aspm --kube-context "$context" -n "$namespace" --logs
helm upgrade aspm "$root/deploy/helm/aspm" --kube-context "$context" -n "$namespace" -f "$values" --set tests.enabled=true --wait --timeout 35m
kubectl --context "$context" -n "$namespace" rollout restart deployment/aspm-aspm-web deployment/aspm-aspm-worker
kubectl --context "$context" -n "$namespace" rollout status deployment/aspm-aspm-web --timeout=5m
kubectl --context "$context" -n "$namespace" rollout status deployment/aspm-aspm-worker --timeout=20m
helm test aspm --kube-context "$context" -n "$namespace" --logs
helm history aspm --kube-context "$context" -n "$namespace"
echo 'Review migration compatibility and database backup before any explicit Helm rollback. No schema rollback was attempted.'
