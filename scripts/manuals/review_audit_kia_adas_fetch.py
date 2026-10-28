"""Acquire ADAS fault-reference subtrees. Acquisition is not semantic review."""
import asyncio,json,re,hashlib
from pathlib import Path
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
import httpx
ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'.local/manual-review/2026-10-28/audit/kia-adas'
pattern=re.compile(r'\b(?:FCA|LKA|LDW|LFA|ISLA|DAW|DMS|FAW|SCC|BCA|BCW|PDW|PCA|HDA|HBA|IFS|BVM|SVM|RVM|RCCA|RCCW|SEA|SEW|RSPA)\b|전방 주시|운전자 모니터링|인식 센서|센서 정보')
async def main():
 RAW.mkdir(parents=True,exist_ok=True)
 ds=json.loads((ROOT/'data/manual-research/2026-10-28/kia_manifest.json').read_text(encoding='utf8'))['documents']
 for p in (ROOT/'.local/manual-review/2026-10-28/audit').glob('*2025-acquired.json'):ds.append(json.loads(p.read_text(encoding='utf8')))
 results=[];errors=[];sem=asyncio.Semaphore(12)
 refs=json.loads((ROOT/'data/manual-review/2026-10-28/kia-inventory.json').read_text(encoding='utf8'))['entries']
 async with httpx.AsyncClient(timeout=40,follow_redirects=True) as c:
  async def job(d):
   known={a['source_url'].split('#')[0]:a for a in d['assets']};queue=[];seen=set();items=[]
   for e in refs:
    if e['document_id']!=d['id']:continue
    for r in e.get('cross_references',[]):
     if pattern.search(r['label']):queue.append((r['url'].split('#')[0],r['label']))
   seeds=[a for a in d['assets'] if a.get('format')=='html' and '/topics/' in a['source_url']][:3]
   seeds.extend(a for a in d['assets'] if a.get('format')=='html' and pattern.search(a.get('title','')))
   seeds.extend(a for a in d['assets'] if a['source_url'].endswith('/toc.html'))
   for a in seeds:
    if a.get('format')!='html':continue
    raw=(ROOT/a['local_path']).read_bytes();s=BeautifulSoup(raw,'lxml');b=s.select_one('main article') or s.select_one('main') or s.select_one('.topic-contents.main-page') or s
    h=b.find(re.compile('^h[1-6]$'));title=h.get_text(' ',strip=True) if h else a.get('title','')
    if pattern.search(title):queue.append((a['source_url'].split('#')[0],title))
    if True:
     for link in s.select('li a[href], main article a[href], .topic-contents.main-page a[href]'):
      title=link.get_text(' ',strip=True)
      if pattern.search(title):queue.append((urljoin(a['source_url'],link['href']).split('#')[0],title))
   while queue:
    url,scope=queue.pop(0)
    if url in seen:continue
    seen.add(url)
    try:
     if url in known:a=known[url];raw=(ROOT/a['local_path']).read_bytes();path=a['local_path']
     else:
      dest=RAW/d['id']/urlparse(url).path.rsplit('/',1)[-1]
      if dest.exists():raw=dest.read_bytes()
      else:
       async with sem:resp=await c.get(url);resp.raise_for_status();raw=resp.content
       dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
      path=str(dest.relative_to(ROOT))
     s=BeautifulSoup(raw,'lxml');b=s.select_one('main article') or s.select_one('main') or s.select_one('.topic-contents.main-page') or s
     h=b.find(re.compile('^h[1-6]$'));title=h.get_text(' ',strip=True) if h else scope
     items.append(dict(documentId=d['id'],sourceURL=url,sourceSha256=hashlib.sha256(raw).hexdigest(),localPath=path,title=title,rootScope=scope))
     for cur in s.select('li.active'):
      link=cur.select_one('div.topicref > div.title > a[href]')
      if link and urljoin(url,link['href']).split('#')[0]==url:
       for link in cur.select('ul a[href]'):
        if re.search('이상|가림|고장|인식 센서|센서 정보',link.get_text(' ',strip=True)):queue.append((urljoin(url,link['href']).split('#')[0],scope))
     if s.select_one('.topic-contents.main-page'):
      stem=urlparse(url).path.rsplit('/',1)[-1].removesuffix('.html')
      for link in b.select('a[href]'):
       target=urljoin(url,link['href']).split('#')[0]
       if urlparse(target).path.rsplit('/',1)[-1].startswith(stem+'_') and re.search('이상|가림|고장|인식 센서|센서 정보',link.get_text(' ',strip=True)):queue.append((target,scope))
    except Exception as e:errors.append(dict(documentId=d['id'],URL=url,error=str(e)))
   results.extend(items);print(d['id'],len(items),flush=True)
   (RAW/(d['id']+'-manifest.json')).write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf8')
  await asyncio.gather(*(job(d) for d in ds if d.get('toc_url')))
 (RAW/'manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8');(RAW/'errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),encoding='utf8')
 print('assets',len(results),'errors',len(errors))
if __name__=='__main__':asyncio.run(main())
