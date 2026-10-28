"""Inventory missing required web references; extraction never means review."""
import json,re,hashlib
from pathlib import Path
from hyundai_review_inventory import js_json,flatten
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'data/manual-review/2026-10-28';RAW=ROOT/'.local/manual-review/2026-10-28/audit/hyundai-web-closure';CODES=['NH2','GN7','GN7HEV','CN8','CN8KH','NX5','NX5KP']
def main():
 RAW.mkdir(parents=True,exist_ok=True);old=json.loads((OUT/'hyundai-web-coverage.json').read_text(encoding='utf8'))['sections'];oldids={r['sectionId'] for r in old};seen=set();units=[];lookup={};entries=[]
 for code in CODES:
  directory=ROOT/'.local/manual-corpus/2026-10-28/hyundai'/f'{code}-2027-web';sf=directory/'data/searchData.json';search=js_json(sf);toc=flatten(js_json(directory/'data/tocData.json'));sha=hashlib.sha256(sf.read_bytes()).hexdigest()
  for r in old:
   if r['documentId']!=f'HYUNDAI-{code}-2027':continue
   for line in search.get(r['source']['locator']['topicId'],[]):seen.add(hashlib.sha256(re.sub(r'\s+','',line).encode()).hexdigest())
  emergency=[key for key,v in toc.items() if v['title']=='비상시 응급조치'];selected=[]
  for key,node in toc.items():
   title=node['title'];sid=f'HYUNDAI-{code}-2027-{key}'
   if sid in oldids:continue
   isem=any(key==p or key.startswith(p+'_') for p in emergency)
   adas=bool(re.search(r'\b(?:FCA|LKA|LFA|ISLA|DAW|DMS|SCC|BCA|PDW|PCA|HDA|HBA|IFS|BVM|SVM|RVM|RCCA|SEA|SEW|RSPA)\b|운전자 모니터링|인식 센서|센서 정보',title))
   fault=bool(re.search('이상|고장',title));brake=bool(re.search('주차 브레이크|자동 정차|차체.?자세 제어|제동 장치|브레이크 작동',title));keycontext=bool(re.search('비상 시동|스마트 키.*배터리|스마트키.*배터리|키 배터리|시동.*켜기|시동.*걸기',title))
   if not (isem or adas or fault or brake or keycontext):continue
   if adas and re.search('설정|작동|사용',title) and not re.search('모니터링',title):continue
   lines=search.get(key,[])
   if not lines:continue
   scope='emergency-required-reference' if isem else 'brake-or-key-required-reference' if brake or keycontext else 'adas-fault-and-sensor-reference'
   # Keep all parking/headlight restriction context for cleaning prohibitions/fallback.
   if fault and not re.search('주차|모니터|하이빔|헤드램프',title):
    limits=next((j for j,l in enumerate(lines) if j>1 and re.fullmatch(r'(?:작동 )?제한 사항',l.strip())),None)
    if limits is not None:lines=lines[:limits]
   e=dict(sectionId=sid,documentId=f'HYUNDAI-{code}-2027',title=title,topicId=key,sourceURL=f'https://ownersmanual.hyundai.com/full_webhelp/{code}/2027/ko_KR/'+node['path'],sourceSha256=sha,sourceKind='official_searchData_text',sourceLocalPath=str(sf.relative_to(ROOT)),scope=scope,reviewStatus='CANDIDATE_NOT_REVIEWED',lines=lines)
   n=len(entries);entries.append(e)
   for line in lines:
    ha=hashlib.sha256(re.sub(r'\s+','',line).encode()).hexdigest()
    if ha in seen:continue
    if ha in lookup:units[lookup[ha]]['entries'].append(n)
    else:lookup[ha]=len(units);units.append(dict(id=len(units),hash=ha,text=line,entries=[n]))
 (RAW/'inventory.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf8');(RAW/'units.json').write_text(json.dumps(units,ensure_ascii=False,indent=2),encoding='utf8')
 for i in range(0,len(units),80):(RAW/f'read-{i//80:02}.txt').write_text('\n'.join(f"{u['id']} [{entries[u['entries'][0]]['documentId']}] {u['text']}" for u in units[i:i+80]),encoding='utf8')
 print('sections',len(entries),'unique units',len(units),'chars',sum(len(x['text']) for x in units))
 from collections import Counter
 print(Counter(e['documentId'] for e in entries));print(Counter(e['scope'] for e in entries))
if __name__=='__main__':main()
