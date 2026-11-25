"""Read-only native qualification disk/capacity preflight. Never removes data."""
# ruff: noqa: INP001 -- standalone CLI helpers invoke installed git/helm tools
import argparse
import json
import platform
import shutil
import sys
from pathlib import Path

GIB = 1024 ** 3
BUDGET_GIB = {"seed": 6, "archive": 4, "one_restore": 6, "wal": 5, "images_build": 10, "observations_indexes": 3, "reports_raw": 5, "margin": 6}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=Path.cwd())
    parser.add_argument("--docker-root", type=Path, help="Native daemon's DockerRootDir, inspected separately")
    args = parser.parse_args()
    paths = [args.path.resolve()]
    if args.docker_root:
        paths.append(args.docker_root.resolve())
    free_bytes = {str(path): shutil.disk_usage(path).free for path in paths}
    reserve_gib = 6
    required_bytes = (sum(BUDGET_GIB.values()) + reserve_gib) * GIB
    system = platform.system()
    machine = platform.machine()
    json.dump({
        "host": {"os": system, "architecture": machine},
        "budget_gib": BUDGET_GIB,
        "reserve_gib": reserve_gib,
        "required_bytes": required_bytes,
        "free_bytes": free_bytes,
        "disk_pass": min(free_bytes.values()) >= required_bytes,
        "native_host": system == "Linux" and machine in {"amd64", "x86_64"},
        "data_deleted": False,
    }, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
