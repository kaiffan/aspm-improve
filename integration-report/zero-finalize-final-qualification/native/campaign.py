"""Deploy an owned Linux AMD64 lab, seal a 1M snapshot, and run fresh cohorts."""
# ruff: noqa
import argparse
import gzip
import hashlib
import json
import math
import os
import random
import re
import secrets
import shutil
import subprocess as sp
import sys
import threading
import time
import types
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from build import A, B, host, output

ROOT=Path(__file__).resolve().parent
URL="http://127.0.0.1:48115"
GIB=1024**3
RESERVE=6*GIB
BUDGET={"seed":6*GIB,"archive":4*GIB,"one_restore":6*GIB,"WAL":5*GIB,"images_build":10*GIB,
        "observations_indexes_expected":3*GIB,"reports_and_raw":5*GIB,"additional_margin":6*GIB}
STEPS=[("A",1),("B",1),("B",2),("A",2),("A",3),("B",3)]
SERVICES=("nginx","uwsgi","worker","beat","valkey")
SLO={"import":110,"open":60,"create":5,"export":70}


def check_frozen():
    lock=json.loads((ROOT/"workload-lock.json").read_text())
    for name,digest in lock.items():
        assert hashlib.sha256((ROOT/"frozen"/name).read_bytes()).hexdigest()==digest,name
    assert lock["mixed.cjs"]=="b97f22d2bd17caefb8ea9e8528930d8408df05d1abb5ef14a3d5d2e8670ea2ae"


def save(path,data):
    with path.open("x",encoding="utf-8") as file:
        file.chmod(0o600)
        json.dump(data,file,indent=2,default=str)
        file.write("\n")


class Stand:
    def __init__(self,path,info):
        self.root=path.resolve()
        self.info=info
        self.raw=self.root/"raw"
        self.telemetry=self.root/"telemetry"
        self.private=self.root/"owner.json"
        self.images=json.loads((self.root/"images.json").read_text())
        if (self.images["A"]["sha"],self.images["B"]["sha"])!=(A,B):
            raise RuntimeError("Unexpected image source revisions.")
        self.owner=json.loads(self.private.read_text()) if self.private.exists() else None
        self.variant="A"
        self.db="postgres"

    @property
    def project(self):
        return "zfq-"+self.owner["id"]

    def disk(self,required):
        paths=[self.root,Path(self.info["DockerRootDir"])]
        free={str(path):shutil.disk_usage(path).free for path in paths}
        if min(free.values())<required:
            raise RuntimeError(f"Disk guard: {free}, need {required} bytes")
        return free

    def initialize(self):
        if self.owner:
            raise RuntimeError("Stand already has an owner.")
        if self.info["NCPU"]<8 or self.info["MemTotal"]<24*GIB:
            raise RuntimeError("Allocate at least 8 vCPU and 24 GiB RAM to the test VM.")
        free=self.disk(sum(BUDGET.values())+RESERVE)
        self.owner={"id":secrets.token_hex(6),"password":secrets.token_hex(24),"secret":secrets.token_hex(32),"aes":secrets.token_urlsafe(24)}
        self.raw.mkdir(mode=0o700)
        self.telemetry.mkdir(mode=0o700)
        self.telemetry.chmod(0o777) # Mount is isolated by the owner-only parent directory.
        save(self.private,self.owner)
        cpu=Path("/proc/cpuinfo").read_text()
        save(self.raw/"host.json",{"platform":os.uname()._asdict(),"model_names":sorted(set(re.findall(r"^model name\s*:\s*(.+)$",cpu,re.M))),
           "docker_cpus":self.info["NCPU"],"docker_ram_bytes":self.info["MemTotal"],"free_bytes":free,"budget_bytes":BUDGET,
           "filesystems":output("df","-PT",str(self.root),self.info["DockerRootDir"]),"cpu_quota":Path("/sys/fs/cgroup/cpu.max").read_text() if Path("/sys/fs/cgroup/cpu.max").exists() else None})
        self.compose("up","-d","--wait","postgres")
        self.verify_images()
        self.ownership()
        self.io_probe()

    def io_probe(self):
        name=self.root/"io-probe.bin"
        start=time.monotonic()
        with name.open("xb") as file:
            for _ in range(128):
                file.write(os.urandom(1024*1024))
            file.flush()
            os.fsync(file.fileno())
        duration=time.monotonic()-start
        name.unlink()
        probe = """p=$(mktemp "$PGDATA/zfq-io.XXXXXX"); trap 'rm -f "$p"' EXIT; dd if=/dev/zero of="$p" bs=1M count=128 conv=fsync"""
        pgprobe = self.pg("sh", "-ec", probe, capture_output=True, text=True)
        save(self.raw/"io-preflight.json",{"filesystem":"state", "bytes":128*1024**2,"write_fsync_seconds":duration,
             "includes_generation":True,"postgres_volume_write_fsync":pgprobe.stderr})

    def env(self):
        o=self.owner
        img=self.images[self.variant]
        return {**os.environ,"QUAL_OWNER":o["id"],"QUAL_PASSWORD":o["password"],"QUAL_SECRET":o["secret"],"QUAL_AES":o["aes"],
                "QUAL_HOME":str(self.root),"QUAL_PACKAGE":str(ROOT),"QUAL_DB":self.db,"APP_IMAGE":img["app"]["tag"],
                "NGINX_IMAGE":img["nginx"]["tag"],"APP_SHA":img["sha"]}

    def compose(self,*args,**opts):
        return sp.run(["docker","compose","-p",self.project,"-f",str(ROOT/"compose.yml"),*args],env=self.env(),check=True,**opts)

    def ownership(self):
        if not self.owner or not re.fullmatch(r"[0-9a-f]{12}",self.owner["id"]):
            raise RuntimeError("Invalid owner.")
        labels=output("docker","ps","-aq","--filter","label=com.docker.compose.project="+self.project).splitlines()
        for cid in labels:
            actual=output("docker","inspect","-f",'{{index .Config.Labels "org.aspm.zfq.owner"}}',cid)
            assert actual==self.owner["id"],cid
        for name in ("pgdata","evidence","media"):
            result=sp.run(["docker","volume","inspect",self.project+"_"+name],capture_output=True,text=True)
            if result.returncode==0:
                assert json.loads(result.stdout)[0]["Labels"]["org.aspm.zfq.owner"]==self.owner["id"]

    def pg(self,*args,**opts):
        return self.compose("exec","-T","postgres",*args,**opts)

    def sql(self,sql,db="postgres"):
        result=self.pg("psql","-XqAt","-v","ON_ERROR_STOP=1","-U","zfq","-d",db,"-c",sql,capture_output=True,text=True)
        return result.stdout.strip()

    def fingerprint(self,db):
        statement="COPY (SELECT id,encode(sha256(convert_to(f::text,'UTF8')),'hex') FROM dojo_finding f WHERE id<=1000000 ORDER BY id) TO STDOUT"
        cmd=["docker","compose","-p",self.project,"-f",str(ROOT/"compose.yml"),"exec","-T","-e",
             "PGOPTIONS=-c TimeZone=UTC -c DateStyle=ISO,MDY -c default_transaction_read_only=on","postgres",
             "psql","-XqAt","-v","ON_ERROR_STOP=1","-U","zfq","-d",db,"-c",statement]
        digest=hashlib.sha256()
        with sp.Popen(cmd,env=self.env(),stdout=sp.PIPE) as process:
            for block in iter(lambda:process.stdout.read(1024*1024),b""):
                digest.update(block)
            assert process.wait()==0
        return {"count":int(self.sql("SELECT count(*) FROM dojo_finding WHERE id<=1000000",db)),"sha256":digest.hexdigest()}

    def database(self,name):
        assert re.fullmatch(r"zfq_"+self.owner["id"]+r"_(proof|run)",name) or name in {"aspm_acceptance_seed","zf_native_load"}
        assert self.sql(f"SELECT count(*) FROM pg_database WHERE datname='{name}'")=="0"
        self.sql(f'CREATE DATABASE "{name}"')
        self.sql(f"""COMMENT ON DATABASE "{name}" IS 'ZQF:{self.owner["id"]}'""")
        return name

    def drop_owned(self,name):
        assert re.fullmatch(r"zfq_"+self.owner["id"]+r"_(proof|run)",name)
        self.ownership()
        assert self.sql(f"SELECT shobj_description(oid,'pg_database') FROM pg_database WHERE datname='{name}'")=="ZQF:"+self.owner["id"]
        self.sql(f'DROP DATABASE "{name}"')

    def app_script(self,source):
        self.compose("run","--rm","--no-deps","-T","--entrypoint","python","uwsgi","manage.py","shell",
                     "--no-imports","-c","import sys; exec(sys.stdin.read())",input=source,text=True)

    def seed(self):
        self.ownership()
        self.disk(sum(BUDGET.values())-BUDGET["images_build"]+RESERVE)
        self.db=self.database("aspm_acceptance_seed")
        self.compose("up","-d","valkey")
        self.compose("run","--rm","--no-deps","-T","--entrypoint","/entrypoint-initializer.sh","uwsgi")
        self.app_script((ROOT/"frozen"/"seed_dataset.py").read_text())
        self.app_script((ROOT/"seed_accounts.py").read_text())
        for name in ("accounts.json","identities.json"):
            result=self.compose("run","--rm","--no-deps","-T","--entrypoint","cat","uwsgi",
                                "/acceptance-telemetry/"+name,capture_output=True,text=True)
            save(self.root/name,json.loads(result.stdout))
        fingerprint=self.fingerprint(self.db)
        assert fingerprint["count"]==1_000_000
        assert self.sql("SELECT count(*) FROM dojo_test",self.db)=="2500"
        dump=self.root/"seed.dump"
        with dump.open("xb") as file:
            file.chmod(0o600)
            self.pg("pg_dump","-U","zfq","-Fc","--no-owner","--no-privileges",self.db,stdout=file)
        sha=digest(dump)
        proof=self.database("zfq_"+self.owner["id"]+"_proof")
        self.restore(proof,dump)
        checked=self.fingerprint(proof)
        assert checked==fingerprint
        save(self.raw/"snapshot-restore.json",{"database":self.db,"fingerprint":fingerprint,"restore_fingerprint":checked,
             "dump_sha256":sha,"dump_bytes":dump.stat().st_size,"database_bytes":int(self.sql(f"SELECT pg_database_size('{self.db}')"))})
        self.drop_owned(proof)
        self.compose("stop","valkey")

    def restore(self,name,dump):
        with dump.open("rb") as file:
            self.pg("pg_restore","-U","zfq","--exit-on-error","--no-owner","--no-privileges","-d",name,stdin=file)
        self.sql("ANALYZE",name)

    def shutdown(self):
        self.ownership()
        self.compose("stop",*SERVICES)

    def cohort(self,variant,family,repeat):
        self.ownership()
        seal=json.loads((self.raw/"snapshot-restore.json").read_text())
        dump=self.root/"seed.dump"
        assert digest(dump)==seal["dump_sha256"]
        self.disk(RESERVE+seal["database_bytes"]+8*GIB)
        self.variant=variant
        self.db=self.database("zfq_"+self.owner["id"]+"_run")
        self.restore(self.db,dump)
        assert self.fingerprint(self.db)==seal["fingerprint"]
        # Stopping Valkey unmounts its tmpfs. Remove just this verified owner's container for a cold broker/cache.
        self.compose("rm","-sf","valkey")
        label=f"{family}-{variant}-r{repeat}"
        try:
            self.verify_images()
            self.compose("up","-d","--force-recreate",*SERVICES)
            self.ready()
            if family=="core9":
                for level in ((1,5,10,15,25) if repeat==1 else (15,25)):
                    self.core(f"{label}-c{level}",level)
            else:
                self.acceptance(label,variant,repeat)
            assert self.fingerprint(self.db)==seal["fingerprint"], "Protected original Finding changed"
            save(self.raw/(label+".integrity.json"),{"protected_findings":seal["fingerprint"],"restored_identically":True,
                "business_outcomes_validated":True,"source_sha":self.images[variant]["sha"]})
        finally:
            self.shutdown()
        self.drop_owned(self.db)

    def verify_images(self):
        for service in ("app","nginx"):
            entry=self.images[self.variant][service]
            actual=json.loads(output("docker","image","inspect",entry["tag"]))[0]
            assert actual["Id"]==entry["id"] and actual["Architecture"]=="amd64"

    def ready(self):
        for _ in range(100):
            try:
                with urllib.request.urlopen(URL+"/login?force_login_form",timeout=2) as result:
                    if result.status==200:
                        return
            except OSError:
                pass
            time.sleep(1)
        raise RuntimeError("Gateway readiness timed out.")

    def pg_metrics(self):
        raw=self.sql("""SELECT json_build_object('wal',pg_current_wal_lsn(),
            'db',(SELECT row_to_json(d) FROM pg_stat_database d WHERE datname=current_database()),
            'io',(SELECT json_agg(i) FROM pg_stat_io i),
            'sql',(SELECT json_build_object('calls',sum(calls),'plan_ms',sum(total_plan_time),'exec_ms',sum(total_exec_time),
                       'blocks_read',sum(shared_blks_read),'blocks_hit',sum(shared_blks_hit),'wal_bytes',sum(wal_bytes))
                   FROM pg_stat_statements WHERE dbid=(SELECT oid FROM pg_database WHERE datname=current_database())))""",self.db)
        return json.loads(raw)

    def sample(self):
        ids=self.compose("ps","-q",capture_output=True,text=True).stdout.split()
        stats=output("docker","stats","--no-stream","--format","{{json .}}",*ids)
        cgroups={}
        for service in ("postgres","uwsgi","worker"):
            cid=self.compose("ps","-q",service,capture_output=True,text=True).stdout.strip()
            cgroups[service]={}
            for filename in ("cpu.stat","memory.peak","io.stat"):
                result=sp.run(["docker","exec",cid,"cat","/sys/fs/cgroup/"+filename],capture_output=True,text=True)
                cgroups[service][filename]=result.stdout.strip() if result.returncode==0 else None
        return {"at":time.time(),"containers":[json.loads(row) for row in stats.splitlines()],"cgroups":cgroups,
                "free_bytes":self.disk(RESERVE)}

    def measure(self,label,run):
        before=self.pg_metrics()
        start=time.monotonic()
        done=threading.Event()
        resource_error=[]
        self.stop=threading.Event()
        def collect():
            path=self.raw/(label+".resources.jsonl")
            with path.open("x") as file:
                while not done.is_set():
                    try:
                        file.write(json.dumps(self.sample())+"\n"); file.flush()
                    except Exception as error:
                        resource_error.append(str(error));self.stop.set();return
                    done.wait(5)
        th=threading.Thread(target=collect)
        th.start()
        try:
            result=run()
        finally:
            done.set()
            th.join()
            after=self.pg_metrics()
            wal=int(self.sql(f"SELECT pg_wal_lsn_diff('{after['wal']}','{before['wal']}')::bigint",self.db))
            save(self.raw/(label+".metrics.json"),{"before":before,"after":after,"wal_bytes":wal,
                 "duration_s":time.monotonic()-start,"resource_guard_errors":resource_error})
        assert not resource_error,resource_error
        return result

    def zero_finalize(self,fixture_dir,rows):
        self.ownership()
        self.disk(RESERVE+3*GIB)
        self.variant="B"
        self.verify_images()
        self.db=self.database("zf_native_load")
        self.compose("up","-d","valkey")
        try:
            self.compose("run","--rm","--no-deps","-T","--entrypoint","/entrypoint-initializer.sh","uwsgi")
            self.sql("CREATE EXTENSION IF NOT EXISTS pg_stat_statements",self.db)
            self.app_script('import os\nos.environ["ZF_LOAD_CREDENTIALS"]="/acceptance-telemetry/zfq-load-private.json"\n'+
                (ROOT.parent/"scripts/provision_load.py").read_text())
            self.compose("up","-d","--force-recreate",*SERVICES)
            self.ready()
            cmd=["docker","compose","-p",self.project,"-f",str(ROOT/"compose.yml"),"run","--rm","--no-deps","-T",
                 "-v",str(fixture_dir.resolve())+":/fixtures:ro","-e","ZF_LOAD_CREDENTIALS=/acceptance-telemetry/zfq-load-private.json",
                 "--entrypoint","python","uwsgi","/qualification-scripts/load.py","--url","http://nginx:8080",
                 "--fixtures","/fixtures","--output","/acceptance-telemetry/zfq-load.json","--rows",str(rows)]
            self.measure("zero-finalize-load",lambda:sp.run(cmd,env=self.env(),check=True,timeout=900))
            result=self.compose("run","--rm","--no-deps","-T","--entrypoint","cat","uwsgi",
                                "/acceptance-telemetry/zfq-load.json",capture_output=True,text=True)
            save(self.raw/"zero-finalize-load.json",json.loads(result.stdout))
        finally:
            self.shutdown()

    def core(self,label,level):
        mock=types.ModuleType("lab")
        mock.load=lambda:{"active_database":self.db,"port":48115}
        mock.PRIVATE=self.root
        mock.OUT=self.root
        sys.modules["lab"]=mock
        sys.path.insert(0,str(ROOT/"frozen"))
        from http_driver import Driver,summary
        plan=json.loads((ROOT/"frozen/core9-plan.json").read_text())
        assert list(plan["weights"].values())==[30,15,10,10,10,5,10,5,5]
        schedule=[case for case,weight in zip(plan["cases"],plan["weights"].values(),strict=True) for _ in range(weight)]*3
        random.Random(35100101).shuffle(schedule)
        warm=Driver(label+"-warm")
        for i,case in enumerate(plan["cases"]):
            assert warm.read(case,i)["valid"]
        def run():
            driver=Driver(label,self.stop)
            started=time.monotonic()
            with ThreadPoolExecutor(max_workers=level) as pool:
                def read(item):
                    try:
                        return driver.read(item[1],item[0])
                    except Exception as error:
                        return {"case":item[1]["id"],"valid":False,"error":str(error)}
                rows=list(pool.map(read,enumerate(schedule)))
            duration=time.monotonic()-started
            save(self.raw/(label+".json"),{"level":level,"summary":summary(rows,duration),"samples":rows})
            assert len(rows)==300 and all(row["valid"] for row in rows)
        self.measure(label,run)

    def acceptance(self,label,variant,repeat):
        output_file=self.raw/(label+".json")
        config={"run":label,"variant":variant,"repeat":repeat,"seed":35100101,"vus":10,"blocks":10,"think_ms":1000,
          "readonly_warmup":True,"database":self.db,"url":URL,"accounts":str(self.root/"accounts.json"),
          "telemetry":str(self.telemetry),"scans":str(ROOT/"frozen/scans"),"artifacts":str(self.raw/(label+"-reports")),
          "output":str(output_file),"stop_file":str(self.root/(label+".stop")),"start_file":str(self.root/(label+".start")),
          "scan_type_id":int(self.sql("SELECT id FROM dojo_test_type WHERE name='ZAP Scan' LIMIT 1",self.db))}
        config_path=self.root/(label+".json")
        save(config_path,config)
        log=self.raw/(label+".log")
        with log.open("x") as file, sp.Popen(["node",str(ROOT/"frozen/mixed.cjs"),str(config_path)],stdout=file,stderr=sp.STDOUT) as process:
            try:
                warm_deadline=time.monotonic()+180
                ready=Path(str(output_file)+".ready.json")
                while not ready.exists():
                    assert process.poll() is None and time.monotonic()<warm_deadline, "Acceptance browser warmup failed"
                    time.sleep(.5)
                def run():
                    Path(config["start_file"]).touch()
                    deadline=time.monotonic()+1800
                    while process.poll() is None and time.monotonic()<deadline and not self.stop.is_set():
                        time.sleep(.5)
                    assert process.poll()==0, "Acceptance failed or stopped"
                self.measure(label,run)
            finally:
                if process.poll() is None:
                    Path(config["stop_file"]).touch()
                    process.terminate()
                    try:
                        process.wait(timeout=20)
                    except sp.TimeoutExpired:
                        process.kill()
                        process.wait()
        result=json.loads(output_file.read_text())
        assert not result["stopped"]
        samples=result["samples"]
        assert len(samples)==400 and all(row["valid"] for row in samples)
        p90={}
        for key in SLO:
            values=sorted(r["acceptance_ms"]/1000 for r in samples if r["operation"]==key)
            assert len(values)==100
            p90[key]=values[math.ceil(.9*len(values))-1]
        row=self.sql("""SELECT json_build_object('findings',(SELECT count(*) FROM dojo_finding WHERE id>1000000),
             'duplicates',(SELECT count(*) FROM dojo_finding WHERE id>1000000 AND duplicate),
             'tests',(SELECT count(*) FROM dojo_test WHERE id>2500),
             'evidence',(SELECT count(*) FROM dojo_burprawrequestresponse b JOIN dojo_finding f ON b.finding_id=f.id WHERE f.test_id>2500))""",self.db)
        business=json.loads(row)
        assert business["findings"]==40100 and business["tests"]==100 and business["duplicates"]==0 and business["evidence"]>=120000,business
        save(self.raw/(label+".slo.json"),{"p90_seconds":p90,"threshold_seconds":SLO,"business":business,
              "pass":all(p90[key]<=SLO[key] for key in SLO)})


def digest(path):
    with path.open("rb") as file:
        return hashlib.file_digest(file,"sha256").hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state",type=Path,required=True)
    parser.add_argument("command",choices=["plan","init","seed","core9","acceptance","load","stop"])
    parser.add_argument("--fixtures",type=Path)
    parser.add_argument("--rows",type=int,default=1500)
    args=parser.parse_args()
    check_frozen()
    if args.command=="plan":
        print(json.dumps({"budget_bytes":BUDGET,"additional_floor_bytes":RESERVE,
              "cohorts":STEPS,"acceptance_slo":SLO,"A":A,"B":B}))
        return
    info=host()
    stand=Stand(args.state,info)
    if args.command=="init":
        stand.initialize()
    elif args.command=="seed":
        stand.seed()
    elif args.command=="load":
        if not args.fixtures or not args.fixtures.is_dir() or not 1500<=args.rows<=10000:
            parser.error("load requires --fixtures and 1500–10000 observations")
        stand.zero_finalize(args.fixtures,args.rows)
    elif args.command=="stop":
        stand.shutdown()
        stand.compose("stop","postgres")
    else:
        for variant,repeat in STEPS:
            stand.cohort(variant,args.command,repeat)
        seal=json.loads((stand.raw/"snapshot-restore.json").read_text())
        assert stand.fingerprint("aspm_acceptance_seed")==seal["fingerprint"]


if __name__=="__main__":
    if not __debug__:
        raise SystemExit("Python assertions must be enabled.")
    main()
