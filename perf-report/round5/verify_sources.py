import hashlib,io,json,subprocess,tarfile
from pathlib import Path
r=Path(__file__).resolve().parent
sources={'original':('dd-final-original:3.5.100','334bef02d65a74909fe976b22724526474d5a0f6'),'round4':('dd-final-final:3.5.100','716efb463387f82a0d13d5eae2541ac6b7dfee96'),'round5':('dd-r5-final:3.5.100','c6a6144ed93b83adb1fd4ea9daa2c5e417ecea37')}
rows={}
code="import pathlib,json,hashlib; p=pathlib.Path('/app'); print(json.dumps({str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'dojo').rglob('*') if f.is_file() and not f.is_symlink() and '__pycache__' not in str(f) and f.suffix!='.pyc'}))"
for v,(image,sha) in sources.items():
 actual=json.loads(subprocess.check_output(['docker','run','--rm','--entrypoint','python',image,'-c',code],text=True))
 expected={}
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',sha,'dojo']))) as archive:
  for entry in archive:
   if entry.isfile():expected[entry.name]=hashlib.sha256(archive.extractfile(entry).read()).hexdigest()
 different=[p for p in set(actual)|set(expected) if actual.get(p)!=expected.get(p)]
 assert not different,(v,different[:10])
 rows[v]={'sha':sha,'image':image,'image_id':subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',image],text=True).strip(),'verified_files':len(expected),'different_files':different}
 print('Verified',v,len(expected),flush=True)
(r/'source_verification.json').write_text(json.dumps(rows,indent=2)+'\n')
