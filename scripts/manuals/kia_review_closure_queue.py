import json,pathlib,re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
R=pathlib.Path(__file__).resolve().parents[2];L=R/'.local/manual-review/2026-10-28/kia';O=R/'data/manual-review/2026-10-28'
def read(p):return json.loads(p.read_text('utf8'))
main=read(O/'kia-crossref-reviewed.json');assist=read(O/'kia-crossref-reviewed-hyundai-assist.json');main['entries'].update(assist['entries']);main['sourceReadingComplete']=True;main['requiredReferenceClosureComplete']=False
(O/'kia-crossref-reviewed.json').write_text(json.dumps(main,ensure_ascii=False,indent=2),'utf8')
known={o['source_url'].split('#')[0] for x in main['entries'].values() for o in x['occurrences']}
known.update(read(O/'kia-direct-reviewed.json'))
ad=read(O/'audit-kia-adas-review.json');known.update(x['sourceURL'].split('#')[0] for x in ad['rows']+ad.get('additionalRows',[]))
q={};legacy={}
for i,x in enumerate(read(L/'direct-ref-unread-bodies.json')):
 title=x['title']; selected=[]
 if any(w in title for w in ['AUTO HOLD','스마트 회생','차체자세','ISG','전자식 파킹','타이어 공기압']):selected=x['children']
 elif '디지털' in title and '키' in title:selected=[a for a in x['children'] if any(w in a['label'] for w in ['제한','정비']) or (i in [85,108] and any(w in a['label'] for w in ['스마트폰','카드']))]
 elif '퓨즈' in title:selected=[a for a in x['children'] if any(w in a['label'] for w in ['실내','차단 플러그'])]
 elif i in [14,110,169]:selected=x['children']
 elif i==96:selected=x['children']
 for a in selected:
  if a['url']==x['url'] or a['url'] in known:continue
  q.setdefault(a['url'],{'url':a['url'],'label':a['label'],'parents':[]})['parents'].append(x['url'])
for x in main['entries'].values():
 for o in x['occurrences']:
  url=o['source_url'].split('#')[0]
  if 'chapter' not in url:continue
  s=BeautifulSoup((R/o['local_path']).read_bytes(),'lxml');b=s.select_one('.topic-contents.main-page')
  if not b:continue
  stem=url.rsplit('/',1)[-1].replace('.html','')
  for a in b.select('a[href]'):
   u=urljoin(url,a['href']).split('#')[0]
   if u in known or not u.rsplit('/',1)[-1].startswith(stem+'_'):continue
   legacy.setdefault(u,{'url':u,'label':a.get_text(' ',strip=True),'parents':[]})['parents'].append(url)
for k in list(q):
 if k in legacy:del q[k]
(L/'closure-child-queue.json').write_text(json.dumps(list(q.values()),ensure_ascii=False,indent=2),'utf8')
(L/'legacy-child-queue.json').write_text(json.dumps(list(legacy.values()),ensure_ascii=False,indent=2),'utf8')
print('direct necessary child candidates',len(q),'legacy children',len(legacy))
print('legacy',[(x['label'],x['url']) for x in legacy.values()])
