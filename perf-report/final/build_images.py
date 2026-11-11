#!/usr/bin/env python3
"""Build release-source variants using one operator-supplied pinned runtime image."""
import argparse
from contextlib import nullcontext
from pathlib import Path
import subprocess
import tarfile
import tempfile

SOURCES={'original':'334bef02d65a74909fe976b22724526474d5a0f6','current':'20771ddc0bdfb4b763708f70e1cd6c131c3f6b5e','final':'70daa20757a9b5b99836343e50791a4de8c72fd0'}
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo',type=Path,required=True)
parser.add_argument('--contexts-dir',type=Path)
parser.add_argument('--base-image',required=True,help='Pinned shared local runtime; do not use a floating latest tag')
args=parser.parse_args()
for variant,sha in SOURCES.items():
    manager = nullcontext(str(args.contexts_dir/variant)) if args.contexts_dir else tempfile.TemporaryDirectory(prefix='dd-final-build-')
    with manager as directory:
        context=Path(directory)
        context.mkdir(parents=True,exist_ok=True)
        if (context/"dojo").exists():raise RuntimeError("Build context already exists; use an empty output directory")
        with (context/'source.tar').open('wb') as stream:
            subprocess.run(['git','-C',str(args.repo),'archive','--format=tar',sha,'dojo'],check=True,stdout=stream)
        with tarfile.open(context/'source.tar') as archive:
            archive.extractall(context,filter='tar')
        (context/'source.tar').unlink()
        (context/'Dockerfile').write_text('ARG BASE\nFROM ${BASE}\nUSER root\nRUN rm -rf /app/dojo\nCOPY --chown=1001:1001 dojo /app/dojo\nUSER 1001\n')
        subprocess.run(['docker','build','--build-arg','BASE='+args.base_image,'-t','dd-final-'+variant+':3.5.100',str(context)],check=True)
