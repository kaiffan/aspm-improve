#!/usr/bin/env bash
set -euo pipefail
if [[ ${1:-} == --help || $# != 5 ]]; then
  echo 'Usage: restore.sh PG_SERVICE EMPTY_DATABASE DUMP_PATH SOURCE_DATABASE SERVICE/EMPTY_DATABASE'
  echo 'Validates SHA-256. Restores in one transaction into an empty, explicitly confirmed target. Exit 0/1/2.'
  [[ ${1:-} == --help ]] && exit 0
  exit 2
fi
service=$1 target=$2 dump=$3 source=$4
[[ "$service" =~ ^[A-Za-z0-9_.-]+$ && "$source" != "$target" && "$5" == "$service/$target" ]] || {
  echo 'The named target must differ from the source and match the explicit confirmation.' >&2; exit 2;
}
[[ -r "$dump" && -r "$dump.sha256" ]] || { echo 'Dump and checksum are required' >&2; exit 2; }
expected=$(cat "$dump.sha256")
actual=$(shasum -a 256 "$dump" | cut -d' ' -f1)
[[ "$actual" == "$expected" ]] || { echo 'Dump checksum mismatch' >&2; exit 1; }
con="service=$service"
actual=$(psql -X -Aqt -w "$con" -c 'SELECT current_database()')
[[ "$actual" == "$target" ]] || { echo 'Database does not match expected target' >&2; exit 2; }
objects=$(psql -X -Aqt -w "$con" -c "SELECT count(*) FROM pg_class AS c JOIN pg_namespace AS n ON c.relnamespace=n.oid WHERE n.nspname <> 'information_schema' AND left(n.nspname, 3) <> 'pg_'")
[[ "$objects" == 0 ]] || { echo 'Target database must be empty' >&2; exit 2; }
pg_restore --no-password --single-transaction --exit-on-error --no-owner --no-privileges --dbname="$con" "$dump"
psql -X -Aqt -w "$con" -c 'SELECT count(*) FROM django_migrations'
printf 'Restored into %s; continue with application and evidence checks.\n' "$target"
