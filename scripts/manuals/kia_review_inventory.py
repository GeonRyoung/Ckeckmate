"""Inventory original Kia warning sections. Inventory is not semantic approval."""
from __future__ import annotations
import hashlib, json, pathlib, re
from urllib.parse import urljoin
from bs4 import BeautifulSoup

ROOT=pathlib.Path(__file__).resolve().parents[2]
RAW=ROOT/'.local/manual-review/2026-10-28/kia'
OUT=ROOT/'data/manual-review/2026-10-28'
RAW.mkdir(parents=True,exist_ok=True)
OUT.mkdir(parents=True,exist_ok=True)
manifest=json.loads((ROOT/'data/manual-research/2026-10-28/kia_manifest.json').read_text('utf8'))
for extra in sorted((ROOT/'.local/manual-review/2026-10-28/audit').glob('*2025-acquired.json')):
    manifest['documents'].append(json.loads(extra.read_text('utf8')))
if (RAW/'additional-assets.json').exists():
    extra=json.loads((RAW/'additional-assets.json').read_text('utf8'))
    for doc in manifest['documents']:doc['assets'].extend(extra.get(doc['id'],[]))
title_pattern=re.compile(r'경고등|표시등|경고 메시지|경고문')
entries=[]
documents=[]
for doc in manifest['documents']:
    selected=[]
    for asset in doc['assets']:
        if asset.get('format')!='html': continue
        if asset.get('title') and not title_pattern.search(asset['title']): continue
        soup=BeautifulSoup((ROOT/asset['local_path']).read_bytes(),'lxml')
        main=soup.select_one('main') or soup.select_one('.topic-contents.main-page') or soup
        article=main.select_one('article') or main
        top=article.find(re.compile('^h[1-6]$'))
        title=top.get_text(' ',strip=True) if top else asset['title']
        if not title_pattern.search(title): continue
        selected.append({'url':asset['source_url'],'title':title})
        sections=[s for s in article.select('section, div.section') if s.find(re.compile('^h[1-6]$'),recursive=False)]
        if not sections: sections=[article]
        expanded=[]
        for section in sections:
            tables=section.select('table')
            if len(section.get_text())>2500 and tables and not section.select('section, div.section'):
                for table in tables:
                    current=None
                    for tr in table.select('tr'):
                        cells=tr.find_all(['th','td'],recursive=False)
                        if not cells or cells[0].name=='th':continue
                        if len(cells)>=4:
                            current=BeautifulSoup('<section><h2></h2></section>','lxml').section
                            current.h2.string=cells[0].get_text(' ',strip=True)
                            if tr.get('id'):current['id']=tr['id']
                            expanded.append(current)
                        if current:
                            para=BeautifulSoup('<p></p>','lxml').p
                            for cell in cells[-2:]:para.append(BeautifulSoup(str(cell),'lxml'))
                            current.append(para)
                cloned=BeautifulSoup(str(section),'lxml')
                for table in cloned.select('table'):table.decompose()
                if len(cloned.get_text(' ',strip=True))>80:expanded.append(cloned)
            else:expanded.append(section)
        sections=expanded
        for section in sections:
            heading=section.find(re.compile('^h[1-6]$'))
            label=heading.get_text(' ',strip=True) if heading else title
            txt=section.get_text(' ',strip=True)
            txt=re.sub(r'\s+',' ',txt).strip()
            key=hashlib.sha256(txt.encode()).hexdigest()
            loc=asset['source_url']+('#'+section['id'] if section.get('id') else '')
            links=[{'label':a.get_text(' ',strip=True),'url':urljoin(asset['source_url'],a['href'])} for a in section.select('a[href]') if '/topics/' in urljoin(asset['source_url'],a['href'])]
            entries.append({'document_id':doc['id'],'model':doc['model'],'model_year':doc['source_label_year'],'powertrain_catalog':doc['powertrain'],'label':label,'section_text_hash':key,'source_url':loc,'asset_sha256':asset['sha256'],'source_local_path':asset['local_path'],'cross_references':links,'source_text':txt,'review_status':'INVENTORIED_NOT_REVIEWED'})
    documents.append({'document_id':doc['id'],'model':doc['model'],'selected_topics':selected,'status':'SUPPLEMENT_DELEGATED' if doc['id']=='kia_KA4HI_2025' else 'INVENTORIED_NOT_REVIEWED'})
unique={}
for entry in entries:
    key=entry['section_text_hash']
    if key not in unique: unique[key]={'key':key,'label':entry['label'],'text':entry['source_text'],'occurrences':[],'cross_references':entry['cross_references']}
    unique[key]['occurrences'].append({'document_id':entry['document_id'],'source_url':entry['source_url']})
for i,item in enumerate(unique.values(),1):item['sequence']=i
(RAW/'unique-sections.json').write_text(json.dumps(list(unique.values()),ensure_ascii=False,indent=2),'utf8')
(RAW/'inventory-with-text.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),'utf8')
public=[{k:v for k,v in e.items() if k!='source_text'} for e in entries]
(OUT/'kia-inventory.json').write_text(json.dumps({'scope':'warning/indicator topic sections selected by titles; references require separate review','documents':documents,'entries':public,'unique_sections':len(unique),'all_reviewed':False},ensure_ascii=False,indent=2),'utf8')
print('documents',len(documents),'entries',len(entries),'unique',len(unique),'chars',sum(len(i['text']) for i in unique.values()))
for d in documents:print(d['document_id'],[(s['url'].rsplit('/',1)[-1],s['title']) for s in d['selected_topics']])
