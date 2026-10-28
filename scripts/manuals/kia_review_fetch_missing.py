"""Follow observed next-page links to fill missing cluster chapters. No guessed URLs."""
import json,pathlib,hashlib
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[2]
RAW=ROOT/'.local/manual-review/2026-10-28/kia'
manifest=json.loads((ROOT/'data/manual-research/2026-10-28/kia_manifest.json').read_text('utf8'))
out={}
with httpx.Client(timeout=30,follow_redirects=True) as client:
 for d in manifest['documents']:
  if d['id'] not in ['kia_KA4_2027','kia_MQ4KH_2027']:continue
  sources={a['source_url']:a for a in d['assets']}
  seed=next(a for a in d['assets'] if a.get('title')=='클러스터')
  url=seed['source_url'];seen=set();new=[]
  for _ in range(35):
   if url in seen:break
   seen.add(url)
   if url in sources:body=(ROOT/sources[url]['local_path']).read_bytes()
   else:
    path=RAW/d['id']/url.rsplit('/',1)[-1];path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():body=path.read_bytes()
    else:r=client.get(url);r.raise_for_status();body=r.content;path.write_bytes(body)
    soup=BeautifulSoup(body,'lxml');main=soup.select_one('main') or soup;h=main.find(['h1','h2','h3'])
    new.append({'source_url':url,'local_path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body),'title':h.get_text(' ',strip=True) if h else '', 'format':'html'})
   soup=BeautifulSoup(body,'lxml');n=soup.select_one('[rel=next]')
   if not n:break
   url=urljoin(url,n['href'])
  out[d['id']]=new
(RAW/'additional-assets.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),'utf8')
print({k:len(v) for k,v in out.items()})
