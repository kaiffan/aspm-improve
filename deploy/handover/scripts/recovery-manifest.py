#!/usr/bin/env python3
"""Seal or verify the database, exported object inventory and deployment inputs."""
import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def files(root):
    paths = (root / "database.dump", root / "storage" / "objects.jsonl", root / "deployment.json")
    with paths[1].open(encoding="utf-8") as inventory:
        for line in inventory:
            entry = json.loads(line)
            blob = entry["blob"]
            if not re.fullmatch(r"[a-f0-9]{64}", blob):
                msg = "Invalid inventory blob name"
                raise ValueError(msg)
            path = root / "storage" / "objects" / blob
            if not path.is_file() or path.stat().st_size != entry["size"] or digest(path) != entry["sha256"]:
                msg = "Object backup failed its integrity check"
                raise ValueError(msg)
    return {str(path.relative_to(root)): digest(path) for path in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["seal", "verify"])
    parser.add_argument("root", type=Path)
    parser.add_argument("--application-sha")
    parser.add_argument("--chart-version")
    parser.add_argument("--source-database")
    parser.add_argument("--writers-paused", action="store_true")
    args = parser.parse_args()
    manifest = args.root / "RECOVERY_MANIFEST.json"
    checksums = files(args.root)
    if args.operation == "verify":
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if data["version"] != 1 or data["checksums"] != checksums:
            msg = "Recovery manifest differs from the backup files"
            raise ValueError(msg)
        print(checksums["storage/objects.jsonl"])
        return
    if not (args.writers_paused and args.chart_version and args.source_database and re.fullmatch(r"[0-9a-f]{40}", args.application_sha or "")):
        parser.error("Sealing requires a frozen source, its database, application SHA and chart version")
    data = {
        "version": 1, "sealed_at": datetime.now(UTC).isoformat(),
        "consistency": "application_writers_quiesced",
        "source_database": args.source_database, "application_sha": args.application_sha,
        "chart_version": args.chart_version, "checksums": checksums,
    }
    with manifest.open("x", encoding="utf-8") as target:
        json.dump(data, target, indent=2, sort_keys=True)
        target.write("\n")


if __name__ == "__main__":
    main()
