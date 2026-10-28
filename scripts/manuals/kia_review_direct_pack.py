import json,pathlib,sys,re,difflib
R=pathlib.Path(__file__).resolve().parents[2];L=R/'.local/manual-review/2026-10-28/kia';O=R/'data/manual-review/2026-10-28'
u=json.loads((L/'direct-ref-unread-bodies.json').read_text('utf8'));p=O/'kia-direct-reviewed.json';r=json.loads(p.read_text('utf8')) if p.exists() else {}
def norm(s):return re.sub(r'[^가-힣A-Za-z0-9]','',s).lower()
def clean(s):return re.sub(r'\b(?:O[A-Z0-9_]{7,}|P_CT\w+)\b','',s)
count=int(sys.argv[1]);pack=[]
for i,x in enumerate(u):
 if x['url'] in r:continue
 text=clean(x['text']);bs=[]
 for j,y in enumerate(u):
  if y['url'] in r and norm(x['title'])==norm(y['title']):bs.append((difflib.SequenceMatcher(None,clean(y['text']),text,autojunk=False).ratio(),j,y))
 ratio,j,y=max(bs,key=lambda z:z[0]) if bs else (0,None,None)
 print('\nUNIT',i,x['url'],x['title'],'FROM',','.join(x['from']))
 if ratio>=.90:
  print('BASIS',j,round(ratio,3));a=clean(y['text']);b=text
  for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
   if tag!='equal' and norm(a[i1:i2])!=norm(b[j1:j2]):print(b[max(0,j1-12):j1],repr(a[i1:i2]),'→',repr(b[j1:j2]),b[j2:j2+12])
 else:print('FULL',text)
 print('CHILDREN',[(a['label'],a['url'].rsplit('/',1)[-1]) for a in x['children']])
 pack.append({'index':i,'url':x['url'],'basis':y['url'] if ratio>=.90 else None})
 if len(pack)>=count:break
(L/'direct-latest-pack.json').write_text(json.dumps(pack,ensure_ascii=False,indent=2),'utf8')
