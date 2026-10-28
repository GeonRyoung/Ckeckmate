"""Extract source candidates only; direct reading is recorded separately."""
import json,re,hashlib
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'.local/manual-review/2026-10-28/audit/kia-adas'
def main():
 es=json.loads((RAW/'manifest.json').read_text(encoding='utf8'));selected=[];units=[];byhash={}
 for e in es:
  s=BeautifulSoup((ROOT/e['localPath']).read_bytes(),'lxml');b=s.select_one('main article') or s.select_one('.topic-contents.main-page') or s.select_one('main')
  if not b:continue
  title=e['title'];text=b.get_text('\n',strip=True)
  fault=bool(re.search('이상|가림|고장',title));sensor=bool(re.search('인식 센서|센서 정보',title));root=bool(re.search(r'\b(?:FCA|LKA|LDW|LFA|ISLA|DAW|FAW|DMS|SCC|BCA|BCW|PDW|PCA|HDA|HBA|IFS|BVM|SVM|RVM|RCCA|RCCW|SEA|SEW|RSPA)\b',title))
  if not (fault or sensor or root):continue
  # Stop before general performance limits; fault and blockage are separate preceding children.
  if fault:
   hs=list(b.find_all(re.compile('^h[1-6]$')))
   for h in hs[1:]:
    if re.fullmatch(r'(?:작동 )?제한 사항',h.get_text(' ',strip=True)):
     tail=h.find_all_next();h.decompose()
     for x in tail:
      if getattr(x,'parent',None):x.decompose()
     break
  text=b.get_text('\n',strip=True)
  if not text:continue
  n=len(selected);e={**e,'scope':'fault-obstruction' if fault else 'sensor-precautions' if sensor else 'system-introduction-and-linked-sensor-precautions','reviewStatus':'CANDIDATE_NOT_REVIEWED'};selected.append(e)
  for line in text.splitlines():
   line=line.strip()
   if not line or re.fullmatch(r'[A-Z0-9_\-]{6,}',line):continue
   key=re.sub(r'\s+','',line);ha=hashlib.sha256(key.encode()).hexdigest()
   if ha in byhash:units[byhash[ha]]['entries'].append(n)
   else:
    byhash[ha]=len(units);units.append(dict(id=len(units),text=line,hash=ha,entries=[n]))
 (RAW/'review-inventory.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2),encoding='utf8');(RAW/'review-units.json').write_text(json.dumps(units,ensure_ascii=False,indent=2),encoding='utf8')
 for start in range(0,len(units),80):
  (RAW/f'read-{start//80:02}.txt').write_text('\n'.join(f"{u['id']} [{','.join(sorted(set(selected[i]['documentId'] for i in u['entries'])))}] {u['text']}" for u in units[start:start+80]),encoding='utf8')
 print('selected',len(selected),'unique units',len(units),'chars',sum(len(u['text']) for u in units))
if __name__=='__main__':main()
