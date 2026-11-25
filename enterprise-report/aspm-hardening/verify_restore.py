"""Compare source and restored database manifests with a private restored evidence tree."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_manifest", type=Path)
    parser.add_argument("restored_manifest", type=Path)
    parser.add_argument("restored_files", type=Path)
    args = parser.parse_args()
    source = json.loads(args.source_manifest.read_text())
    restored = json.loads(args.restored_manifest.read_text())
    if not source or source != restored:
        raise RuntimeError("Source and restored manifests did not match")
    root = args.restored_files.resolve()
    for name, expected in restored:
        path = (root / name).resolve()
        if not path.is_relative_to(root):
            raise RuntimeError("Manifest path escapes the restored evidence tree")
        with path.open("rb") as file:
            if hashlib.file_digest(file, "sha256").hexdigest() != expected:
                raise RuntimeError("Restored evidence checksum did not match database")
    print(json.dumps({"matching_references": len(restored), "file_checksums_match": True, "manifest_sha256": hashlib.sha256(json.dumps(restored).encode()).hexdigest()}, indent=2))


if __name__ == "__main__":
    main()
