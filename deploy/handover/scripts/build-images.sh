#!/usr/bin/env bash
set -euo pipefail
revision=baseline
if [[ ${1:-} == --monitoring ]]; then
  revision=monitoring
  shift
fi
if [[ ${1:-} == --help || $# != 3 ]]; then
  echo 'Usage: build-images.sh [--monitoring] linux/amd64|linux/arm64 IMAGE_PREFIX SOURCE_DIRECTORY'
  echo 'Builds and loads Django and nginx with a source-SHA tag. Reads source manifest from the package. Exit 0/1/2.'
  [[ ${1:-} == --help ]] && exit 0
  exit 2
fi
platform=$1 prefix=${2%/} source=$(cd "$3" && pwd)
root=$(cd "$(dirname "$0")/.." && pwd)
case "$platform" in linux/amd64|linux/arm64) ;; *) echo 'Unsupported platform' >&2; exit 2;; esac
sha=$(python3 - "$root/DELIVERY_MANIFEST.json" "$revision" <<'PYTHON'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text())
if sys.argv[2] == "monitoring":
    if "monitoring" not in manifest:
        raise SystemExit("This package has no monitoring source revision")
    print(manifest["monitoring"]["source_sha"])
else:
    print(manifest["application_sha"])
PYTHON
)
if [[ ! "$sha" =~ ^[a-f0-9]{40}$ || -z "$prefix" ]]; then echo 'Invalid source or image prefix' >&2; exit 2; fi
if [[ ! -f "$source/.aspm-source-revision" ]] || [[ $(cat "$source/.aspm-source-revision") != "$sha" ]]; then
  echo 'Source revision does not match the selected build. For --monitoring, use prepare-monitoring-source.py.' >&2; exit 2
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
