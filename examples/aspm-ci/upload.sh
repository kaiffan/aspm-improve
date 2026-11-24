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

# These identify one pipeline and distinguish retries from independent deliveries.
set --
[ -z "${PIPELINE_ID:-}" ] || set -- "$@" --form-string "pipeline_id=$PIPELINE_ID"
[ -z "${JOB_ID:-}" ] || set -- "$@" --form-string "job_id=$JOB_ID"
[ -z "${ATTEMPT_NUMBER:-}" ] || set -- "$@" --form-string "attempt_number=$ATTEMPT_NUMBER"
[ -z "${SCAN_SCOPE:-}" ] || set -- "$@" --form-string "scan_scope=$SCAN_SCOPE"
[ -z "${ASPM_EXPECTED_SCANNERS:-}" ] || set -- "$@" --form-string "expected_scanners=$ASPM_EXPECTED_SCANNERS"

# Do not enable shell tracing: the Authorization header is a secret.
curl --fail-with-body --silent --show-error --retry 3 --retry-all-errors \
  --connect-timeout 10 --max-time 180 \
  -H "Authorization: ASPM ${ASPM_TOKEN}" \
  -H "Idempotency-Key: ${DELIVERY_KEY}" \
  --form-string "project_id=${ASPM_PROJECT_ID}" \
  --form-string "repository_url=${REPOSITORY_URL}" \
  --form-string "commit_sha=${COMMIT_SHA}" \
  --form-string "scanner_type=${SCANNER_TYPE}" \
  "$@" -F "file=@${REPORT_FILE}" \
  "${ASPM_URL%/}/api/aspm/v1/scans/"

# Results publish automatically; no finalize or export request is needed.
# Optional status: GET /api/aspm/v1/scans/$SCAN_ID/
# Optional fixed export: POST /api/aspm/v1/commits/$COMMIT_ID/reports/ with {}
# (requires read,reports scopes; use pipeline or scan_ids when selection is ambiguous).
