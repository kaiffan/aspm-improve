"""Build and verify native unpublished A/B images from selected Git revisions."""
# ruff: noqa
import argparse
import json
import os
import platform
import subprocess as sp
import tarfile
import tempfile
from pathlib import Path

A = "19cd7b4129de52e75eabaf0e07739e4c2b682f8e"
B = "25da29aaff229d3a815e223d8af8bdc4ecca7c5e"

def output(*args):
    return sp.check_output(args, text=True).strip()

def host():
    if platform.system()!="Linux" or platform.machine() not in {"x86_64","amd64"}:
        raise SystemExit("Native Linux x86_64 required.")
    info=json.loads(output("docker","info","--format","{{json .}}"))
    if info["OSType"]!="linux" or info["Architecture"] not in {"x86_64","amd64"}:
        raise SystemExit("Native Linux AMD64 Docker daemon required.")
    if os.environ.get("DOCKER_HOST"):
        raise SystemExit("Select a local Unix socket context explicitly and unset DOCKER_HOST.")
    context=json.loads(output("docker","context","inspect",output("docker","context","show")))[0]
    if not context["Endpoints"]["docker"]["Host"].startswith("unix://"):
        raise SystemExit("A local Unix Docker socket is required for capacity checks.")
    return info

def verify(repo, sha, image):
    blobs={}
    for item in sp.check_output(["git","-C",str(repo),"ls-tree","-rz",sha,"dojo"]).split(b"\0"):
        if item:
            header,path=item.decode().split("\t",1)
            if path!="dojo/fixtures/readme.txt":  # Release Dockerfile deliberately removes this marker.
                blobs[path]=header.split()[2]
    verifier=r"""
import hashlib,json,pathlib,sys
for name, expected in json.load(sys.stdin).items():
 p=pathlib.Path('/app')/name
 data=str(p.readlink()).encode() if p.is_symlink() else p.read_bytes()
 assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() == expected, name
"""
    sp.run(["docker","run","--rm","-i","--network","none","--entrypoint","python",image,"-c",verifier],
           input=json.dumps(blobs),text=True,check=True)
    return len(blobs)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--state",type=Path,required=True)
    parser.add_argument("--plan",action="store_true")
    args=parser.parse_args()
    for sha in (A,B):
        output("git","-C",str(args.repo),"cat-file","-t",sha)
    inputs=["Dockerfile.django-debian","Dockerfile.nginx-alpine","requirements.txt","components","docker"]
    if output("git","-C",str(args.repo),"diff","--name-only",A,B,"--",*inputs):
        raise SystemExit("Build inputs differ. Review a common dependency image before qualification.")
    if args.plan:
        print(json.dumps({"A":A,"B":B,"common_runtime":True,"required_host":"native Linux AMD64","push":False}))
        return
    from shutil import disk_usage
    info=host()
    state=args.state.resolve()
    for path in [state.parent,Path(info["DockerRootDir"])]:
        if disk_usage(path).free<45*1024**3:
            raise SystemExit("Native build requires 45 GiB free on state and Docker filesystems.")
    state.mkdir(mode=0o700,exist_ok=False)
    images={}
    with tempfile.TemporaryDirectory(dir=state) as tmp:
        scope=Path(tmp)
        for variant,sha in (("A",A),("B",B)):
            source=scope/variant
            source.mkdir()
            archive=scope/(variant+".tar")
            with archive.open("wb") as sink:
                sp.run(["git","-C",str(args.repo),"archive",sha],stdout=sink,check=True)
            with tarfile.open(archive) as tar:
                tar.extractall(source,filter="data")
            archive.unlink()
            app="local/zfq-app:"+sha[:12]
            nginx="local/zfq-nginx:"+sha[:12]
            for tag,filename in [(app,"Dockerfile.django-debian"),(nginx,"Dockerfile.nginx-alpine")]:
                sp.run(["docker","build","--platform","linux/amd64","--target","release","-f",filename,
                        "--label","org.opencontainers.image.revision="+sha,"-t",tag,"."],cwd=source,check=True)
            values={}
            for label,tag in [("app",app),("nginx",nginx)]:
                image=json.loads(output("docker","image","inspect",tag))[0]
                assert image["Architecture"]=="amd64" and image["Os"]=="linux"
                assert image["Config"]["Labels"]["org.opencontainers.image.revision"]==sha
                values[label]={"tag":tag,"id":image["Id"],"layers":image["RootFS"]["Layers"]}
            values["sha"]=sha
            values["dojo_blobs"]=verify(args.repo,sha,app)
            packages=json.loads(output("docker","run","--rm","--network","none","--entrypoint","python",app,
                                       "-m","pip","list","--format=json"))
            values["python_packages"]=sorted(packages,key=lambda package:package["name"].lower())
            images[variant]=values
    assert images["A"]["python_packages"]==images["B"]["python_packages"], "Image dependencies differ."
    (state/"images.json").write_text(json.dumps(images,indent=2)+"\n")

if __name__=="__main__":
    if not __debug__:
        raise SystemExit("Python assertions must be enabled.")
    main()
