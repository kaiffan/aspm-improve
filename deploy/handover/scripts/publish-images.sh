#!/usr/bin/env bash
set -euo pipefail
if [[ ${1:-} == --help || $# != 3 ]]; then
  echo 'Usage: publish-images.sh linux/amd64|linux/arm64 REGISTRY/PROJECT IMAGE_VALUES_FILE'
  echo 'Pushes the two monitoring images, verifies their digests and writes Helm image values.'
  [[ ${1:-} == --help ]] && exit 0
  exit 2
fi
platform=$1 prefix=${2%/} output=$3
root=$(cd "$(dirname "$0")/.." && pwd)
case "$platform" in linux/amd64|linux/arm64) ;; *) echo 'Unsupported platform' >&2; exit 2;; esac
registry=${prefix%%/*}
if [[ "$prefix" != */* || ! "$prefix" =~ ^[a-z0-9][a-z0-9.-]*(:[0-9]+)?(/[a-z0-9][a-z0-9._-]*)+$ ]]; then
  echo 'Use an explicit registry hostname and repository prefix, without a scheme or credentials.' >&2
  exit 2
fi
case "$registry" in *.*|*:*|localhost) ;; *) echo 'The registry hostname must be explicit.' >&2; exit 2;; esac
if [[ -e "$output" || -L "$output" ]]; then
  echo 'Choose a new image values file.' >&2
  exit 2
fi
sha=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["monitoring"]["source_sha"])' "$root/DELIVERY_MANIFEST.json")
[[ "$sha" =~ ^[a-f0-9]{40}$ ]] || { echo 'Invalid monitoring revision.' >&2; exit 2; }
tag="${sha:0:12}-${platform##*/}"
layout='{{.Id}} {{.Os}}/{{.Architecture}} {{index .Config.Labels "org.opencontainers.image.revision"}}'
for name in django nginx; do
  ref="$prefix/$name:$tag"
  read -r image_id actual_platform revision < <(docker image inspect "$ref" --format "$layout")
  if [[ -z "$image_id" || "$actual_platform" != "$platform" || "$revision" != "$sha" ]]; then
    echo "Build $ref for $platform from the monitoring revision first." >&2
    exit 1
  fi
  if [[ "$name" == django ]]; then django_id=$image_id; else nginx_id=$image_id; fi
done
for name in django nginx; do
  repository="$prefix/$name"
  ref="$repository:$tag"
  docker push "$ref"
  digest=$(docker buildx imagetools inspect "$ref" --format '{{.Manifest.Digest}}')
  if [[ ! "$digest" =~ ^sha256:[a-f0-9]{64}$ ]]; then
    echo "Could not read a registry digest for $ref." >&2
    exit 1
  fi
  docker pull --platform "$platform" "$repository@$digest"
  if [[ "$name" == django ]]; then
    expected_id=$django_id
    django_digest=$digest
  else
    expected_id=$nginx_id
    nginx_digest=$digest
  fi
  actual=$(docker image inspect "$repository@$digest" --format "$layout")
  if [[ "$actual" != "$expected_id $platform $sha" ]]; then
    echo "The pulled image digest does not match the locally built image: $ref" >&2
    exit 1
  fi
done
(
  set -o noclobber
  cat >"$output" <<YAML
image:
  repository: $prefix/django
  digest: $django_digest
nginxImage:
  repository: $prefix/nginx
  digest: $nginx_digest
config:
  DD_ASPM_GIT_SHA: "$sha"
YAML
)
printf 'Verified both images and wrote %s\n' "$output"
