"""Acquire official Korean Kia manuals; originals remain in ignored .local.

Run with Python + httpx + beautifulsoup4 + pymupdf. API routes are taken from
ownersmanual.kia.com's publicly served application JavaScript. No credentials.
HTML acquisition is explicitly partial: TOC plus warning/emergency/maintenance
topics and their relevant child links. This is not an offline website mirror.
"""
from __future__ import annotations
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys
import time
from urllib.parse import urljoin, urldefrag, urlencode

import httpx
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parents[2]
DAY = '2026-10-28'
RAW = ROOT / '.local/manual-corpus' / DAY / 'kia'
OUT = ROOT / 'data/manual-research' / DAY
BASE = 'https://ownersmanual.kia.com'
PARAMS = {'countryCode': 'A99', 'langCode': 'ko_KR'}
CLIENT = httpx.Client(timeout=45, follow_redirects=True, headers={'User-Agent': 'CHECKMATE-manual-research/0.1 (local research; polite cached requests)'})
NOW = dt.datetime.now(dt.timezone.utc).isoformat()
# Current core model families observed on Kia Korean sales pages; archives still
# receive a catalog row so exclusions cannot disappear from the denominator.
CURRENT = {'DL3','GL3','RJ','TAM','JA','SP2','NQ5','MQ4','KA4','KA4HI','TK1','SW1K','PU','SV1','CT1','OV1K','CV1','MV1','DL3KH','GL3KH','SG2','TAMEV','PUEV','NQ5KH','MQ4KH','KA4KH'}
SEED = re.compile(r'경고|표시등|클러스터|계기판|LCD 표시|응급|비상|고장|타이어|냉각|오일|브레이크|제동|차량 안전|에어백|조향|배터리|견인|전기 자동차 주행|충전되지|하이브리드.*(주행|시스템)|정기 점검|일상 점검|화재')
TOPICS = {
    'TPMS': r'TPMS|공기압|저압 타이어', 'ABS': r'\bABS\b|안티록',
    'BRAKE_EBD': r'EBD|브레이크.*경고|브레이크액|제동.*경고',
    'ENGINE_OIL': r'엔진 오일.*경고|엔진 오일 압력|유압 경고',
    'CHARGING_12V': r'충전 경고등|보조 배터리|12V 배터리',
    'COOLANT': r'냉각수.*경고|과열', 'MIL': r'엔진 경고등|엔진 이상|배출가스',
    'ESC': r'\bESC\b|차체 자세 제어', 'EPS': r'\bEPS\b|전동 파워|전동식 파워|MDPS',
    'AIRBAG': r'에어백 경고등', 'MASTER': r'통합 경고|마스터 경고',
    'EV_SERVICE': r'서비스 경고등|전기차 시스템.*점검|전기차.*경고',
    'POWER_DOWN': r'파워다운|출력 제한', 'HV_BATTERY': r'고전압 배터리|구동용 배터리|배터리 충전량',
    'HEV_SYSTEM': r'하이브리드 시스템|하이브리드.*경고',
}

def save_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf8')

def fetch(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size:
        return path.read_bytes()
    for attempt in range(3):
        try:
            r = CLIENT.get(url); r.raise_for_status()
            path.write_bytes(r.content)
            time.sleep(.08)
            return r.content
        except Exception:
            if attempt == 2: raise
            time.sleep(1 + attempt)

def api(route, params, path):
    url = BASE + route + '?' + urlencode(params)
    return json.loads(fetch(url, path)), url

def file_meta(path, url):
    body = path.read_bytes()
    return {'source_url': url, 'local_path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(body).hexdigest(), 'bytes': len(body)}

def text_html(body):
    soup = BeautifulSoup(body, 'html.parser')
    article = soup.select_one('main') or soup.select_one('article') or soup
    return soup, article, article.get_text(' ', strip=True)

def acquire(model):
    key = f"{model['projCode']}_{model['year']}"
    folder = RAW / key
    record = {'id': 'kia_' + key, 'brand': 'Kia', 'model': model['modelName'], 'model_code': model['projCode'],
              'source_label_year': int(model['year']), 'powertrain': model.get('fuel'), 'market': 'KR', 'language':'ko_KR',
              'checked_at_utc': NOW, 'landing_url': BASE + '/main', 'status':'pending', 'assets': [],
              'review_status':'acquired_unreviewed', 'publication_date': None, 'uncertainties':[]}
    try:
        detail, endpoint = api('/api/v2/kia/model/owners-manuals', {**PARAMS,'projectCode':model['projCode'],'year':model['year']},folder/'manual-metadata.json')
        record['metadata_url']=endpoint
        om=detail.get('omManual',{})
        record['latest_evidence']={'selection':'highest year returned by official model catalog','web_publication':om.get('webhelpPubdate'),'pdf_publication':om.get('pdfPubdate')}
        record['publication_date']=om.get('webhelpPubdate') or om.get('pdfPubdate')
        pdf=om.get('pdfManual')
        if pdf:
            url=urljoin(BASE,pdf); path=folder/'owners-manual.pdf';body=fetch(url,path)
            if not body.startswith(b'%PDF'):raise ValueError('Official PDF URL did not return PDF signature')
            import pymupdf
            doc=pymupdf.open(path); pages=[page.get_text() for page in doc]
            save_json(folder/'pages.json',pages)
            asset=file_meta(path,url);asset.update({'format':'pdf','pages':len(doc),'cover_text_local':(folder/'pages.json').relative_to(ROOT).as_posix()})
            record['assets'].append(asset);record['pdf_pages']=len(doc)
            record['cover_model_token_found']=any(token.lower() in '\n'.join(pages[:8]).lower() for token in [model['modelName'],model['projCode']])
            record['warning_locators']=[{'warning_type':topic,'pdf_pages_1based':[i+1 for i,t in enumerate(pages) if re.search(pattern,t,re.I)],'status':'automated_keyword_candidates'} for topic,pattern in TOPICS.items()]
            record['status']='full_pdf_acquired';return record
        web=om.get('webhelpManual');toc=om.get('webhelpToc')
        if not web:
            record['status']='owner_manual_unavailable';record['uncertainties'].append('No full owner manual PDF or HTML URL in official metadata');return record
        web=urljoin(BASE,web); toc=urljoin(web,toc or 'toc.html')
        record['manual_url']=web;record['toc_url']=toc
        body=fetch(toc,folder/'toc.html');soup=BeautifulSoup(body,'html.parser')
        title=soup.title.get_text() if soup.title else ''
        record['document_title']=title
        record['model_year_title_check']=model['projCode'].upper() in title.upper() and str(model['year']) in title and 'ko_KR' in title
        record['assets'].append(file_meta(folder/'toc.html',toc))
        all_links={urldefrag(urljoin(toc,a['href']))[0]:a.get_text(' ',strip=True) for a in soup.select('a[href]') if '/topics/' in urljoin(toc,a['href'])}
        save_json(folder/'toc-links.json',all_links)
        record['toc_topic_count']=len(all_links)
        todo={url:title for url,title in all_links.items() if SEED.search(title)}
        done={};errors=[];prefix=web.rsplit('/',1)[0]+'/topics/'
        for depth in range(3):
            if not todo:break
            next_links={}
            for url,title in todo.items():
                if url in done:continue
                path=folder/'topics'/url.rsplit('/',1)[-1]
                try:
                    body=fetch(url,path);soup,article,plain=text_html(body)
                    if not soup.select_one('main, article, h1, h2'):raise ValueError('Not a manual topic')
                    path.with_suffix('.txt').write_text(plain,encoding='utf8')
                    asset=file_meta(path,url);asset.update({'title':soup.title.get_text() if soup.title else title,'format':'html','review_status':'automated_keyword_candidates'})
                    asset['navigation_only']=len(plain)<8
                    asset['warning_types']=[topic for topic,pattern in TOPICS.items() if re.search(pattern,plain,re.I)]
                    done[url]=asset
                    # Some warning headings are only linked by the local TOC,
                    # not the article body; include the navigation tree too.
                    for a in soup.select('a[href]'):
                        link=urldefrag(urljoin(url,a['href']))[0];text=a.get_text(' ',strip=True)
                        if link.startswith(prefix) and link not in done and SEED.search(text):next_links[link]=text
                except Exception as exc:errors.append({'url':url,'error':str(exc)})
            todo=next_links
        record['assets'].extend(done.values());record['html_topic_count']=len(done)
        record['warning_locators']=[{'warning_type':topic,'urls':[u for u,a in done.items() if topic in a['warning_types']],'status':'automated_keyword_candidates'} for topic in TOPICS]
        record['acquisition_errors']=errors
        record['status']='partial_html_warning_emergency_acquired'
        record['uncertainties'].append('TOC and selected topics acquired, not complete manual/assets. Keyword absence is not proof of non-applicability. Exact trim and paired-state guidance require review.')
    except Exception as exc:record['status']='acquisition_failed';record['error']=str(exc)
    return record

def main():
    RAW.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    catalog,url=api('/api/v2/kia/models',PARAMS,RAW/'catalog.json')
    rows=[r for group in catalog.values() for r in group]
    catalog_rows=[];targets=[]
    for row in rows:
        detail,endpoint=api('/api/v3/kia/model',{**PARAMS,'modelName':row['langModelName']},RAW/'models'/(row['modelId']+'.json'))
        years=detail.get('years',[]);latest=max(years,key=int) if years else None
        scope='current_core_family' if row['modelId'] in CURRENT else ('excluded_bus' if row['modelId']=='GZ' else 'archive_not_current_sales_lineup')
        selected=detail.get('yearModels',{}).get(latest,[])
        catalog_rows.append({'model':row['langModelName'],'catalog_model_code':row['modelId'],'available_years':years,'latest_catalog_year':latest,'scope':scope,'model_metadata_url':endpoint,'selected_variants':selected})
        if scope=='current_core_family':targets.extend(selected)
    save_json(OUT/'kia_catalog.json',{'checked_at_utc':NOW,'catalog_url':url,'models':catalog_rows,'scope_notes':'Core families checked against Korean current sales EV/sedan/RV/PBV/commercial pages. Special bodies and GT coverage require separate content verification. Archives are inventoried but not downloaded.'})
    targets=list({(m['projCode'],m['year']):m for m in targets}.values())
    print('catalog',len(rows),'selected variants',len(targets),flush=True)
    results=[]
    with cf.ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(acquire,m):m for m in targets}
        for future in cf.as_completed(futures):
            result=future.result();results.append(result)
            print(result['id'],result['status'],result.get('html_topic_count',result.get('pdf_pages')),flush=True)
            save_json(OUT/'kia_manifest.json',{'checked_at_utc':NOW,'documents':sorted(results,key=lambda r:r['id'])})
    print('done',len(results),flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');main()
