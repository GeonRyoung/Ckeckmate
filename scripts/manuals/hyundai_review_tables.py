"""Extract table row candidates for manual review; no semantic approval is issued."""
import json,re,hashlib
from pathlib import Path
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'.local/manual-review/2026-10-28/hyundai'

def main():
    inventory=json.loads((ROOT/'data/manual-review/2026-10-28/hyundai-inventory.json').read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/'data/manual-research/2026-10-28/hyundai-manifest.json').read_text(encoding='utf-8'))['documents']
    docs={f"HYUNDAI-{d['modelCode']}-{d['year']}":d for d in manifest}
    out=[];notables=[]
    for sec in inventory['sections']:
        if sec['title']!='cluster_warning_indicator_and_messages':continue
        doc=docs[sec['documentId']];pdf=pymupdf.open(ROOT/doc['localPath']);last=None;count=0
        for number in sec['locator']['pdfPages1Based']:
            page=pdf[number-1]
            for table in page.find_tables().tables:
                if table.col_count not in [2,3]:continue
                edges=sorted(set(round(c[0],3) for row in table.rows for c in row.cells if c) | set(round(c[2],3) for row in table.rows for c in row.cells if c))
                for row in table.rows:
                    rects=[c if c else (edges[j],row.bbox[1],edges[j+1],row.bbox[3]) if len(edges)==table.col_count+1 else None for j,c in enumerate(row.cells)]
                    cells=[page.get_text(clip=pymupdf.Rect(c)).strip() if c else '' for c in rects]
                    label=cells[0]
                    if re.sub(r'\s+','',label) in {'경고등','표시등','메시지/표시정보','메시지','구분','원인','설명','표시등설명'}:continue
                    if not re.search('[가-힣]',label):
                        if last and any(re.search('[가-힣]',c) for c in cells[1:]):
                            last['cells'][-1]+='\n[CONTINUED]\n'+'\n'.join(cells[1:]);last['pages'].append(number)
                        continue
                    if len(cells[0])>110:continue
                    last={'id':f"{sec['id']}-row{count+1}",'sectionId':sec['id'],'documentId':sec['documentId'],'pages':[number],'cells':cells,'label':label,'sourceURL':doc['sourceURL']+f'#page={number}','sourceSha256':doc['sha256']}
                    out.append(last);count+=1
        pdf.close()
        if count==0:notables.append(sec['documentId'])
        print(sec['documentId'],count,flush=True)
    groups={}
    for row in out:
        text=' | '.join(row['cells'])
        key=re.sub(r'[\s•]+','',text)
        digest=hashlib.sha256(key.encode()).hexdigest()
        row['rowTextSha256']=digest
        group=groups.setdefault(digest,{'rowTextSha256':digest,'cells':row['cells'],'occurrences':[]})
        group['occurrences'].append({k:v for k,v in row.items() if k not in {'cells','label','rowTextSha256'}})
    result={'rows':out,'uniqueRows':list(groups.values()),'documentsWithoutTables':notables,'reviewStatus':'EXTRACTED_NOT_REVIEWED'}
    (RAW/'table-row-candidates.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('rows',len(out),'unique',len(groups),'characters',sum(len(' '.join(x['cells'])) for x in groups.values()),'notables',notables)

if __name__=='__main__':main()
