"""Acquire omitted required context; never certify candidates."""
import asyncio,json,re,hashlib
from pathlib import Path
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
import httpx
ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'.local/manual-review/2026-10-28/audit/kia-adas'
def body(s):return s.select_one('main article') or s.select_one('.topic-contents.main-page') or s.select_one('main')
async def main():
 es=json.loads((RAW/'manifest.json').read_text(encoding='utf8'));base={e['sourceURL']:e for e in es};queue=[];results=[];seen=set();errors=[]
 targeted=re.compile(r'\b(?:HBA|IFS|PDW|PCA|RVM|SVM|BVM|RSPA)\b')
 for e in es:
  s=BeautifulSoup((ROOT/e['localPath']).read_bytes(),'lxml');b=body(s)
  if e['documentId']=='kia_PU_2026':queue.append((e['sourceURL'],e['documentId'],'PU legacy hidden faults',e['rootScope']))
  if targeted.search(e['rootScope']) and re.search('이상',e['title']):
   # Old manuals embed restrictions inline; modern manuals link child restriction pages.
   queue.append((e['sourceURL'],e['documentId'],'linked sensor handling and manual fallback',e['rootScope']))
   for li in s.select('li.active'):
    a=li.select_one('div.topicref > div.title > a[href]')
    if a and urljoin(e['sourceURL'],a['href']).split('#')[0]==e['sourceURL']:
     for a in li.select('ul a[href]'):
      if '제한' in a.get_text():queue.append((urljoin(e['sourceURL'],a['href']).split('#')[0],e['documentId'],'linked sensor handling and manual fallback',e['rootScope']))
 legacy=['kia_NQ5KH_2026','kia_PUEV_2026','kia_PU_2026','kia_RJ_2026','kia_SP2_2026','kia_KA4_2025','kia_KA4KH_2025']
 for did in legacy:
  e=next(e for e in es if e['documentId']==did);s=BeautifulSoup((ROOT/e['localPath']).read_bytes(),'lxml')
  for a in s.select('li a[href]'):
   if a.get_text(' ',strip=True)=='조명':queue.append((urljoin(e['sourceURL'],a['href']).split('#')[0],did,'lighting discovery','lighting'))
 async with httpx.AsyncClient(timeout=30,follow_redirects=True) as c:
  while queue:
   url,did,reason,scope=queue.pop(0)
   if url in seen:continue
   seen.add(url)
   try:
    if url in base:path=ROOT/base[url]['localPath']
    else:path=RAW/did/urlparse(url).path.rsplit('/',1)[-1]
    if path.exists():raw=path.read_bytes()
    else:r=await c.get(url);r.raise_for_status();raw=r.content;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    s=BeautifulSoup(raw,'lxml');b=body(s)
    if not b:raise ValueError('missing manual body')
    h=b.find(re.compile('^h[1-6]$'));title=h.get_text(' ',strip=True) if h else scope
    if reason!='lighting discovery':results.append(dict(documentId=did,sourceURL=url,sourceSha256=hashlib.sha256(raw).hexdigest(),title=title,rootScope=scope,reason=reason,localPath=str(path.relative_to(ROOT))))
    for a in b.select('a[href]'):
     label=a.get_text(' ',strip=True);target=urljoin(url,a['href']).split('#')[0];stem=urlparse(url).path.rsplit('/',1)[-1].removesuffix('.html');child=urlparse(target).path.rsplit('/',1)[-1].startswith(stem+'_')
     if reason=='lighting discovery' and re.search('HBA|IFS|하이빔 보조|지능형 헤드램프',label):queue.append((target,did,'legacy lighting fault and fallback',label))
     elif child and (reason=='PU legacy hidden faults' or re.search('이상|제한|센서|주의',label)):queue.append((target,did,reason,scope))
   except Exception as ex:errors.append(dict(URL=url,error=str(ex)))
 (RAW/'extra-review-inventory.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8');(RAW/'extra-errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),encoding='utf8')
 known={u['hash'] for u in json.loads((RAW/'review-units.json').read_text(encoding='utf8'))};units=[];lookup={}
 for i,e in enumerate(results):
  s=BeautifulSoup((ROOT/e['localPath']).read_bytes(),'lxml');b=body(s)
  for text in b.get_text('\n',strip=True).splitlines():
   if not text or re.fullmatch(r'[A-Z0-9_\-]{6,}',text):continue
   ha=hashlib.sha256(re.sub(r'\s+','',text).encode()).hexdigest()
   if ha in known:continue
   if ha in lookup:units[lookup[ha]]['entries'].append(i)
   else:lookup[ha]=len(units);units.append(dict(id=len(units),hash=ha,text=text,entries=[i]))
 (RAW/'extra-review-units.json').write_text(json.dumps(units,ensure_ascii=False,indent=2),encoding='utf8')
 for i in range(0,len(units),100):(RAW/f'extra-read-{i//100:02}.txt').write_text('\n'.join(f"{u['id']} [{results[u['entries'][0]]['documentId']}] {u['text']}" for u in units[i:i+100]),encoding='utf8')
 print('sources',len(results),'newunits',len(units),'errors',errors)
if __name__=='__main__':asyncio.run(main())
