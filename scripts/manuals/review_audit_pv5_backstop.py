import json,re,hashlib,concurrent.futures
from pathlib import Path
import httpx
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'.local/manual-review/2026-10-28/audit/kia-adas';OUT=ROOT/'data/manual-review/2026-10-28';BASE='https://ownersmanual.kia.com/full_webhelp/SW1K/2027/ko_KR/topics/'
manifest=json.loads((RAW/'manifest.json').read_text(encoding='utf8'));paths={e['sourceURL']:ROOT/e['localPath'] for e in manifest}
old=json.loads((OUT/'audit-kia-adas-review.json').read_text(encoding='utf8'));seen={r['sourceURL'] for r in old['rows']+old['additionalRows']}
dest=RAW/'pv5-backstop';dest.mkdir(exist_ok=True)
def get(i):
 name=f't{i:05}.html';url=BASE+name;p=paths.get(url,RAW/'kia_SW1K_2027'/name)
 if not p.exists():
  p=dest/name
  if not p.exists():
   r=httpx.get(url,timeout=40);r.raise_for_status();p.write_bytes(r.content)
 s=BeautifulSoup(p.read_bytes(),'lxml');b=s.select_one('main article') or s.select_one('main')
 if not b:return None
 h=b.find(re.compile('^h[1-6]$'));title=h.get_text(' ',strip=True) if h else '';text=b.get_text('\n',strip=True)
 return dict(sourceURL=url,sourceSha256=hashlib.sha256(p.read_bytes()).hexdigest(),localPath=str(p.relative_to(ROOT)),title=title,text=text,alreadyRead=url in seen)
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:es=list(filter(None,ex.map(get,list(range(206,214))+list(range(512,724)))) )
(dest/'all.json').write_text(json.dumps(es,ensure_ascii=False,indent=2),encoding='utf8')
selected=[e for e in es if not e['alreadyRead'] and (re.search('이상|가림|센서|하이빔',e['title']) or re.search('서비스센터|부드러운|고압|화학',e['text']))]
known={u['hash'] for f in ['review-units.json','extra-review-units.json'] for u in json.loads((RAW/f).read_text(encoding='utf8'))};us=[];lookup={}
for i,e in enumerate(selected):
 for line in e['text'].splitlines():
  ha=hashlib.sha256(re.sub(r'\s+','',line).encode()).hexdigest()
  if ha in known:continue
  if ha in lookup:us[lookup[ha]]['entries'].append(i)
  else:lookup[ha]=len(us);us.append(dict(id=len(us),text=line,hash=ha,entries=[i]))
(dest/'inventory.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2),encoding='utf8');(dest/'units.json').write_text(json.dumps(us,ensure_ascii=False,indent=2),encoding='utf8')
for i in range(0,len(us),100):(dest/f'read-{i//100:02}.txt').write_text('\n'.join(str(u['id'])+' '+u['text'] for u in us[i:i+100]),encoding='utf8')
print('all',len(es),'new required sections',len(selected),'units',len(us))
