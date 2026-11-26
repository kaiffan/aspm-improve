import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tarfile
import yaml
from collections import Counter

QA: Path
ROOT_NAME = "ASPM-1.0.1-Enterprise-Delivery"


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def output_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def archive(path, directory, excluded=(), root_name=None):
    root_name = root_name or directory.name
    with tarfile.open(path, "w:gz", compresslevel=6) as tar:
        tar.add(directory, arcname=root_name, recursive=False)
        for f in sorted(directory.rglob("*")):
            relative = f.relative_to(directory)
            if str(relative) in excluded or "__pycache__" in relative.parts:
                continue
            tar.add(f, arcname=str(PurePosixPath(root_name, *relative.parts)), recursive=False)


def verify_archive(path, root, *, links=False):
    with tarfile.open(path) as tar:
        names = set()
        for member in tar:
            name = PurePosixPath(member.name)
            assert name.parts[0] == root and ".." not in name.parts and not name.is_absolute(), member.name
            assert member.name not in names, member.name
            names.add(member.name)
            if member.issym() and links:
                dest = PurePosixPath(member.linkname)
                parts = list(name.parent.parts)
                assert not dest.is_absolute()
                for item in dest.parts:
                    if item == "..":
                        parts.pop()
                        assert parts and parts[0] == root
                    else:
                        parts.append(item)
            else:
                assert member.isdir() or member.isfile(), member.name
        assert len(names) > 10
    return len(names)


def vulnerability_summary(file):
    d = json.loads(file.read_text())
    vulns = []
    secrets = []
    licenses = Counter()
    for group in d["Results"]:
        for v in group.get("Vulnerabilities", ()):
            vulns.append({key: v[key] for key in ("VulnerabilityID", "PkgName", "InstalledVersion",
                         "FixedVersion", "Severity", "Status", "PrimaryURL") if key in v})
        for s in group.get("Secrets", ()):
            secrets.append({"target": group["Target"], "rule": s["RuleID"], "line": s["StartLine"]})
        for l in group.get("Licenses", ()):
            licenses[l["Name"]] += 1
    return {
        "os": d.get("Metadata", {}).get("OS"),
        "image_config_id": d.get("Metadata", {}).get("ImageID"),
        "counts": dict(Counter(v["Severity"] for v in vulns)),
        "findings": vulns,
        "secret_detectors": secrets,
        "licenses": dict(licenses),
    }


def check_links(root):
    broken = []
    for source in root.rglob("*.md"):
        if source.is_symlink():
            continue
        for url in re.findall(r'(?<!\\)\]\(([^() \t\n]+)\)', source.read_text(encoding="utf-8")):
            if ":" in url or url.startswith("#"):
                continue
            target = (source.parent / url.split("#")[0]).resolve()
            if not target.exists() or not target.is_relative_to(root):
                broken.append(f"{source.relative_to(root)} -> {url}")
    if broken:
        raise ValueError("Broken documentation links: " + "\n".join(broken[:25]))


def main():
    global QA
    parser = argparse.ArgumentParser(description="Assemble and verify a portable ASPM delivery from a checkout and qualification outputs.")
    parser.add_argument("--inputs", type=Path, required=True, help="Directory containing rc-source, scans, pdf, evidence and images.json")
    parser.add_argument("repo", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--chart", type=Path, required=True)
    parser.add_argument("--evidence", required=True)
    args = parser.parse_args()
    QA = args.inputs.resolve()
    out = args.out.resolve()
    repo = args.repo.resolve()
    out.mkdir(parents=True, exist_ok=True)
    root = out / ROOT_NAME
    shutil.copytree(repo / "deploy/handover", root, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
    for directory in ("helm", "source", "provenance", "screenshots", "qualification/evidence"):
        (root / directory).mkdir(exist_ok=True, parents=True)
    manifest_path = root / "DELIVERY_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["evidence_sha"] = args.evidence

    chart_copy = root / "helm/aspm"
    shutil.copytree(repo / "deploy/helm/aspm", chart_copy, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    chart_path = root / manifest["chart"]
    shutil.copy2(args.chart, chart_path)
    manifest["chart_sha256"] = digest(chart_path)
    with tarfile.open(chart_path) as chart:
        for member in chart:
            assert member.isfile() or member.isdir()
            if member.isfile():
                actual = chart.extractfile(member).read()
                expected = (root / "helm" / member.name).read_bytes()
                if member.name == "aspm/Chart.yaml":
                    assert yaml.safe_load(actual) == yaml.safe_load(expected), member.name
                else:
                    assert actual == expected, member.name

    scans = QA / "scans"
    summary = {image: vulnerability_summary(scans / f"rc-{image}.scan.json") for image in ("django", "nginx")}
    for image in summary:
        assert not summary[image]["secret_detectors"], image
        shutil.copy2(scans / f"rc-{image}.cdx.json", root / f"provenance/{image}.cyclonedx.json")
    source_scan = vulnerability_summary(scans / "source.scan.json")
    exclusions = sorted({item["target"] for item in source_scan["secret_detectors"]})
    assert all(name.startswith("unittests/scans/") for name in exclusions)
    exclusions = sorted(set(exclusions) | {"unittests/scans/sonarqube/sonar.html"})
    (root / "source/EXCLUDED_FIXTURES.txt").write_text("\n".join(exclusions) + "\n", encoding="utf-8")
    source_path = root / manifest["source"]
    source_root = QA / "rc-source"
    assert (source_root / ".aspm-source-revision").read_text().strip() == manifest["application_sha"]
    archive(source_path, source_root, set(exclusions), "aspm-1.0.1-source")
    verify_archive(source_path, "aspm-1.0.1-source", links=True)
    manifest["source_sha256"] = digest(source_path)
    output_json(root / "provenance/TRIVY_SUMMARY.json", summary)
    output_json(root / "provenance/SOURCE_SCAN_SUMMARY.json", {
        "excluded_source_paths": exclusions, "vulnerability_counts": source_scan["counts"],
        "findings": source_scan["findings"], "detector_count_before_exclusion": len(source_scan["secret_detectors"]),
    })
    shutil.copy2(QA / "images.json", root / "provenance/IMAGES.json")
    shutil.copy2(QA / "pdf/ASPM-1.0.1-Deployment-and-Operations-Guide.pdf", root / "docs")
    evidence = root / "qualification/evidence"
    for f in sorted((QA / "evidence").glob("*")):
        if f.is_file():
            shutil.copy2(f, evidence / f.name)
    for picture in ("classic.png", "commit.png", "login.png", "classic-report.png", "finding-320.png"):
        current = QA / "live-rc" / picture
        previous = QA / "live" / picture
        historical = repo / "enterprise-report/aspm-ha-stabilization/screenshots" / {
            "classic.png": "after-classic-1440.png", "commit.png": "after-commit-390-dark.png",
            "login.png": "after-login-1440.png", "classic-report.png": "after-classic-report-viewer-1920.png",
            "finding-320.png": "after-findings-320.png",
        }[picture]
        for candidate in (current, previous, historical):
            if candidate.exists():
                shutil.copy2(candidate, root / "screenshots" / picture)
                break
    output_json(manifest_path, manifest)
    check_links(root)
    checksums = root / "SHA256SUMS"
    records = []
    for f in sorted(root.rglob("*")):
        if f.is_file() and f != checksums:
            assert not f.is_symlink()
            records.append((digest(f), "./" + str(f.relative_to(root))))
            if f.suffix == ".sh":
                assert f.stat().st_mode & stat.S_IXUSR, f
    checksums.write_text("".join(f"{sha}  {path}\n" for sha, path in records), encoding="utf-8")
    package = out / (ROOT_NAME + ".tar.gz")
    archive(package, root)
    members = verify_archive(package, ROOT_NAME)
    (out / (package.name + ".sha256")).write_text(f"{digest(package)}  {package.name}\n", encoding="utf-8")
    print(f"{package}: {members} members, {len(records)} checksums, {package.stat().st_size} bytes")


if __name__ == "__main__":
    main()
