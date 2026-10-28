"""Prepare source differences for direct review, never auto-approve them."""
import json,re,difflib,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'.local/manual-review/2026-10-28/hyundai'
INV=json.loads((ROOT/'data/manual-review/2026-10-28/hyundai-inventory.json').read_text(encoding='utf-8'))
def text(code):
 s=next(x for x in INV['sections'] if x['documentId']==code and x['title']=='cluster_warning_indicator_and_messages')
 t=(ROOT/s['localPassagePath']).read_text(encoding='utf-8')
 # Formatting normalization only; numbers, units, negations and wording are retained.
 t=re.sub(r'\[PDF PAGE \d+\]|ঌইفӝ|઱੄|҃\s*Ҋ','',t)
 t=re.sub(r'\s+','',t).replace('•','').replace('‘',"'").replace('’',"'").replace('「',"'").replace('」',"'")
 return s,t
def main():
 base,var=sys.argv[1:3];aS,a=text(base);bS,b=text(var)
 ops=[]
 for op,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
  if op!='equal':ops.append((i,j,k,l))
 groups=[]
 for x in ops:
  if groups and x[2]-groups[-1][3]<70:
   old=groups[-1];groups[-1]=(old[0],x[1],old[2],x[3])
  else:groups.append(x)
 rows=[]
 for i,j,k,l in groups:
  rows.append({'baseChange':a[i:j],'variantChange':b[k:l],'variantContext':b[max(0,k-70):min(len(b),l+70)]})
 result={'baseDocumentId':base,'variantDocumentId':var,'baseSectionId':aS['id'],'variantSectionId':bS['id'],'variantPassageSha256':bS['passageSha256'],'reviewStatus':'DIFF_PREPARED_NOT_REVIEWED','differences':rows}
 p=RAW/f'{base}--{var}-diff.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 for i,r in enumerate(rows):print(i,'CHANGE',r['baseChange'],'=>',r['variantChange'],'\nCONTEXT',r['variantContext'])
 print('groups',len(rows),'path',p)
if __name__=='__main__':main()
