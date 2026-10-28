import asyncio,json,pathlib,re,hashlib
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
import httpx
R=pathlib.Path(__file__).resolve().parents[2]; RAW=R/'.local/manual-review/2026-10-28/kia'
m=json.loads((R/'data/manual-research/2026-10-28/kia_manifest.json').read_text('utf8'))
for p in (R/'.local/manual-review/2026-10-28/audit').glob('*2025-acquired.json'):m['documents'].append(json.loads(p.read_text('utf8')))
roots=re.compile('타이어 공기압 (?:경보|감지)|개별 타이어 공기압|타이어 임시 수리|타이어 펑크|전자식 파킹|냉각수 점검|엔진 오일.*점검|브레이크액.*점검|주행 중 고장|주행 중.*고장|차량 견인|화재.*(?:시|발생)|충전되지 않을|엔진 과열|연료 필터|배출가스 제어 장치')
results={};errors=[];sem=asyncio.Semaphore(12)
async def docjob(c,d):
 known={a['source_url']:a for a in d['assets']}; queue=[]; seen=set(); out=[]
 for a in d['assets']:
  if a.get('format')!='html':continue
  title=a.get('title','')
  if not title:
   s=BeautifulSoup((R/a['local_path']).read_bytes(),'lxml'); b=s.select_one('main article') or s.select_one('.topic-contents.main-page') or s
   h=b.find(re.compile('^h[1-6]$'));title=h.get_text(' ',strip=True) if h else ''
  if roots.search(title):queue.append((a['source_url'],title))
 # TOC supplies additional root URLs absent from acquisition.
 toc=next((a for a in d['assets'] if a['source_url'].endswith('/toc.html')),None)
 if toc:
  s=BeautifulSoup((R/toc['local_path']).read_bytes(),'lxml')
  for a in s.select('a[href]'):
   if roots.search(a.get_text(' ',strip=True)):queue.append((urljoin(toc['source_url'],a['href']),a.get_text(' ',strip=True)))
 while queue:
  url,label=queue.pop(0)
  if url in seen:continue
  seen.add(url)
  try:
   if url in known:a=known[url];raw=(R/a['local_path']).read_bytes()
   else:
    async with sem:resp=await c.get(url);resp.raise_for_status();raw=resp.content
    dest=RAW/'crossrefs'/d['id']/urlparse(url).path.rsplit('/',1)[-1];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    a={'source_url':url,'local_path':dest.relative_to(R).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'format':'html'}
   s=BeautifulSoup(raw,'lxml');b=s.select_one('main article') or s.select_one('main') or s.select_one('.topic-contents.main-page') or s
   h=b.find(re.compile('^h[1-6]$'));a={**a,'title':h.get_text(' ',strip=True) if h else label,'root_scope':label};out.append(a)
   for cur in s.select('li.active'):
    link=cur.select_one('div.topicref > div.title > a[href]')
    if link and urljoin(url,link['href']).split('#')[0]==url:
     for link in cur.select('ul a[href]'):queue.append((urljoin(url,link['href']).split('#')[0],label))
  except Exception as e:errors.append({'document_id':d['id'],'url':url,'error':str(e)})
 results[d['id']]=out;print(d['id'],len(out),flush=True)
async def main():
 async with httpx.AsyncClient(timeout=50,follow_redirects=True) as c:await asyncio.gather(*(docjob(c,d) for d in m['documents'] if d.get('toc_url')))
 (RAW/'crossref-assets.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),'utf8')
 (RAW/'crossref-errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),'utf8')
 print('assets',sum(map(len,results.values())),'errors',len(errors))
asyncio.run(main())
