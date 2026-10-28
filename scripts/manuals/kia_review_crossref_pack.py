import json,pathlib,re,difflib,sys
R=pathlib.Path(__file__).resolve().parents[2]; RAW=R/'.local/manual-review/2026-10-28/kia'; O=R/'data/manual-review/2026-10-28'
items=json.loads((RAW/'crossref-units.json').read_text('utf8')); ledger=json.loads((O/'kia-crossref-reviewed.json').read_text('utf8'))['entries']
scope=json.loads((O/'kia-crossref-scope.json').read_text('utf8'))['entries'] if (O/'kia-crossref-scope.json').exists() else []
excluded={x['key'] for x in scope if x['scope_disposition']!='REQUIRED_ACTION_REVIEW'}
read=[u for u in items if u['key'] in ledger];pending=[u for u in items if u['key'] not in ledger and u['key'] not in excluded]
def norm(s):return re.sub(r'\s+|경보|감지|개별|\(TPMS\)|\(TMK\)','',s).replace('경우','때').replace('시','때')
pack=[]
for u in pending[int(sys.argv[1]):int(sys.argv[1])+int(sys.argv[2])]:
 candidates=[b for b in read if norm(b['label'])==norm(u['label'])]
 b=max(candidates,key=lambda b:difflib.SequenceMatcher(None,b['text'],u['text'],autojunk=False).ratio(),default=None)
 ratio=difflib.SequenceMatcher(None,b['text'],u['text'],autojunk=False).ratio() if b else 0
 print('\nUNIT',u['sequence'],u['key'][:10],u['label'],'DOCS',','.join(o['document_id'] for o in u['occurrences']))
 if b and ratio>=.68:
  print('BASIS',b['sequence'],b['key'][:10],round(ratio,3))
  for tag,i,j,a,z in difflib.SequenceMatcher(None,b['text'],u['text'],autojunk=False).get_opcodes():
   if tag!='equal':
    old=b['text'][i:j];new=u['text'][a:z]
    if re.sub(r'[\s「」\[\](),.:*]','',old)==re.sub(r'[\s「」\[\](),.:*]','',new):continue
    print(u['text'][max(0,a-12):a],repr(old),'→',repr(new),u['text'][z:z+12])
 else:print('FULL',u['text'])
 pack.append({'sequence':u['sequence'],'key':u['key'],'basis':b['key'] if b and ratio>=.68 else None})
(RAW/'crossref-latest-pack.json').write_text(json.dumps(pack,indent=2),'utf8')
