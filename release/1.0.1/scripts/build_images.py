"""Build both RC images from Git source and verified, digest-pinned dependency images."""
import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--sha", default="HEAD")
p.add_argument("--context", type=Path, required=True)
p.add_argument("--manifest", type=Path, required=True)
a = p.parse_args()
sha = subprocess.check_output(["git", "rev-parse", a.sha], cwd=ROOT, text=True).strip()
epoch = subprocess.check_output(["git", "show", "-s", "--format=%ct", sha], cwd=ROOT, text=True).strip()
lock = json.loads((ROOT / "release/1.0.1/build-lock.json").read_text())
for item in (lock["runtime"], lock["static"]):
    actual = subprocess.check_output(["docker", "image", "inspect", "--format", "{{.Id}}", item["image"]], text=True).strip()
    if actual != item["id"]:
        raise RuntimeError("Base image identity differs from release lock")
a.context.mkdir(parents=True, exist_ok=True)
if any(a.context.iterdir()):
    raise RuntimeError("Use an empty build context; existing files are preserved")
with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(["git", "archive", sha, "dojo", "LICENSE.md", "NOTICE"], cwd=ROOT))) as archive:
    archive.extractall(a.context, filter="tar")
msgfmt = shutil.which("msgfmt")
if not msgfmt:
    raise RuntimeError("GNU gettext msgfmt is required to preserve existing translations")
gettext_version = subprocess.check_output([msgfmt, "--version"], text=True).splitlines()[0]
translations = {}
for po in sorted((a.context / "dojo/locale").rglob("django.po")):
    mo = po.with_suffix(".mo")
    subprocess.run([msgfmt, str(po), "-o", str(mo)], check=True)
    translations[str(mo.relative_to(a.context))] = hashlib.sha256(mo.read_bytes()).hexdigest()
(a.context / "Dockerfile").write_text("ARG RUNTIME_BASE=" + lock["runtime"]["image"] + "\nARG STATIC_BASE=" + lock["static"]["image"] + "\n" + '''FROM ${RUNTIME_BASE} AS app
ARG SOURCE_DATE_EPOCH
ARG REVISION
USER root
RUN rm -rf /app/dojo
COPY --chown=1001:1001 dojo /app/dojo
COPY LICENSE.md NOTICE /app/
ENV DD_ASPM_GIT_SHA=${REVISION}
LABEL org.opencontainers.image.title="ASPM" org.opencontainers.image.version="1.0.1-rc1" org.opencontainers.image.source="https://github.com/kaiffan/aspm-improve" org.opencontainers.image.revision="${REVISION}" org.opencontainers.image.licenses="BSD-3-Clause" org.aspm.upstream.version="3.5.100"
USER 1001
FROM ${STATIC_BASE} AS nginx
ARG SOURCE_DATE_EPOCH
ARG REVISION
COPY dojo/static/ /usr/share/nginx/html/static/
COPY LICENSE.md NOTICE /usr/share/licenses/aspm/
LABEL org.opencontainers.image.title="ASPM static gateway" org.opencontainers.image.version="1.0.1-rc1" org.opencontainers.image.source="https://github.com/kaiffan/aspm-improve" org.opencontainers.image.revision="${REVISION}" org.aspm.upstream.version="3.5.100"
''')
for path in a.context.rglob("*"):
    if not path.is_symlink():
        os.utime(path, (int(epoch), int(epoch)))
images = {}
for target, prefix in (("app", "aspm-build"), ("nginx", "aspm-nginx-build")):
    image = prefix + ":" + sha[:12]
    subprocess.run(["docker", "build", "--provenance=false", "--build-arg", "RUNTIME_BASE=" + lock["runtime"]["image"], "--build-arg", "STATIC_BASE=" + lock["static"]["image"], "--build-arg", "REVISION=" + sha, "--build-arg", "SOURCE_DATE_EPOCH=" + epoch, "--target", target, "-t", image, str(a.context)], check=True)
    images[target] = {"tag": image, "id": subprocess.check_output(["docker", "image", "inspect", "--format", "{{.Id}}", image], text=True).strip()}
a.manifest.write_text(json.dumps({"source_sha": sha, "source_date_epoch": int(epoch), "upstream": "3.5.100", "version": "1.0.1", "channel": "rc1", "base_images": lock, "images": images, "gettext": gettext_version, "compiled_translations": translations}, indent=2) + "\n")
print("Built immutable source images", sha)
