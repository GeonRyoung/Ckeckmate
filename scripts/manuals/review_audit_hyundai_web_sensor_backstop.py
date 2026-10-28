"""Required sensor handling and headlight fallback hidden under generic headings."""
import json,re,hashlib
from pathlib import Path
from hyundai_review_inventory import js_json,flatten
ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'.local/manual-review/2026-10-28/audit/hyundai-web-closure';known=json.loads((RAW/'inventory.json').read_text(encoding='utf8'));keys={e['sectionId'] for e in known};hashes={u['hash'] for u in json.loads((RAW/'units.json').read_text(encoding='utf8'))};es=[];us=[];lookup={}
for code in ['NH2','GN7','GN7HEV','CN8','CN8KH','NX5','NX5KP']:
 p=ROOT/'.local/manual-corpus/2026-10-28/hyundai'/f'{code}-2027-web';sf=p/'data/searchData.json';search=js_json(sf);toc=flatten(js_json(p/'data/tocData.json'));parents=[k for k,v in toc.items() if v['title']=='인식 센서 및 제한 사항']
 for k,v in toc.items():
  sid=f'HYUNDAI-{code}-2027-{k}';ls=search.get(k,[])
  if sid in keys or not ls:continue
  if not (any(k.startswith(parent+'_') for parent in parents) or any('수동' in t and ('전조등' in t or '상향' in t) for t in ls) and ('하이빔' in v['title'] or '헤드램프' in v['title'])):continue
  e=dict(sectionId=sid,documentId=f'HYUNDAI-{code}-2027',title=v['title'],topicId=k,sourceURL=f'https://ownersmanual.hyundai.com/full_webhelp/{code}/2027/ko_KR/'+v['path'],sourceSha256=hashlib.sha256(sf.read_bytes()).hexdigest(),sourceKind='official_searchData_text',sourceLocalPath=str(sf.relative_to(ROOT)),lines=ls);n=len(es);es.append(e)
  for line in ls:
   ha=hashlib.sha256(re.sub(r'\s+','',line).encode()).hexdigest()
   if ha in hashes:continue
   if ha in lookup:us[lookup[ha]]['entries'].append(n)
   else:lookup[ha]=len(us);us.append(dict(id=len(us),text=line,hash=ha,entries=[n]))
(RAW/'sensor-backstop-inventory.json').write_text(json.dumps(es,ensure_ascii=False,indent=2),encoding='utf8');(RAW/'sensor-backstop-units.json').write_text(json.dumps(us,ensure_ascii=False,indent=2),encoding='utf8')
for i in range(0,len(us),80):(RAW/f'sensor-read-{i//80:02}.txt').write_text('\n'.join(f"{u['id']} [{es[u['entries'][0]]['documentId']}] {u['text']}" for u in us[i:i+80]),encoding='utf8')
print(len(es),len(us),sum(len(u['text']) for u in us))
