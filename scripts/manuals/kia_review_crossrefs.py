"""Inventory action-completing source topics. Candidate enumeration is not review."""
import json,re,pathlib,hashlib
from bs4 import BeautifulSoup
R=pathlib.Path(__file__).resolve().parents[2]; RAW=R/'.local/manual-review/2026-10-28/kia'; OUT=R/'data/manual-review/2026-10-28'
m=json.loads((R/'data/manual-research/2026-10-28/kia_manifest.json').read_text('utf8'))
for p in (R/'.local/manual-review/2026-10-28/audit').glob('*2025-acquired.json'):m['documents'].append(json.loads(p.read_text('utf8')))
extra=json.loads((RAW/'crossref-assets.json').read_text('utf8')) if (RAW/'crossref-assets.json').exists() else {}
pat=re.compile(r'타이어 공기압 (?:경보|감지)|개별 타이어 공기압|저압 타이어|타이어.*교체.*때|타이어 교체 시|타이어 임시 수리|전자식 파킹|냉각수 점검|냉각수량|엔진 오일.*점검|브레이크액.*점검|주행 중 고장|주행 중.*고장|차량 견인|견인 후크|상차 견인|화재.*(?:시|발생)|충전되지 않을|과열|오버히트|매연 필터|요소수|배기가스 장치|디젤.*연료|연료 필터')
units={};assets=[]
for d in m['documents']:
 for a in d['assets']+extra.get(d['id'],[]):
  if a.get('format')!='html' or (not a.get('root_scope') and not pat.search(a.get('title',''))):continue
  s=BeautifulSoup((R/a['local_path']).read_bytes(),'lxml'); body=s.select_one('main article') or s.select_one('main') or s.select_one('.topic-contents.main-page') or s
  for n in body.select('script,style,.wh_topic_content .related-links'):n.decompose()
  t=re.sub(r'\s+',' ',body.get_text(' ',strip=True)).strip()
  # Exact canonical normalization strips figure identifiers and font controls only.
  canonical=re.sub(r'\b(?:O[A-Z][A-Z0-9_]{5,}|N_[A-Z0-9_]{5,}|WKIA_[0-9]+)\b','',t)
  canonical=re.sub(r'\s+',' ',canonical.replace('A− A+','')).strip()
  k=hashlib.sha256(canonical.encode()).hexdigest()
  occ={'document_id':d['id'],'source_url':a['source_url'],'asset_sha256':a['sha256'],'local_path':a['local_path']}
  if k not in units:units[k]={'key':k,'label':a['title'],'text':canonical,'occurrences':[]}
  if occ not in units[k]['occurrences']:units[k]['occurrences'].append(occ);assets.append(occ)
for i,u in enumerate(units.values(),1):u['sequence']=i
(RAW/'crossref-units.json').write_text(json.dumps(list(units.values()),ensure_ascii=False,indent=2),'utf8')
(OUT/'kia-crossref-inventory.json').write_text(json.dumps({'scope':'Action-completing emergency, maintenance and brake/tire source topics; ADAS separately pending. Titles are candidates, not review.','candidate_assets':len(assets),'distinct_canonical_units':len(units),'units':[{k:v for k,v in u.items() if k!='text'} for u in units.values()]},ensure_ascii=False,indent=2),'utf8')
print('candidate assets',len(assets),'distinct',len(units),'characters',sum(len(u['text']) for u in units.values()))
for u in units.values():print(u['sequence'],len(u['text']),u['label'],','.join(x['document_id'] for x in u['occurrences']))
