#!/usr/bin/env bash
set -euo pipefail

: "${ASPM_LAB_DJANGO_BASE:?Use a prebuilt ASPM Django lab image with matching dependencies}"
: "${ASPM_LAB_NGINX_BASE:?Use a prebuilt ASPM nginx lab image with compiled dependencies}"
revision=$(git rev-parse "${1:-HEAD}^{commit}")
tag=${revision:0:12}
build=$(mktemp -d "${TMPDIR:-/tmp}/aspm-candidate.XXXXXX")
trap 'rm -rf -- "$build"' EXIT

mkdir "$build/django" "$build/nginx"
git archive "$revision" dojo | tar -xf - -C "$build/django"
cp "$build/django/dojo/static/dojo/css/aspm.css" "$build/django/dojo/static/dojo/js/aspm.js" "$build/nginx/"
cat > "$build/django/Dockerfile" <<'DOCKER'
ARG BASE
FROM ${BASE}
ARG REVISION
LABEL org.opencontainers.image.revision=$REVISION
ENV DD_ASPM_GIT_SHA=$REVISION
COPY dojo/ /app/dojo/
DOCKER
cat > "$build/nginx/Dockerfile" <<'DOCKER'
ARG BASE
FROM ${BASE}
ARG REVISION
LABEL org.opencontainers.image.revision=$REVISION
COPY aspm.css /usr/share/nginx/html/static/dojo/css/aspm.css
COPY aspm.js /usr/share/nginx/html/static/dojo/js/aspm.js
DOCKER

docker build --pull=false --build-arg "BASE=$ASPM_LAB_DJANGO_BASE" --build-arg "REVISION=$revision" \
  --tag "aspm-dual-lab/django:$tag" "$build/django"
docker build --pull=false --build-arg "BASE=$ASPM_LAB_NGINX_BASE" --build-arg "REVISION=$revision" \
  --tag "aspm-dual-lab/nginx:$tag" "$build/nginx"
docker image inspect "aspm-dual-lab/django:$tag" "aspm-dual-lab/nginx:$tag" \
  --format '{{.Id}} {{index .Config.Labels "org.opencontainers.image.revision"}} {{.Os}}/{{.Architecture}}'
