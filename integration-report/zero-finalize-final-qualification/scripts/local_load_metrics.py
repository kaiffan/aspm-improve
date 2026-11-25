"""Run the local diagnostic and capture raw PostgreSQL and container counters."""
# ruff: noqa
import argparse
import json
import subprocess as sp
import threading
import time
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument("--compose",type=Path,required=True)
p.add_argument("--out",type=Path,required=True)
a=p.parse_args()
compose=["docker","compose","-p","zfq-load","-f",str(a.compose)]
pg="aspm-zero-finalize-postgres-1"


def text(*args):
    return sp.check_output(args,text=True).strip()


def sql(statement):
    return text("docker","exec","-e","ZQF_SQL="+statement,pg,"sh","-c",
                'psql -XqAt -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d zf_load -c "$ZQF_SQL"')


def snapshot():
    result=json.loads(sql("""SELECT json_build_object('database',to_jsonb(d),'wal',pg_current_wal_lsn(),
       'wal_statistics',(SELECT to_jsonb(w) FROM pg_stat_wal w),'io',(SELECT json_agg(i) FROM pg_stat_io i),
       'sizes',json_build_object('database',pg_database_size(current_database()),'findings',pg_total_relation_size('dojo_finding'),
       'observations',pg_total_relation_size('dojo_findingobservation'),'scans',pg_total_relation_size('dojo_scanrun')))
       FROM pg_stat_database d WHERE d.datname=current_database()"""))
    result["artifact_space"]=text(*compose,"exec","-T","http","du","-sb","/app/aspm-private")
    return result


def sample():
    cmd=["docker","stats","--no-stream","--format","{{json .}}",pg,"zfq-load-http-1","zfq-load-worker-1","zfq-load-zfq-queue-1"]
    rows=[json.loads(row) for row in text(*cmd).splitlines()]
    cgroups={}
    for service in [pg,"zfq-load-http-1","zfq-load-worker-1"]:
        cgroups[service]={}
        for filename in ("cpu.stat","memory.peak","io.stat"):
            row=sp.run(["docker","exec",service,"cat","/sys/fs/cgroup/"+filename],capture_output=True,text=True)
            cgroups[service][filename]=row.stdout.strip() if row.returncode==0 else None
    return {"at":time.time(),"stats":rows,"cgroups":cgroups}


assert text("docker","inspect","-f",'{{index .Config.Labels "org.aspm.zero-final-qualification.owner"}}',"zfq-load-worker-1")=="zfq-load"
before=snapshot()
samples=[sample()]
done=threading.Event()
errors=[]
def collect():
    while not done.wait(2):
        try:
            samples.append(sample())
        except sp.CalledProcessError as error:
            errors.append(error.returncode)
            return
start=time.monotonic()
worker=threading.Thread(target=collect)
worker.start()
try:
    result=sp.run([*compose,"exec","-T","-e","ZF_LOAD_CREDENTIALS=/tmp/zfq-load-r2.json","http","python","/zfq/load.py",
                   "--fixtures","/app/unittests/scans","--output","/zero-runtime/zfq-load-r2.json","--rows","1500"],
                  capture_output=True,text=True)
finally:
    done.set()
    worker.join()
duration=time.monotonic()-start
samples.append(sample())
after=snapshot()
wal=int(sql(f"SELECT pg_wal_lsn_diff('{after['wal']}','{before['wal']}')::bigint"))
a.out.write_text(json.dumps({"load_returncode":result.returncode,"duration_s":duration,"before":before,"after":after,
                            "wal_bytes_shared_cluster":wal,"samples":samples,"collector_errors":errors,
                            "postgres_is_shared_with_idle_lab_containers":True,"output":result.stderr[-1200:]},indent=2)+"\n")
result.check_returncode()
