#!/usr/bin/env python3
"""Verify and prepare the portable ASPM monitoring source in a new directory."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORY = "aspm-1.0.1-source"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verified_file(relative, expected):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file() or sha256(path) != expected:
        raise ValueError(f"Package verification failed for {relative}")
    return path


def prepare(destination):
    manifest = json.loads((ROOT / "DELIVERY_MANIFEST.json").read_text())
    monitoring = manifest["monitoring"]
    baseline = manifest["application_sha"]
    revision = monitoring["source_sha"]
    if not all(re.fullmatch(r"[0-9a-f]{40}", sha) for sha in (baseline, revision)) or baseline != monitoring["baseline_application_sha"]:
        raise ValueError("Monitoring source revisions in the manifest disagree")
    archive = verified_file(manifest["source"], manifest["source_sha256"])
    patch = verified_file(monitoring["runtime_patch"], monitoring["runtime_patch_sha256"])
    target = destination / SOURCE_DIRECTORY
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"Choose a new build parent; {target} already exists")
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".aspm-source-", dir=destination) as work:
        subprocess.run(["tar", "-xzf", str(archive), "-C", work], check=True)
        source = Path(work) / SOURCE_DIRECTORY
        marker = source / ".aspm-source-revision"
        if marker.read_text().strip() != baseline:
            raise ValueError("The unpacked source revision does not match the baseline")
        subprocess.run(["git", "apply", "--check", str(patch)], cwd=source, check=True)
        subprocess.run(["git", "apply", str(patch)], cwd=source, check=True)
        marker.write_text(f"{revision}\n")
        source.rename(target)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_parent", type=Path)
    args = parser.parse_args()
    try:
        print(prepare(args.build_parent.resolve()))
    except (KeyError, OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"ASPM: {error}\n")


if __name__ == "__main__":
    main()
