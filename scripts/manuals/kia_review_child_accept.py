import json,pathlib,sys
R=pathlib.Path(__file__).resolve().parents[2];L=R/'.local/manual-review/2026-10-28/kia';O=R/'data/manual-review/2026-10-28';u=json.loads((L/'closure-child-bodies.json').read_text('utf8'));p=O/'kia-child-reviewed.json';r=json.loads(p.read_text('utf8'));pack=json.loads((L/'child-latest-pack.json').read_text('utf8'));notes=json.loads(pathlib.Path(sys.argv[1]).read_text('utf8'))
for k,n in notes.items():
 x=u[int(k)];basis=next((z['basis'] for z in pack if z['index']==int(k)),None);r[x['url']]={z:x[z] for z in ['url','title','source_sha256','parents']};r[x['url']].update(source_status='SOURCE_TEXT_REVIEWED',method='CANONICAL_FULL_AND_ALL_DIFFS' if basis else 'FULL_SOURCE_READ',basis_url=basis,review_note_ko=n,runtimeApproved=False,expertApproved=False)
p.write_text(json.dumps(r,ensure_ascii=False,indent=2),'utf8');print('read',len(r),'/',len(u))
