import json,pathlib,asyncio,hashlib,re
from urllib.parse import urlparse,urljoin
import httpx
from bs4 import BeautifulSoup
R=pathlib.Path(__file__).resolve().parents[2];L=R/'.local/manual-review/2026-10-28/kia'
refs=json.loads((L/'direct-ref-audit.json').read_text('utf8'));out=[];errors=[];sem=asyncio.Semaphore(12)
async def one(c,x):
 url=x['url']
 try:
  if x.get('asset'):a=x['asset'];raw=(R/a['local_path']).read_bytes()
  else:
   async with sem:r=await c.get(url);r.raise_for_status();raw=r.content
   p=L/'direct-refs'/urlparse(url).path.split('/full_webhelp/')[1];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);a={'source_url':url,'local_path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(raw).hexdigest()}
  s=BeautifulSoup(raw,'lxml');b=s.select_one('main article') or s.select_one('main') or s.select_one('.topic-contents.main-page')
  if not b:raise ValueError('No manual body')
  t=b.get_text(' ',strip=True);h=b.find(re.compile('^h[1-6]$'));links=[{'label':a.get_text(' ',strip=True),'url':urljoin(url,a['href']).split('#')[0]} for a in b.select('a[href]')];children=[]
  for cur in s.select('li.active'):
   a=cur.select_one('div.topicref > div.title > a[href]')
   if a and urljoin(url,a['href']).split('#')[0]==url:children += [{'label':a.get_text(' ',strip=True),'url':urljoin(url,a['href']).split('#')[0]} for a in cur.select('ul a[href]')]
  stem=url.rsplit('/',1)[-1].replace('.html','')
  children += [a for a in links if a['url'].rsplit('/',1)[-1].startswith(stem+'_')]
  out.append({**x,'asset':a if False else {**(x.get('asset') or {}),'source_url':url,'local_path':str((L/'direct-refs'/urlparse(url).path.split('/full_webhelp/')[1]).relative_to(R)).replace('\\','/') if not x.get('asset') else x['asset']['local_path'],'sha256':hashlib.sha256(raw).hexdigest()},'title':h.get_text(' ',strip=True) if h else '', 'text':t,'links':links,'children':children})
 except Exception as e:errors.append({'url':url,'error':str(e),'from':x['from']})
async def main():
 async with httpx.AsyncClient(timeout=50,follow_redirects=True) as c:await asyncio.gather(*(one(c,x) for x in refs if not x['read_evidence']))
 out.sort(key=lambda x:x['url']);(L/'direct-ref-unread-bodies.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),'utf8');(L/'direct-ref-errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),'utf8');print('bodies',len(out),'errors',errors)
asyncio.run(main())
