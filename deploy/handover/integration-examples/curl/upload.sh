#!/usr/bin/env bash
set -euo pipefail
if [[ ${1:-} == --help || $# != 2 ]]; then
  echo 'Usage: upload.sh SCANNER_TYPE REPORT_FILE'
  echo 'Set ASPM_URL, ASPM_TOKEN, ASPM_PROJECT_ID, ASPM_REPOSITORY_ID, ASPM_COMMIT_SHA, ASPM_IDEMPOTENCY_KEY. Exit 0/1/2.'
  [[ ${1:-} == --help ]] && exit 0
  exit 2
fi
: "${ASPM_URL:?}" "${ASPM_TOKEN:?}" "${ASPM_PROJECT_ID:?}" "${ASPM_REPOSITORY_ID:?}" "${ASPM_COMMIT_SHA:?}" "${ASPM_IDEMPOTENCY_KEY:?}"
[[ "$ASPM_URL" == https://* ]] || { echo 'Configure the trusted HTTPS endpoint' >&2; exit 2; }
[[ "$ASPM_COMMIT_SHA" =~ ^([[:xdigit:]]{40}|[[:xdigit:]]{64})$ && -r "$2" ]] || exit 2
umask 077
tmp=$(mktemp -d)
trap 'rm -f -- "$tmp/headers" "$tmp/response"; rmdir -- "$tmp"' EXIT
printf 'Authorization: ASPM %s\n' "$ASPM_TOKEN" >"$tmp/headers"
curl --fail-with-body --silent --show-error --connect-timeout 10 --max-time 120 \
  --retry 3 -H "@$tmp/headers" -H "Idempotency-Key: $ASPM_IDEMPOTENCY_KEY" \
  --form-string "project_id=$ASPM_PROJECT_ID" --form-string "repository_id=$ASPM_REPOSITORY_ID" \
  --form-string "commit_sha=$ASPM_COMMIT_SHA" --form-string "scanner_type=$1" -F "file=@$2" \
  "${ASPM_URL%/}/api/aspm/v1/scans/" >"$tmp/response"
id=$(python3 -c 'import json,sys,uuid; print(uuid.UUID(json.load(sys.stdin)["id"]))' <"$tmp/response")
for step in $(seq 1 60); do
  curl --fail-with-body --silent --show-error --connect-timeout 10 --max-time 25 --retry 3 \
    -H "@$tmp/headers" "${ASPM_URL%/}/api/aspm/v1/scans/$id/" >"$tmp/response"
  status=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])' <"$tmp/response")
  case "$status" in
    COMPLETED) cat "$tmp/response"; exit 0;;
    FAILED) python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["id"],d["error_code"])' <"$tmp/response" >&2; exit 1;;
    ACCEPTED|PROCESSING) sleep 5;;
    *) echo 'Unknown ScanRun status' >&2; exit 1;;
  esac
done
printf 'Polling deadline reached for ScanRun %s\n' "$id" >&2
exit 1
