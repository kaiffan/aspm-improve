import json
import os
import time
from pathlib import Path

end = time.monotonic() + int(os.environ["DD_RSS_DURATION"])
while time.monotonic() < end:
    workers = {}
    parents = set()
    for path in Path("/proc").glob("[0-9]*/status"):
        try:
            content = dict(line.split(":", 1) for line in path.read_text().splitlines() if ":" in line)
            if "uwsgi" in content["Name"].lower():
                workers[int(path.parent.name)] = int(content["VmRSS"].split()[0])
                parents.add(int(content["PPid"].strip()))
        except (FileNotFoundError, ProcessLookupError, KeyError, PermissionError):
            pass
    memory = [value for pid, value in workers.items() if pid not in parents]
    print(json.dumps({"at": time.time(), "workers": len(memory), "rss_max_kib": max(memory,default=0), "rss_sum_kib": sum(memory)}), flush=True)
    time.sleep(.4)
