"""Read-only native qualification disk/capacity preflight. Never removes data."""
# ruff: noqa: INP001 -- standalone CLI helpers invoke installed git/helm tools
import argparse
import shutil
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
    {str(p): shutil.disk_usage(p).free for p in paths}
    sum(BUDGET_GIB.values()) * GIB + 6 * GIB


if __name__ == "__main__":
    main()
