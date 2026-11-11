#!/bin/sh
# Run only between load phases. Creates new databases; never overwrites or drops one.
set -eu
r4_prefix=${1:?Provide a NEW database prefix beginning with dd_round4}
case "$r4_prefix" in dd_round4*) ;; *) exit 2 ;; esac
case "$r4_prefix" in *[!a-z0-9_]*) exit 2 ;; esac
r4_pg=django-defectdojo-postgres-1
r4_seed="${r4_prefix}seed"
docker exec "$r4_pg" sh -c 'createdb -U "$POSTGRES_USER" "$1"' sh "$r4_seed"
docker exec "$r4_pg" sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f "$1"' sh "/tmp/${r4_prefix}snapshot.dump"
docker exec "$r4_pg" sh -c 'pg_restore -U "$POSTGRES_USER" -d "$1" --no-owner --no-privileges --exit-on-error "$2"' sh "$r4_seed" "/tmp/${r4_prefix}snapshot.dump"
docker exec "$r4_pg" sh -c 'psql -X -U "$POSTGRES_USER" -d "$1" -v ON_ERROR_STOP=1 -c ANALYZE' sh "$r4_seed"
for r4_variant in original current final; do
  docker exec "$r4_pg" sh -c 'createdb -U "$POSTGRES_USER" -T "$1" "$2"' sh "$r4_seed" "${r4_prefix}${r4_variant}"
done
