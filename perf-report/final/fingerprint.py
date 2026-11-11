#!/usr/bin/env python3
"""Read-only, constant-memory fingerprints; run between load phases, not during them."""
import argparse
import json
import subprocess
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--reference',default='dd_round4_seed')
parser.add_argument('--databases')
args=parser.parse_args()
if args.databases is None:args.databases='source,'+args.reference
sql="""SELECT json_build_object('findings',count(*),'original_ids',count(*) FILTER (WHERE id<=1000000),
'fixture_ids',count(*) FILTER (WHERE id>1000000),'sum_ids',sum(id)::text,
'rows_xor',bit_xor(hashtextextended(f::text,0))::text,'max_updated',max(updated),
'deduplication',(SELECT enable_deduplication FROM dojo_system_settings ORDER BY id LIMIT 1),
'database_bytes',pg_database_size(current_database())) FROM dojo_finding f"""
rows={}
for database in args.databases.split(','):
    command=['docker','exec','-e','R4_FP_SQL='+sql,'-e','R4_FP_DB='+('' if database=='source' else database),'django-defectdojo-postgres-1','sh','-c',
             'PGOPTIONS="-c default_transaction_read_only=on -c statement_timeout=120000 -c TimeZone=UTC -c DateStyle=ISO,MDY" psql -X -U "$POSTGRES_USER" -d "${R4_FP_DB:-$POSTGRES_DB}" -Atc "$R4_FP_SQL"']
    rows[database]=json.loads(subprocess.check_output(command,text=True))
args.output.write_text(json.dumps(rows,indent=2)+'\n')
if 'source' in rows and args.reference in rows:
    assert rows['source']['findings']==1000168 and rows['source']['original_ids']==1000000
    assert all(rows['source'][key]==rows[args.reference][key] for key in ('findings','sum_ids','rows_xor','max_updated','deduplication'))
print('Fingerprint checks passed; finding rows match the pre-benchmark snapshot' if 'source' in rows and args.reference in rows else 'Fingerprints recorded; write-copy rows are expected to differ from the seed')
