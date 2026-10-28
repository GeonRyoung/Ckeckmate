import json,re,hashlib
from pathlib import Path
import pymupdf
ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'.local/manual-review/2026-10-28/audit/adas'
def main():
 es=[]
 extra=json.loads((RAW/'extra-manifest.json').read_text(encoding='utf8'));has={e['code'] for e in extra if '센서' in e['title']}
 for p in sorted((ROOT/'.local/manual-corpus/2026-10-28/hyundai').glob('*-omManual.pdf')):
  code=p.stem.replace('-omManual','')
  if code in has or code.startswith(('US4SV','HRSV','HR-','HREV-')):continue
  d=pymupdf.open(p);toc=d.get_toc();ranges=[]
  for i,(lev,title,start) in enumerate(toc):
   if '센서 정보 알아두기' in title or (lev==2 and re.search(r'\((FCA|BCA)\)',title)):
    end=toc[i+1][2] if i+1<len(toc) else start+2
    ranges.append((title,start,max(start,end)))
  if code in ['CN7N-2026','QX-2027']:
   for j,page in enumerate(d):
    t=re.sub(r'\s+','',page.get_text())
    if re.search('레이더커버를훼손|부드러운천|카메라렌즈앞유리|고압으로물을',t) and re.search('카메라|레이더|초음파',t):ranges.append(('인식 센서 취급',j+1,j+1))
  for title,start,end in ranges:
   text='\n'.join(f'[PDF {j}]\n'+d[j-1].get_text() for j in range(start,end+1));dest=RAW/f'sensor-{code}-{start}-{end}.txt';dest.write_text(text,encoding='utf8')
   es.append(dict(code=code,title=title,pages=[start,end],path=str(dest.relative_to(ROOT)),hash=hashlib.sha256(p.read_bytes()).hexdigest()))
 units={}
 for i,e in enumerate(es):
  t=re.sub(r'\s+','',Path(ROOT/e['path']).read_text(encoding='utf8'));t=re.sub(r'\[PDF\d+\]|2C_[A-Za-z0-9_]+','',t)
  for s in re.split(r'(?<=[.!?])',t):
   if len(s)<12:continue
   h=hashlib.sha256(s.encode()).hexdigest();units.setdefault(h,dict(id=len(units),hash=h,text=s,entries=[]))['entries'].append(i)
 U=list(units.values());(RAW/'sensor-manifest.json').write_text(json.dumps(es,ensure_ascii=False,indent=2),encoding='utf8');(RAW/'sensor-units.json').write_text(json.dumps(U,ensure_ascii=False,indent=2),encoding='utf8')
 for j in range(0,len(U),70):(RAW/f'sensor-read-{j//70:02}.txt').write_text('\n'.join(f"[{u['id']}] {u['text']}" for u in U[j:j+70]),encoding='utf8')
 print(len(es),len(U),sum(len(u['text']) for u in U))
if __name__=='__main__':main()
