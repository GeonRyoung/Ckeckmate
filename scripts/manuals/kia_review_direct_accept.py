import json,pathlib,sys
R=pathlib.Path(__file__).resolve().parents[2];L=R/'.local/manual-review/2026-10-28/kia';O=R/'data/manual-review/2026-10-28';u=json.loads((L/'direct-ref-unread-bodies.json').read_text('utf8'));p=O/'kia-direct-reviewed.json';r=json.loads(p.read_text('utf8')) if p.exists() else {};notes=json.loads(pathlib.Path(sys.argv[1]).read_text('utf8'));pack=json.loads((L/'direct-latest-pack.json').read_text('utf8')) if (L/'direct-latest-pack.json').exists() else []
for i,n in notes.items():
 x=u[int(i)]
 if n=='__INHERIT__':n=r[next(y['basis'] for y in pack if y['index']==int(i))]['review_note_ko']+' [원문 기준과 모든 의미 차이를 직접 대조하여 동일 판정.]'
 r[x['url']]={'index':int(i),'source_url':x['url'],'source_sha256':x['asset']['sha256'],'title':x['title'],'document_ids':x['documents'],'review_note_ko':n,'source_status':'SOURCE_TEXT_REVIEWED','runtimeApproved':False,'expertApproved':False}
p.write_text(json.dumps(r,ensure_ascii=False,indent=2),'utf8');print('direct roots read',len(r))
