"""Build a monitoring edition from the verified baseline delivery and a source revision."""
# ruff: noqa: INP001
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
from datetime import date


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("original", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--chart", type=Path, required=True)
    parser.add_argument("--guide", type=Path, required=True)
    parser.add_argument("--date", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    handover = Path(__file__).resolve().parents[2]
    repo = handover.parents[1]
    module = importlib.util.spec_from_file_location("assembler", handover / "scripts/assemble-delivery.py")
    assembler = importlib.util.module_from_spec(module)
    module.loader.exec_module(assembler)

    root = args.output / assembler.ROOT_NAME
    args.output.mkdir(parents=True, exist_ok=True)
    shutil.copytree(args.original, root)
    manifest_file = root / "DELIVERY_MANIFEST.json"
    manifest = json.loads(manifest_file.read_text())
    shutil.copytree(handover / "monitoring", root / "monitoring", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    for source in ("START_HERE.md", "docs/13_MONITORING.md", "scripts/render-guide.py"):
        shutil.copy2(handover / source, root / source)
    shutil.copy2(args.guide, root / "docs" / args.guide.name)
    shutil.rmtree(root / "helm/aspm")
    shutil.copytree(repo / "deploy/helm/aspm", root / "helm/aspm", ignore=shutil.ignore_patterns("__pycache__"))
    chart = root / "helm" / args.chart.name
    shutil.copy2(args.chart, chart)
    # Keep the originally qualified source/image records separate from the additive monitoring commit.
    patch = root / "monitoring/source/aspm-monitoring.patch"
    patch.parent.mkdir()
    patch.write_bytes(subprocess.check_output(
        ["git", "-C", str(repo), "diff", "--binary", manifest["application_sha"], args.sha, "--", "dojo"],
    ))
    if not patch.stat().st_size:
        msg = "No monitoring runtime patch was found"
        raise ValueError(msg)
    manifest.update({
        "chart": str(chart.relative_to(root)),
        "chart_version": args.chart.stem.removeprefix("aspm-"),
        "chart_source_sha": args.sha,
        "chart_sha256": assembler.digest(chart),
        "generated_on": args.date.isoformat(),
        "release_status": "MONITORING HANDOVER — PRODUCTION HOLD",
        "monitoring": {
            "source_sha": args.sha,
            "baseline_application_sha": manifest["application_sha"],
            "runtime_patch": str(patch.relative_to(root)),
            "runtime_patch_sha256": assembler.digest(patch),
            "guide": "monitoring/README.md",
            "qualification": "monitoring/VALIDATION.md",
        },
    })
    assembler.output_json(manifest_file, manifest)
    assembler.check_links(root)
    checksums = root / "SHA256SUMS"
    with checksums.open("w", encoding="utf-8") as output:
        for source in sorted(root.rglob("*")):
            if source.is_file() and source != checksums:
                output.write(f"{assembler.digest(source)}  ./{source.relative_to(root)}\n")
    archive = args.output / (assembler.ROOT_NAME + ".tar.gz")
    assembler.archive(archive, root)
    assembler.verify_archive(archive, assembler.ROOT_NAME)
    with archive.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    archive.with_suffix(archive.suffix + ".sha256").write_text(f"{digest}  {archive.name}\n")
    print(archive)


if __name__ == "__main__":
    main()
