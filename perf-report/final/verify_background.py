#!/usr/bin/env python3
"""Validate real import outcomes in copies without reading evidence payloads."""
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
output={}
normalized={}
manifest={r['variant']:r for r in json.loads((ROOT/'background_manifest.json').read_text())}
for variant in ('original','current','final'):
    groups=[];normalized[variant]=[]
    for phase in ('idle','loaded'):
        steps=json.loads((ROOT/'raw'/f'import-{variant}-{phase}.json').read_text())
        assert len(steps)==9 and all(r['status']==201 and r['deduplication_complete'] for r in steps)
        normalized[variant]+=[{k:r[k] for k in ('phase','rep','operation','status','deduplication_complete','statistics')} for r in steps]
        for rep in (1,2,3):
            selected=[r for r in steps if r['rep']==rep]
            primary=int(selected[0]['test']);peer=int(selected[2]['test'])
            groups.append((phase,rep,primary,peer))
    sql='WITH batches(phase,rep,primary_id,peer_id) AS (VALUES '+','.join(f"('{phase}',{rep},{primary},{peer})" for phase,rep,primary,peer in groups)+''')
SELECT json_agg(json_build_object('phase',phase,'rep',rep,
'primary_findings',(SELECT count(*) FROM dojo_finding WHERE test_id=primary_id),
'primary_active',(SELECT count(*) FROM dojo_finding WHERE test_id=primary_id AND active),
'peer_findings',(SELECT count(*) FROM dojo_finding WHERE test_id=peer_id),
'peer_duplicates',(SELECT count(*) FROM dojo_finding WHERE test_id=peer_id AND duplicate),
'request_response_rows',(SELECT count(*) FROM dojo_burprawrequestresponse b JOIN dojo_finding f ON b.finding_id=f.id WHERE f.test_id IN (primary_id,peer_id)),
'location_references',(SELECT count(*) FROM dojo_locationfindingreference l JOIN dojo_finding f ON l.finding_id=f.id WHERE f.test_id IN (primary_id,peer_id)))) FROM batches'''
    command=['docker','exec','-e','R4_DB='+manifest[variant]['database'],'-e','R4_SQL='+sql,'django-defectdojo-postgres-1','sh','-c','PGOPTIONS="-c default_transaction_read_only=on" psql -X -U "$POSTGRES_USER" -d "$R4_DB" -Atc "$R4_SQL"']
    rows=json.loads(subprocess.check_output(command,text=True))
    for row in rows:
        assert row['primary_findings']==44 and row['primary_active']==40,row
        assert row['peer_findings']==40 and row['peer_duplicates']==40,row
        assert row['request_response_rows']>0 and row['location_references']>0,row
    output[variant]=rows
assert normalized['original']==normalized['current']==normalized['final']
(ROOT/'background_correctness.json').write_text(json.dumps({'outcomes':output,'api_statistics_equal':True},indent=2)+'\n')
print('54 import/reimport responses and deduplication/reference outcomes match in all three copies')
