import pathlib,json,hashlib,asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlparse
import httpx
R=pathlib.Path(__file__).resolve().parents[2];L=R/'.local/manual-review/2026-10-28/kia';u=json.loads((L/'crossref-units.json').read_text('utf8'));q=[]
for x in u:
 if x['sequence'] not in [18,47,196,278,279,309,356,397,471,530,539,563,420,424,437]:continue
 for o in x['occurrences']:
  s=BeautifulSoup((R/o['local_path']).read_bytes(),'lxml');b=s.select_one('main article') or s.select_one('main') or s.select_one('.topic-contents.main-page')
  for img in b.select('img[src]'):
   src=urljoin(o['source_url'],img['src'])
   if any(z in src.lower() for z in ['icon','warning','caution','notice']):continue
   near=img.find_parent(['figure','div']);q.append({'source_image_url':src,'source_url':o['source_url'],'source_asset_sha256':o['asset_sha256'],'document_id':o['document_id'],'unit':x['sequence'],'expected_text':x['text'],'image_alt':img.get('alt',''),'near_text':near.get_text(' ',strip=True)[:800] if near else ''})
sem=asyncio.Semaphore(10)
async def f(c,x):
 async with sem:r=await c.get(x['source_image_url']);r.raise_for_status()
 h=hashlib.sha256(r.content).hexdigest();p=L/'visual'/ (h[:20]+pathlib.Path(urlparse(x['source_image_url']).path).suffix);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(r.content);x['image_path']=str(p);x['image_sha256']=h
async def main():
 async with httpx.AsyncClient(timeout=40,follow_redirects=True) as c:
  results=await asyncio.gather(*(f(c,x) for x in q),return_exceptions=True)
 for x,e in zip(q,results):
  if isinstance(e,Exception):x['error']=str(e)
 (L/'visual-qa-request.json').write_text(json.dumps(q,ensure_ascii=False,indent=2),'utf8');print('images',len(q),'distinct',len({x.get('image_sha256') for x in q}),'errors',sum('error'in x for x in q))
asyncio.run(main())
