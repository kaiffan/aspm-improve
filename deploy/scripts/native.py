"""Select this milestone's immutable A/B SHAs while reusing the frozen native campaign."""
# ruff: noqa: INP001, S607 -- standalone CLI helpers invoke installed git/helm tools
import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

BASELINE = "25da29aaff229d3a815e223d8af8bdc4ecca7c5e"
ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "integration-report/zero-finalize-final-qualification/native"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default=BASELINE, help="Full immutable baseline application SHA")
    parser.add_argument("--candidate", required=True, help="Full immutable application SHA, not a mutable branch")
    parser.add_argument("tool", choices=["build", "campaign", "summarize"])
    args, forwarded = parser.parse_known_args()
    for sha in (args.baseline, args.candidate):
        if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
            parser.error("A full lowercase 40-character SHA is required")
        subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", sha + "^{commit}"], check=True)
    build = load("build", KIT / "build.py")
    build.A = args.baseline
    build.B = args.candidate
    module = build if args.tool == "build" else load("enterprise_campaign", KIT / (args.tool + ".py"))
    sys.argv = [str(KIT / (args.tool + ".py")), *forwarded]
    module.main()


if __name__ == "__main__":
    if not __debug__:
        msg = "Python assertions must remain enabled"
        raise SystemExit(msg)
    main()
