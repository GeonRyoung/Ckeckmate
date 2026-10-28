import json,pathlib,sys,re,difflib
R=pathlib.Path(__file__).resolve().parents[2];L=R/'.local/manual-review/2026-10-28/kia';O=R/'data/manual-review/2026-10-28'
u=json.loads((L/'closure-child-bodies.json').read_text('utf8'));p=O/'kia-child-reviewed.json';r=json.loads(p.read_text('utf8')) if p.exists() else {}
def norm(s):return re.sub(r'\s+',' ',s).strip()
prior=[]
for x in json.loads((L/'crossref-units.json').read_text('utf8')):prior.append({'url':x['occurrences'][0]['source_url'],'title':x['label'],'text':x['text']})
prior+=json.loads((L/'direct-ref-unread-bodies.json').read_text('utf8'))
for i,x in enumerate(u):
 matches=[y for y in prior if norm(y['text'])==norm(x['text'])]
 if x['url'] not in r and matches:
  y=matches[0];r[x['url']]={k:x[k] for k in ['url','title','source_sha256','parents']};r[x['url']].update(source_status='SOURCE_TEXT_REVIEWED',method='EXACT_BODY_REUSE_WITH_PARENT_CONTEXT',basis_url=y['url'],review_note_ko='기존 직접 독해 본문과 전체 문자 동일. 문서별 URL/부모 연결 유지.',runtimeApproved=False,expertApproved=False)
p.write_text(json.dumps(r,ensure_ascii=False,indent=2),'utf8')
print('SAVED',len(r),'REMAINING',len(u)-len(r))
count=int(sys.argv[1]);pack=[];basis=[x for x in u if x['url'] in r]+prior
for i,x in enumerate(u):
 if x['url'] in r:continue
 bs=[(difflib.SequenceMatcher(None,norm(y['text']),norm(x['text']),autojunk=False).ratio(),y) for y in basis if re.sub(r'\W','',y['title'])==re.sub(r'\W','',x['title'])]
 ratio,y=max(bs,key=lambda z:z[0]) if bs else (0,None)
 print('\nUNIT',i,x['url'],x['title'])
 if ratio>=.90:
  print('BASIS',y['url'],round(ratio,3));a=norm(y['text']);b=norm(x['text'])
  for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
   if tag!='equal':print(b[max(0,j1-18):j1],repr(a[i1:i2]),'→',repr(b[j1:j2]),b[j2:j2+18])
 else:print('FULL',x['text'])
 print('CHILDREN',x['children']);pack.append({'index':i,'url':x['url'],'basis':y['url'] if ratio>=.90 else None});basis.append(x)
 if len(pack)>=count:break
(L/'child-latest-pack.json').write_text(json.dumps(pack,ensure_ascii=False,indent=2),'utf8')
