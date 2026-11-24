#!/usr/bin/env sh
set -eu
: "${ASPM_URL:?Set HTTPS ASPM URL}"
: "${ASPM_TOKEN:?Set masked service token}"
: "${ASPM_PROJECT_ID:?Select an existing Product}"
: "${REPOSITORY_URL:?Set repository HTTP(S) URL}"
: "${COMMIT_SHA:?Set full Git SHA}"
: "${DELIVERY_KEY:?Set a stable pipeline/job/attempt delivery identity}"
: "${SCANNER_TYPE:?For example Semgrep JSON Report or Trivy Scan}"
: "${REPORT_FILE:?Set scanner artifact filename}"

# Do not enable shell tracing: the Authorization header is a secret.
curl --fail-with-body --silent --show-error --retry 3 --retry-all-errors \
  --connect-timeout 10 --max-time 180 \
  -H "Authorization: ASPM ${ASPM_TOKEN}" \
  -H "Idempotency-Key: ${DELIVERY_KEY}" \
  -F "project_id=${ASPM_PROJECT_ID}" \
  -F "repository_url=${REPOSITORY_URL}" \
  -F "commit_sha=${COMMIT_SHA}" \
  -F "scanner_type=${SCANNER_TYPE}" \
  -F "file=@${REPORT_FILE}" \
  "${ASPM_URL%/}/api/aspm/v1/scans/"

# Status: curl -H "Authorization: ASPM $ASPM_TOKEN" "$ASPM_URL/api/aspm/v1/scans/$SCAN_ID/"
# After ALL expected jobs have delivered and their status is terminal:
# curl -X POST -H "Authorization: ASPM $ASPM_TOKEN" -H 'Content-Type: application/json' \
#   -d '{"expected_scanners":["Semgrep JSON Report","Trivy Scan"]}' \
#   "$ASPM_URL/api/aspm/v1/commits/$COMMIT_ID/finalize/"
# curl -X POST -H "Authorization: ASPM $ASPM_TOKEN" -H 'Content-Type: application/json' \
#   -d '{}' "$ASPM_URL/api/aspm/v1/commits/$COMMIT_ID/reports/"
