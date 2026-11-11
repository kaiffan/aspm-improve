"""Inherited resource guard; longer Docker-command timeout for laptop wake-up. No app settings changed."""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

output, stop, seconds = sys.argv[1:4]
web = sys.argv[4:] or ["dd35100-round2-uwsgi-round2-1"]
db = "django-defectdojo-postgres-1"
valkey = os.environ.get("DD_FINAL_VALKEY", "django-defectdojo-valkey-1")
worker = os.environ.get("DD_FINAL_WORKER", "django-defectdojo-celeryworker-1")
db_name = os.environ.get("DD_FINAL_DB", "")
redis_db = os.environ.get("DD_FINAL_REDIS_DB", "0")
# Discover the active app database rather than assuming the validation-copy name.
probe = subprocess.run(["docker", "exec", web[0], "python", "manage.py", "shell", "-c", "from django.db import connection; print('MONITOR_DB '+connection.settings_dict['NAME'])"], capture_output=True, text=True, timeout=25, check=True)
db_name = next(line[11:] for line in probe.stdout.splitlines() if line.startswith("MONITOR_DB "))

stat_sql = """
SELECT json_build_object('connections',numbackends,'blks_read',blks_read,'blks_hit',blks_hit,
 'temp_bytes',temp_bytes,'deadlocks',deadlocks,
 'active',(SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid() AND state='active'),
 'lock_wait',(SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock'),
 'io_wait',(SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='IO'),
 'long',(SELECT coalesce(json_agg(x),'[]') FROM (SELECT round(extract(epoch from clock_timestamp()-query_start)*1000) AS ms,
     wait_event_type AS wait, substring(lower(query) from 'from[[:space:]]+"?(dojo_[a-z0-9_]+)') AS relation
     FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()
     AND state='active' AND clock_timestamp()-query_start>interval '150 ms'
     ORDER BY query_start LIMIT 12) x))
FROM pg_stat_database WHERE datname=current_database()
"""

def call(argv, timeout=15):
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=True).stdout

def mem(value):
    match = re.search(r"([0-9.]+)([kKMG]?i?B)", value)
    size, unit = match.groups()
    factor = {"B": 1, "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3, "kB": 1000, "MB": 1000**2, "GB": 1000**3}
    return float(size) * factor[unit]

end = time.monotonic() + float(seconds)
first_swap = None
errors = 0
with open(output, "a", buffering=1) as stream:
    while time.monotonic() < end:
        sample = {"at": time.time(), "database": db_name}
        try:
            stats = [json.loads(line) for line in call(["docker","stats","--no-stream","--format","{{json .}}"]).splitlines()]
            sample["services"] = {x["Name"]:{"cpu":float(x["CPUPerc"].rstrip("%")), "memory_bytes":mem(x["MemUsage"])}
                                  for x in stats if x["Name"] in {*web, db, valkey, worker}}
            sample["containers_total_bytes"] = sum(mem(x["MemUsage"]) for x in stats)
            sample["pg"] = json.loads(call(["docker","exec","-e","R3_STATS_SQL="+stat_sql,"-e","DD_FINAL_DB="+db_name,db,"sh","-c",
                                            'psql -X -U "$POSTGRES_USER" -d "${DD_FINAL_DB:-$POSTGRES_DB}" -Atc "$R3_STATS_SQL"']))
            sample["celery_queue"] = int(call(["docker","exec",valkey,"valkey-cli","-n",redis_db,"LLEN","celery"]).strip())
            power = call(["pmset", "-g", "batt"]).splitlines()[0]
            sample["power_source"] = "AC" if "'AC Power'" in power else "Battery"
            power_config = call(["pmset", "-g", "custom"])
            ac_config = power_config.split("AC Power:", 1)[-1]
            low_power = re.search(r"lowpowermode\s+(\d+)", ac_config)
            sample["ac_low_power_mode"] = int(low_power.group(1)) if low_power else None
            if sample["power_source"] != "AC" or sample["ac_low_power_mode"] != 0:
                sample["stop"] = "power configuration changed"
            swap = call(["sysctl","-n","vm.swapusage"])
            sample["swap_mib"] = float(re.search(r"used = ([0-9.]+)M",swap).group(1))
            if first_swap is None:
                first_swap = sample["swap_mib"]
            pressure = call(["memory_pressure","-Q"])
            sample["host_free_percent"] = int(re.search(r"memory free percentage: (\d+)",pressure).group(1))
            bad = call(["docker","inspect","--format","{{.State.OOMKilled}} {{.State.Running}}",*web,db])
            if bad.splitlines() != ["false true"] * (len(web)+1):
                sample["stop"] = "container stopped or OOM"
            elif sample["containers_total_bytes"] > 7.2 * 1024**3 or sample["host_free_percent"] < 12:
                sample["stop"] = "memory threshold"
            elif sample["swap_mib"] - first_swap > 384 and sample["host_free_percent"] < 24:
                sample["stop"] = "swap growth and memory pressure"
            errors = 0
        except (subprocess.SubprocessError, ValueError, AttributeError, KeyError) as error:
            sample["monitor_error"] = type(error).__name__
            errors += 1
            if errors >= 3:
                sample["stop"] = "monitor unavailable"
        stream.write(json.dumps(sample)+"\n")
        if "stop" in sample:
            Path(stop).touch()
            break
        time.sleep(1.8)
