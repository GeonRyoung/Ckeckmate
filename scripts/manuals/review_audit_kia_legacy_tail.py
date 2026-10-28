import json,re,hashlib,concurrent.futures
from pathlib import Path
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'.local/manual-review/2026-10-28/audit/kia-legacy-tail';RAW.mkdir(exist_ok=True);queue=json.loads((ROOT/'.local/manual-review/2026-10-28/kia/legacy-child-queue.json').read_text(encoding='utf8'))[:57]
def fetch(x):
 url=x['url'];parts=url.split('/');p=RAW/(parts[4]+'-'+parts[5]+'-'+parts[-1])
 if not p.exists():r=httpx.get(url,timeout=40);r.raise_for_status();p.write_bytes(r.content)
 s=BeautifulSoup(p.read_bytes(),'lxml');b=s.select_one('.topic-contents.main-page') or s.select_one('main article') or s.select_one('main');text=b.get_text('\n',strip=True) if b else '';links=[{'label':a.get_text(' ',strip=True),'url':urljoin(url,a['href'])} for a in b.select('a[href]') if Path(urljoin(url,a['href'])).stem.startswith(Path(url).stem+'_')] if b else []
 return dict(**x,sourceSha256=hashlib.sha256(p.read_bytes()).hexdigest(),localPath=str(p.relative_to(ROOT)),text=text,childLinks=links)
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:es=list(ex.map(fetch,queue))
known={e['url'] for e in es};children=[c for e in es for c in e['childLinks'] if c['url'] not in known];extra=[]
for c in children:
 if c['url'] not in known:known.add(c['url']);extra.append(fetch(c))
es+=extra;units=[];seen={}
for i,e in enumerate(es):
 for line in e['text'].splitlines():
  h=hashlib.sha256(re.sub(r'\s+','',line).encode()).hexdigest()
  if h in seen:units[seen[h]]['entries'].append(i)
  else:seen[h]=len(units);units.append(dict(id=len(units),hash=h,text=line,entries=[i]))
(RAW/'inventory.json').write_text(json.dumps(es,ensure_ascii=False,indent=2),encoding='utf8');(RAW/'units.json').write_text(json.dumps(units,ensure_ascii=False,indent=2),encoding='utf8')
for i in range(0,len(units),100):(RAW/f'read-{i//100:02}.txt').write_text('\n'.join(str(u['id'])+' '+u['text'] for u in units[i:i+100]),encoding='utf8')
print('pages',len(es),'unique lines',len(units),'chars',sum(len(u['text']) for u in units))
