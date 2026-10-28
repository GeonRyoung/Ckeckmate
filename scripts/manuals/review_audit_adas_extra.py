import json,re,hashlib
from pathlib import Path
import pymupdf
ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'.local/manual-review/2026-10-28/audit/adas'
def main():
 out=[]
 for p in sorted((ROOT/'.local/manual-corpus/2026-10-28/hyundai').glob('*-omManual.pdf')):
  if p.name.startswith(('US4SV','HRSV')):continue
  d=pymupdf.open(p);toc=d.get_toc();code=p.stem.replace('-omManual','');ranges=[]
  for i,(lev,title,start) in enumerate(toc):
   if re.search('센서 정보 알아두기|인식 센서 및 제한|운전자 모니터링|전방 주시|운전자 상태',title) and lev<=2:
    end=next((t[2] for t in toc[i+1:] if t[0]<=lev),len(d)+1)-1
    ranges.append((title,start,end))
  if code in ['CN7N-2026','HR-2026','HREV-2026','QX-2027']:
   for j,page in enumerate(d):
    text=re.sub(r'\s+','',page.get_text())
    if re.search('기능이상|시스템이상|센서가림|시스템점검|작동불량',text) and re.search('보조|카메라|레이더|주차거리',text):ranges.append(('예외목차 고장 후보',j+1,min(j+2,len(d))))
  for title,start,end in ranges:
   text='\n'.join(f'[PDF {j}]\n'+d[j-1].get_text() for j in range(start,end+1))
   dest=RAW/f'extra-{code}-{start}-{end}.txt';dest.write_text(text,encoding='utf8')
   out.append({'code':code,'title':title,'pages':[start,end],'path':str(dest.relative_to(ROOT)),'characters':len(text),'hash':hashlib.sha256(p.read_bytes()).hexdigest()})
 (RAW/'extra-manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
