import json,pathlib,asyncio,hashlib,re
from urllib.parse import urlparse,urljoin
import httpx
from bs4 import BeautifulSoup
R=pathlib.Path(__file__).resolve().parents[2];L=R/'.local/manual-review/2026-10-28/kia';queue=json.loads((L/'closure-child-queue.json').read_text('utf8'));out=[];errors=[];sem=asyncio.Semaphore(12)
async def one(c,x):
 url=x['url'];p=L/'closure-children'/urlparse(url).path.split('/full_webhelp/')[1]
 try:
  if p.exists():raw=p.read_bytes()
  else:
   async with sem:r=await c.get(url);r.raise_for_status();raw=r.content
   p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
  s=BeautifulSoup(raw,'lxml');b=s.select_one('main article') or s.select_one('main') or s.select_one('.topic-contents.main-page')
  if not b:raise ValueError('no body')
  h=b.find(re.compile('^h[1-6]$'));links=[{'label':a.get_text(' ',strip=True),'url':urljoin(url,a['href']).split('#')[0]} for a in b.select('a[href]')];children=[]
  for cur in s.select('li.active'):
   a=cur.select_one('div.topicref > div.title > a[href]')
   if a and urljoin(url,a['href']).split('#')[0]==url:children += [{'label':a.get_text(' ',strip=True),'url':urljoin(url,a['href']).split('#')[0]} for a in cur.select('ul a[href]')]
  stem=url.rsplit('/',1)[-1].replace('.html','');children += [a for a in links if a['url'].rsplit('/',1)[-1].startswith(stem+'_')]
  out.append({**x,'title':h.get_text(' ',strip=True) if h else '', 'text':b.get_text(' ',strip=True),'source_sha256':hashlib.sha256(raw).hexdigest(),'local_path':p.relative_to(R).as_posix(),'links':links,'children':[a for a in children if a['url']!=url]})
 except Exception as e:errors.append({'url':url,'error':str(e)})
async def main():
 async with httpx.AsyncClient(timeout=50,follow_redirects=True) as c:await asyncio.gather(*(one(c,x) for x in queue))
 out.sort(key=lambda x:x['url']);(L/'closure-child-bodies.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),'utf8');(L/'closure-child-errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),'utf8');print('bodies',len(out),'chars',sum(len(x['text']) for x in out),'errors',errors)
asyncio.run(main())
