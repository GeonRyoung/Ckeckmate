import json,pathlib,collections
R=pathlib.Path(__file__).resolve().parents[2];O=R/'data/manual-review/2026-10-28';L=R/'.local/manual-review/2026-10-28/kia'
u=json.loads((L/'unique-sections.json').read_text('utf8'))
inventory=json.loads((O/'kia-inventory.json').read_text('utf8'))['entries']
refs={}
for x in inventory:
 for a in x['cross_references']:
  url=a['url'].split('#')[0];e=refs.setdefault(url,{'url':url,'labels':set(),'from':set(),'documents':set()});e['labels'].add(a['label']);e['from'].add(x['label']);e['documents'].add(x['document_id'])
known={}
for p in [R/'data/manual-research/2026-10-28/kia_manifest.json']:
 for d in json.loads(p.read_text('utf8'))['documents']:
  for a in d['assets']:known[a['source_url']]=a
for p in (R/'.local/manual-review/2026-10-28/audit').glob('*2025-acquired.json'):
 for a in json.loads(p.read_text('utf8'))['assets']:known[a['source_url']]=a
for assets in json.loads((L/'crossref-assets.json').read_text('utf8')).values():
 for a in assets:known[a['source_url']]=a
inline={o['source_url'].split('#')[0] for x in u for o in x['occurrences']}
cr={o['source_url'].split('#')[0] for x in json.loads((O/'kia-crossref-reviewed.json').read_text('utf8'))['entries'].values() for o in x['occurrences']}
adas=json.loads((O/'audit-kia-adas-review.json').read_text('utf8'));ad={x['sourceURL'].split('#')[0] for x in adas['rows']+adas.get('additionalRows',[])}
rows=[]
for url,e in refs.items():
 e={k:sorted(v) if isinstance(v,set) else v for k,v in e.items()};e['asset']=known.get(url);e['read_evidence']=[n for n,s in [('inline',inline),('countermeasure',cr),('adas',ad)] if url in s];rows.append(e)
(L/'direct-ref-audit.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),'utf8')
print('TOTAL',len(rows),'NO URL READ',sum(not x['read_evidence'] for x in rows))
for i,x in enumerate(rows):
 if not x['read_evidence']:print(i,','.join(x['labels']),'FROM',','.join(x['from']),x['url'])
