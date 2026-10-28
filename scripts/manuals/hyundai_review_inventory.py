"""Create a read-only review inventory. Extraction is NOT semantic approval.

Raw passages stay in ignored .local. This script never marks SOURCE_REVIEWED.
Run with uv run --no-project --with pymupdf==2.0 python scripts/manuals/hyundai_review_inventory.py
"""
import hashlib
import json
from pathlib import Path
import re
import pymupdf

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / '.local/manual-review/2026-10-28/hyundai'
OUT = ROOT / 'data/manual-review/2026-10-28'
MANIFEST = ROOT / 'data/manual-research/2026-10-28/hyundai-manifest.json'

def js_json(path):
    s=path.read_text(encoding='utf-8-sig')
    return json.loads(s[s.index('{'):s.rindex('}')+1])

def flatten(tree):
    out={}
    def visit(node):
        if isinstance(node,dict):
            for key,val in node.items():
                if isinstance(val,list) and len(val)>=2:
                    out[key]={'title':val[0],'path':val[1]}
                    if len(val)>2:visit(val[2])
    visit(tree);return out

def section_end(toc,index,pages):
    level,title,start=toc[index]
    return next((x[2] for x in toc[index+1:] if x[0]<=level and x[2]>start),pages)

def main():
    RAW.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    records=[];units=[]
    for doc in json.loads(MANIFEST.read_text(encoding='utf-8'))['documents']:
        ident=f"HYUNDAI-{doc['modelCode']}-{doc['year']}"
        record={'documentId':ident,'model':doc['model'],'modelCode':doc['modelCode'],'year':int(doc['year']),'powertrain':doc.get('powertrain'),'sourceURL':doc['sourceURL'],'sourceSha256':doc.get('sha256'),'manualRole':'special_equipment_pending_role_review' if doc['modelCode'] in {'US4SV','HRSV'} else 'base_manual','sections':[]}
        if doc['status']=='downloaded':
            ps=json.loads((ROOT/doc['textPagesPath']).read_text(encoding='utf-8'))
            with pymupdf.open(ROOT/doc['localPath']) as pdf:toc=pdf.get_toc()
            if doc['modelCode'] in {'US4SV','HRSV'}:
                ranges=[('special_equipment_manual',1,len(ps))]
            elif doc['modelCode'] in {'HREV','QX','HR','CN7N'}:
                start,end={'HREV':(111,120),'QX':(85,98),'HR':(117,132),'CN7N':(79,91)}[doc['modelCode']]
                ranges=[('cluster_warning_indicator_and_messages',start,end)]
            else:
                start=next(x[2] for x in toc if '경고등 및 표시등' in x[1] and x[2]>50)
                end=next(x[2] for x in toc if x[2]>start and x[1] in {'클러스터 설정하기','클러스터 표시창'})
                ranges=[('cluster_warning_indicator_and_messages',start,end)]
            # Relevant supporting procedures are separately inventoried; none auto-reviewed.
            for index,x in enumerate(toc):
                if re.search(r'^(타이어 공기압|타이어 펑크|브레이크액|엔진 오일|냉각수|엔진이 과열|배터리|점프 스타트|전기차.*사고|전기차.*화재|매연 필터|배출가스|요소수|물빼기|경고등/표시등)',x[1]):
                    ranges.append((x[1],x[2],section_end(toc,index,len(ps))))
            seen=set()
            for title,start,end in ranges:
                key=(start,end)
                if key in seen:continue
                seen.add(key)
                pages=[{'pdfPage':i,'text':ps[i-1]} for i in range(start,min(end,len(ps))+1)]
                sid=f'{ident}-p{start}-{end}'
                text='\n'.join(f"[PDF PAGE {x['pdfPage']}]\n{x['text']}" for x in pages)
                target=RAW/f'{sid}.txt';target.write_text(text,encoding='utf-8')
                unit={'id':sid,'documentId':ident,'title':title,'locator':{'pdfPages1Based':list(range(start,min(end,len(ps))+1))},'sourceURL':doc['sourceURL']+f'#page={start}','sourceSha256':doc['sha256'],'localPassagePath':target.relative_to(ROOT).as_posix(),'passageSha256':hashlib.sha256(text.encode()).hexdigest(),'characters':len(text),'reviewStatus':'INVENTORIED_NOT_REVIEWED','runtimeApproved':False}
                record['sections'].append(sid);units.append(unit)
        else:
            directory=ROOT/doc['localPath'];toc=flatten(js_json(directory/'data/tocData.json'));search=js_json(directory/'data/searchData.json')
            resources={r['url']:r for r in doc['resources']}
            for key,node in toc.items():
                title=node['title'];path=node['path']
                if not (re.search(r'경고등|표시등|클러스터 메시지|저압|공기압 경보|브레이크액|엔진 오일|냉각수|과열|점프 스타트|물빼기|매연 필터|요소수|배출가스',title) or path.startswith('cluster-') and 'message' in path):continue
                text='\n'.join(search.get(key,[]))
                if not text:continue
                sid=f'{ident}-{key}';target=RAW/f'{sid}.txt';target.write_text(text,encoding='utf-8')
                url=doc['webURL'].rsplit('/',1)[0]+'/'+path
                unit={'id':sid,'documentId':ident,'title':title,'locator':{'topicId':key,'path':path},'sourceURL':url,'sourceSha256':resources.get(url,{}).get('sha256'),'localPassagePath':target.relative_to(ROOT).as_posix(),'passageSha256':hashlib.sha256(text.encode()).hexdigest(),'characters':len(text),'reviewStatus':'INVENTORIED_NOT_REVIEWED','runtimeApproved':False}
                record['sections'].append(sid);units.append(unit)
        records.append(record)
    result={'version':1,'scope':'Cluster warnings/indicators/messages and relevant supporting procedure candidates. Every item starts unreviewed.','reviewer':'AI','runtimeApproved':False,'documents':records,'sections':units}
    (OUT/'hyundai-inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('documents',len(records),'sections',len(units),'characters',sum(x['characters'] for x in units))
    print('cluster chars',sum(x['characters'] for x in units if 'cluster_warning' in x['title'] or '경고등' in x['title']))

if __name__=='__main__':main()
