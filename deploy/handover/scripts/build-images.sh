#!/usr/bin/env bash
set -euo pipefail
if [[ ${1:-} == --help || $# != 3 ]]; then
  echo 'Usage: build-images.sh linux/amd64|linux/arm64 IMAGE_PREFIX SOURCE_DIRECTORY'
  echo 'Builds and loads Django and nginx with a source-SHA tag. Reads source manifest from the package. Exit 0/1/2.'
  [[ ${1:-} == --help ]] && exit 0
  exit 2
fi
platform=$1 prefix=${2%/} source=$(cd "$3" && pwd)
root=$(cd "$(dirname "$0")/.." && pwd)
case "$platform" in linux/amd64|linux/arm64) ;; *) echo 'Unsupported platform' >&2; exit 2;; esac
sha=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["application_sha"])' "$root/DELIVERY_MANIFEST.json")
if [[ ! "$sha" =~ ^[a-f0-9]{40}$ || -z "$prefix" ]]; then echo 'Invalid source or image prefix' >&2; exit 2; fi
if [[ ! -f "$source/.aspm-source-revision" ]] || [[ $(cat "$source/.aspm-source-revision") != "$sha" ]]; then
  echo 'Use the verified application source archive from this delivery package.' >&2; exit 2
fi
for pair in django:django-debian nginx:nginx-alpine; do
  name=${pair%:*} dockerfile=${pair#*:}
  ref="$prefix/$name:${sha:0:12}-${platform##*/}"
  docker buildx build --load --platform "$platform" --target release \
    --label "org.opencontainers.image.revision=$sha" --label 'org.opencontainers.image.version=1.0.1' \
    --tag "$ref" --file "$source/Dockerfile.$dockerfile" "$source"
  docker image inspect "$ref" --format '{{.Id}} {{.Os}}/{{.Architecture}} {{index .Config.Labels "org.opencontainers.image.revision"}} {{json .RepoDigests}}'
  [[ $(docker image inspect "$ref" --format '{{.Os}}/{{.Architecture}}') == "$platform" ]]
done
