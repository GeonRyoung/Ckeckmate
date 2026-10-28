"""Prepare bounded official source procedure units for direct reading/diff review."""
import json,re,hashlib,difflib,sys
from pathlib import Path
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'.local/manual-review/2026-10-28/hyundai/procedures';RAW.mkdir(parents=True,exist_ok=True)
MAN=json.loads((ROOT/'data/manual-research/2026-10-28/hyundai-manifest.json').read_text(encoding='utf-8'))['documents']
PATTERNS={'TPMS':r'타이어 공기압 경보 시스템\s*\(TPMS\)$','OVERHEAT':r'^엔진 과열$','OIL':r'^엔진 오일$|^엔진 오일 점검하기$','COOLANT':r'^냉각수$|^냉각수 점검하기$|^냉각수 점검$','BRAKE_FLUID':r'^브레이크액$|^브레이크 액$|^브레이크액 점검하기$|^브레이크 오일$','EPB':r'^전자식 파킹 브레이크\s*\(EPB\)$','ESC':r'^차체.*\(ESC\).*장치$|^차체.*제어.*\(ESC\)$','EV_WARN':r'^경고등 및 표시등 확인하기$'}
units=[]
for d in MAN:
 if not d.get('localPath','').endswith('.pdf') or d['modelCode'] in ['US4SV','HRSV']:continue
 pdf=pymupdf.open(ROOT/d['localPath']);toc=pdf.get_toc();pages=json.loads((ROOT/d['textPagesPath']).read_text(encoding='utf-8'))
 for topic,pattern in PATTERNS.items():
  for i,t in enumerate(toc):
   if not re.search(pattern,t[1]):continue
   end=next((x[2] for x in toc[i+1:] if x[0]<=t[0]),len(pages))
   nums=list(range(t[2],min(end,len(pages))+1));text='\n'.join(pages[n-1] for n in nums)
   key=f"{d['modelCode']}-{d['year']}-{topic}";p=RAW/(key+'.txt');p.write_text(text,encoding='utf-8')
   units.append({'id':key,'documentId':f"HYUNDAI-{d['modelCode']}-{d['year']}",'topic':topic,'title':t[1],'sourceURL':d['sourceURL'],'documentSha256':d['sha256'],'locator':{'pdfPages1Based':nums},'sourceTextSha256':hashlib.sha256(text.encode()).hexdigest(),'localPath':p.relative_to(ROOT).as_posix(),'characters':len(text),'reviewStatus':'PREPARED_NOT_REVIEWED'})
(RAW/'units.json').write_text(json.dumps(units,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':
 if len(sys.argv)>2:
  base,var=sys.argv[1:3];a=next(u for u in units if u['id']==base);b=next(u for u in units if u['id']==var)
  def normalize(t):return re.sub(r'\s+|•|ঌইفӝ|઱੄|҃\s*Ҋ','',t).replace('‘',"'").replace('’',"'")
  x=normalize((ROOT/a['localPath']).read_text(encoding='utf-8'));y=normalize((ROOT/b['localPath']).read_text(encoding='utf-8'));groups=[]
  for op,i,j,k,l in difflib.SequenceMatcher(None,x,y,autojunk=False).get_opcodes():
   if op=='equal':continue
   if groups and k-groups[-1][3]<70:old=groups[-1];groups[-1]=(old[0],j,old[2],l)
   else:groups.append((i,j,k,l))
  out={'base':a,'variant':b,'groups':[{'base':x[i:j],'variant':y[k:l],'context':y[max(0,k-70):min(len(y),l+70)]} for i,j,k,l in groups]}
  (RAW/f'{base}--{var}.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
  for n,r in enumerate(out['groups']):print(n,r['context'])
 else:
  for u in units:print(u['id'],u['locator']['pdfPages1Based'],u['characters'])
