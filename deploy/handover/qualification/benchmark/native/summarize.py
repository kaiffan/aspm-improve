"""Summarize only complete, provenance-matched native A/B cohorts."""
# ruff: noqa
import argparse
import json
import statistics
from pathlib import Path

from build import A, B

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state",type=Path,required=True)
    args=parser.parse_args()
    raw=args.state/"raw"
    def read(name):
        return json.loads((raw/name).read_text())
    core={}
    acceptance={}
    for tag,sha in (("A",A),("B",B)):
        integrity=[read(f"{family}-{tag}-r{repeat}.integrity.json")
                   for family in ("core9","acceptance") for repeat in (1,2,3)]
        assert all(row["source_sha"]==sha and row["restored_identically"] for row in integrity)
        assert all(row["protected_findings"]==integrity[0]["protected_findings"] for row in integrity)
        core[tag]={}
        for level in (1,5,10,15,25):
            runs=range(1,4) if level>=15 else (1,)
            values=[read(f"core9-{tag}-r{repeat}-c{level}.json")["summary"] for repeat in runs]
            assert all(value["errors"]==0 and value["n"]==300 for value in values)
            core[tag][level]={"samples":values,"median_p95_ms":statistics.median(v["p95_ms"] for v in values),
                              "median_rps":statistics.median(v["rps"] for v in values)}
        acceptance[tag]=[read(f"acceptance-{tag}-r{repeat}.slo.json") for repeat in (1,2,3)]
    print(json.dumps({"core9":core,"acceptance":acceptance,
           "all_acceptance_slos_met":all(row["pass"] for runs in acceptance.values() for row in runs),
           "review_required":"Inspect repeat variation, SQL, CPU, and I/O. No production status is inferred."},indent=2))

if __name__=="__main__":
    if not __debug__:
        raise SystemExit("Python assertions must be enabled.")
    main()
