"""Finish diagnostics and tests sequentially after all HTTP suites have completed."""
import json
import subprocess
import sys
from pathlib import Path
R=Path(__file__).resolve().parent
files=[p for p in (R/'raw').glob('*-c*-*.json') if p.name.startswith(('mixed-','endpoints-'))]
assert len(files)==78,len(files)
for p in files:
    d=json.loads(p.read_text());assert not d['stopped'] and d['error_rate']==0,p
commands=[
 [sys.executable,str(R/'check_compatibility.py')],
 [sys.executable,str(R/'capture_profiles.py'),'--variants','round4,round5'],
 [sys.executable,str(R/'diagnose_sql.py')],
 [sys.executable,str(R/'capture_environment.py')],
 [sys.executable,str(R.parent/'final/fingerprint.py'),'--output',str(R/'fingerprint_after.json')],
 [sys.executable,str(R/'final_validate.py')],
 [sys.executable,str(R/'rank_sql.py'),str(R/'raw/diagnostic-r4-sql.jsonl'),str(R/'sql_ranking_r4.json')],
 [sys.executable,str(R/'analyze.py')],
]
for argv in commands:subprocess.run(argv,check=True)
