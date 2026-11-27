"""Execute each dashboard expression through Grafana's VictoriaMetrics datasource."""
# ruff: noqa: INP001
import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def check_panel(args, uid, panel):
    values = {key: getattr(args, key) for key in ("cluster", "environment", "namespace", "release")}
    findings = []
    for target in panel["targets"]:
        expr = re.sub(r"[$][{](\w+):regex[}]", lambda match: values.get(match[1], ".*"), target["expr"]).replace("$__rate_interval", "5m")
        suffix = "query_range" if target["range"] else "query"
        params = {"query": expr}
        if target["range"]:
            params.update(start=args.end - 900, end=args.end, step=30)
        url = f"{args.grafana}/api/datasources/proxy/uid/{args.datasource}/api/v1/{suffix}?" + urllib.parse.urlencode(params)
        try:
            with urllib.request.urlopen(url, timeout=12) as response:
                data = json.load(response)
            if data["status"] != "success":
                findings.append((target["refId"], "error", data.get("errorType", "query")))
                continue
            series = data["data"]["result"]
            found_data = any(value not in {"NaN", "+Inf", "-Inf"} for item in series
                             for _, value in (item.get("values") or [item["value"]]))
            findings.append((target["refId"], "data" if found_data else "no_data", len(series)))
        except urllib.error.HTTPError as error:
            findings.append((target["refId"], "error", error.read().decode()[:400]))
    return {"dashboard": uid, "panel": panel["id"], "title": panel["title"], "queries": findings}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--grafana", default="http://127.0.0.1:13000")
    parser.add_argument("--datasource", default="vm-local")
    parser.add_argument("--cluster", default="orbstack")
    parser.add_argument("--environment", default="test")
    parser.add_argument("--namespace", default="aspm-lab-monitoring")
    parser.add_argument("--release", default="aspm")
    parser.add_argument("--end", type=int, default=int(time.time()))
    args = parser.parse_args()
    directory = Path(__file__).resolve().parents[1] / "dashboards"
    dashboards = [json.loads(path.read_text()) for path in sorted(directory.glob("*.json"))]
    jobs = [(doc["uid"], panel) for doc in dashboards for panel in doc["panels"] if "targets" in panel]
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(lambda job: check_panel(args, *job), jobs))
    states = [state for result in results for _, state, _ in result["queries"]]
    print(json.dumps({"dashboards": len(dashboards), "panels": len(results), "queries": len(states),
                      "panels_with_data": sum(any(state == "data" for _, state, _ in row["queries"]) for row in results),
                      "query_errors": states.count("error"), "results": results}, ensure_ascii=False, indent=2))
    if "error" in states:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
