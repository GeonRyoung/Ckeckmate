"""Readable unique units for ADAS fault/obstruction scope, not a review approval."""
import json,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'data/manual-review/2026-10-28';RAW=ROOT/'.local/manual-review/2026-10-28/audit/adas'
def main():
 es=json.loads((OUT/'audit-hyundai-adas-inventory.json').read_text(encoding='utf8'))['entries'];units={}
 for i,e in enumerate(es):
  text=(ROOT/e['localTextPath']).read_text(encoding='utf8')
  compact=re.sub(r'\s+','',text)
  starts=[m.start() for m in re.finditer('이상및제한|이상및작동제한|고장및제한',compact)]
  if starts:compact=compact[starts[0]:]
  # All fault and obstruction paragraphs preceding general performance limitations.
  compact=re.split('작동제한사항|작동제한조건|기능의제한',compact,maxsplit=1)[0]
  compact=re.sub(r'\[PDF\d+\]|2C_[A-Za-z0-9_]+|B[0-9]+[A-Za-z_]+','',compact)
  sentences=re.split(r'(?<=[.!?。])',compact)
  for s in sentences:
   if len(s)<12:continue
   h=hashlib.sha256(s.encode()).hexdigest()
   units.setdefault(h,{'id':len(units),'hash':h,'text':s,'entries':[]})['entries'].append(i)
 data=list(units.values())
 (RAW/'fault-units.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
 print(len(data),sum(len(u['text']) for u in data))
 for j in range(0,len(data),70):
  (RAW/f'fault-read-{j//70:02}.txt').write_text('\n'.join(f"[{u['id']}] {u['text']}" for u in data[j:j+70]),encoding='utf8')
if __name__=='__main__':main()
