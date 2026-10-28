"""Candidate inventory only; never marks text reviewed."""
import json,re,hashlib
from pathlib import Path
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'.local/manual-review/2026-10-28/audit/adas'
OUT=ROOT/'data/manual-review/2026-10-28'
def main():
 RAW.mkdir(parents=True,exist_ok=True)
 entries=[]; groups={}
 for p in sorted((ROOT/'.local/manual-corpus/2026-10-28/hyundai').glob('*-omManual.pdf')):
  if p.name.startswith(('US4SV','HRSV')):continue
  d=pymupdf.open(p);toc=d.get_toc();code,year=p.stem.split('-')[:2];active=None
  for i,(level,title,start) in enumerate(toc):
   if level==2:active=title if re.search(r'\((?:FCA|LKA|LFA|ISLA|DAW|DMS|SCC|BCA|PDW|PCA|HDA|HBA|IFS|BVM|SVM|RCCA|SEA|SEW|RSPA)\)',title) else None
   if not active or not re.search('이상|고장|작동 제한',title):continue
   end=next((x[2] for x in toc[i+1:] if x[0]<=level),len(d)+1)-1
   # Keep full limitations section for reading, including driver actions and cancellation exceptions.
   text='\n'.join(f'\n[PDF {n}]\n'+d[n-1].get_text() for n in range(start,end+1))
   path=RAW/f'{code}-{year}-{start}-{end}.txt';path.write_text(text,encoding='utf8')
   clean=re.sub(r'\s+',' ',re.sub(r'\[PDF \d+\]','',text)).strip()
   h=hashlib.sha256(clean.encode()).hexdigest()
   e={'documentId':f'HYUNDAI-{code}-{year}','system':active,'title':title,'pdfPages':[start,end],
      'sourceURL':f'https://ownersmanual.hyundai.com/full_pdf/{code}/{year}/ko_KR','sourceSha256':hashlib.sha256(p.read_bytes()).hexdigest(),
      'localTextPath':str(path.relative_to(ROOT)),'characters':len(text),'textHash':h,'reviewStatus':'CANDIDATE_NOT_REVIEWED'}
   entries.append(e);groups.setdefault(h,[]).append(e)
 (OUT/'audit-hyundai-adas-inventory.json').write_text(json.dumps({'entries':entries,'runtimeApproved':False},ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({'documents':len(set(e['documentId'] for e in entries)),'entries':len(entries),'characters':sum(e['characters'] for e in entries),'exactUnique':len(groups)},ensure_ascii=False))
if __name__=='__main__':main()
