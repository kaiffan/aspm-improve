#!/usr/bin/env bash
set -euo pipefail
if [[ ${1:-} == --help || $# != 3 ]]; then
  echo 'Usage: backup.sh PG_SERVICE EXPECTED_DATABASE NEW_DUMP_PATH'
  echo 'Uses libpq service and protected passfile. Creates a verified custom dump and SHA-256 sidecar. Exit 0/1/2.'
  [[ ${1:-} == --help ]] && exit 0
  exit 2
fi
service=$1 expected=$2 output=$3
[[ "$service" =~ ^[A-Za-z0-9_.-]+$ ]] || { echo 'Invalid service name' >&2; exit 2; }
[[ ! -e "$output" && ! -e "$output.sha256" ]] || { echo 'Choose a new destination' >&2; exit 2; }
actual=$(psql -X -Aqt -w "service=$service" -c 'SELECT current_database()')
[[ "$actual" == "$expected" ]] || { echo 'Database does not match expected source' >&2; exit 2; }
umask 077
stage=$(mktemp "${output}.incomplete.XXXXXX")
trap 'rm -f -- "$stage"' EXIT
pg_dump --no-password --format=custom --no-owner --no-acl --dbname="service=$service" --file="$stage"
pg_restore --list "$stage" >/dev/null
digest=$(shasum -a 256 "$stage" | cut -d' ' -f1)
ln "$stage" "$output"
(set -C; printf '%s\n' "$digest" >"$output.sha256")
printf 'Verified PostgreSQL dump created: %s\n' "$output"
