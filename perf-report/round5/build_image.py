"""Export immutable source to an empty context; build without touching any DB."""
import argparse
import io
import subprocess
import tarfile
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--sha',default='c6a6144ed93b83adb1fd4ea9daa2c5e417ecea37')
p.add_argument('--context',type=Path,required=True)
p.add_argument('--base',default='dd-api-perf-base:3.5.100')
p.add_argument('--image',default='dd-r5-final:3.5.100')
a=p.parse_args();a.context.mkdir(parents=True,exist_ok=True)
if any(a.context.iterdir()):p.error('Use an empty build context; existing files are preserved')
with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',a.sha,'dojo']))) as archive:
    archive.extractall(a.context,filter='tar')
(a.context/'Dockerfile').write_text('ARG BASE\nFROM ${BASE}\nUSER root\nRUN rm -rf /app/dojo\nCOPY --chown=1001:1001 dojo /app/dojo\nUSER 1001\n')
subprocess.run(['docker','build','--build-arg','BASE='+a.base,'-t',a.image,str(a.context)],check=True)
