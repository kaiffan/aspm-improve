import json
import os
import time
from pathlib import Path

end = time.monotonic() + int(os.environ["DD_RSS_DURATION"])
while time.monotonic() < end and not Path("/tmp/dd-r4-rss-stop").exists():
    workers = {}
    for path in Path("/proc").glob("[0-9]*/status"):
        try:
            content = dict(line.split(":", 1) for line in path.read_text().splitlines() if ":" in line)
            if content["Name"].strip().lower().startswith("uwsgiworker"):
                workers[int(path.parent.name)] = int(content["VmRSS"].split()[0])
        except (FileNotFoundError, ProcessLookupError, KeyError, PermissionError):
            pass
    memory = list(workers.values())
    print(json.dumps({"at": time.time(), "scope": "all_workers_by_procname", "pids_rss_kib": workers, "workers": len(memory), "rss_max_kib": max(memory,default=0), "rss_sum_kib": sum(memory)}), flush=True)
    time.sleep(.4)
