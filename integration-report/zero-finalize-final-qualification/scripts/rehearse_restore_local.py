"""Exercise the production-format PostgreSQL archive/restore tools on owned synthetic data."""
# ruff: noqa
import hashlib
import json
import re
import secrets
import subprocess as sp
import tempfile
import time
from pathlib import Path

PG = "aspm-zero-finalize-postgres-1"
SOURCE = "aspm_zero_ab_a"
target = "zf_restore_proof_"+secrets.token_hex(5)
assert __debug__ and re.fullmatch(r"zf_restore_proof_[0-9a-f]{10}",target)
assert sp.check_output(["docker","inspect","-f",'{{index .Config.Labels "com.docker.compose.project"}}',PG],text=True).strip()=="aspm-zero-finalize"

def pg(*args,**kwargs):
    script = 'tool=$1; shift; exec "$tool" -U "$POSTGRES_USER" "$@"'
    command = ["docker", "exec", "-i", PG, "sh", "-ec", script, "sh", *args]
    return sp.run(command,check=True,**kwargs)

def sql(db,statement):
    return pg("psql","-XqAt","-v","ON_ERROR_STOP=1","-d",db,"-c",statement,capture_output=True,text=True).stdout.strip()

def fingerprint(db,table):
    assert table in {"dojo_finding","dojo_findingobservation","dojo_scanrun","dojo_generatedreport"}
    digest=hashlib.sha256()
    query=f"COPY (SELECT id,encode(sha256(convert_to(t::text,'UTF8')),'hex') FROM {table} t ORDER BY id) TO STDOUT"
    # This small rehearsal is constrained separately from the 1M streaming native check.
    result=pg("psql","-XqAt","-v","ON_ERROR_STOP=1","-d",db,"-c",query,capture_output=True)
    digest.update(result.stdout)
    return {"rows":len(result.stdout.splitlines()),"sha256":digest.hexdigest()}

assert int(sql("postgres",f"SELECT pg_database_size('{SOURCE}')")) < 100*1024**2
assert sql("postgres",f"SELECT count(*) FROM pg_database WHERE datname='{target}'")=="0"
sql("postgres",f"CREATE DATABASE {target}")
sql("postgres",f"COMMENT ON DATABASE {target} IS 'ZQF:local-restore-proof'")
with tempfile.TemporaryDirectory() as stage:
    archive=Path(stage)/"synthetic.dump"
    start=time.monotonic()
    with archive.open("wb") as file:
        pg("pg_dump","-Fc","--no-owner","--no-privileges",SOURCE,stdout=file)
    dump_seconds=time.monotonic()-start
    start=time.monotonic()
    with archive.open("rb") as file:
        pg("pg_restore","--exit-on-error","--no-owner","--no-privileges","-d",target,stdin=file)
    restored_seconds=time.monotonic()-start
    tables={table:{"source":fingerprint(SOURCE,table),"restored":fingerprint(target,table)}
            for table in ("dojo_finding","dojo_findingobservation","dojo_scanrun","dojo_generatedreport")}
    assert all(result["source"]==result["restored"] for result in tables.values())
    print(json.dumps({"passed":True,"lab_scope":"small synthetic ARM64 database","dump_bytes":archive.stat().st_size,
                     "dump_sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),"dump_seconds":dump_seconds,
                     "restore_seconds":restored_seconds,"tables":tables,"owned_target_retained":target}))
