"""Audit acquired Kia assets and record sales-product scope and review examples."""
import datetime as dt
import hashlib
import json
import pathlib
from urllib.parse import urlparse
from bs4 import BeautifulSoup

ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'data/manual-research/2026-10-28'
RAW=ROOT/'.local/manual-corpus/2026-10-28/kia'
def write(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')

def main():
    manifest=json.loads((OUT/'kia_manifest.json').read_text(encoding='utf8'))
    documents=manifest['documents'];bycode={d['model_code']:d for d in documents}
    audits=[]
    for d in documents:
        d['manual_role']='owner_manual'
        d['offline_complete']=False
        d['images_css_scripts_acquired']=False
        d['ready_for_production_rag']=False
        d['powertrain_catalog_value']=d['powertrain']
        d['powertrain_applicability_review']='required; API fuel labels can combine or omit powertrains'
        if d['model_code']=='SP3':
            d['content_powertrain_evidence']={'title':d.get('document_title'),'sections':['t00530.html','t00536.html'],'finding':'ICE and HEV sections confirmed; API ICE label is incomplete. PHEV domestic applicability is not confirmed.'}
        if d['model_code']=='KA4HI':
            d['manual_role']='supplement'
            d['status']='full_supplement_pdf_acquired_ocr_required'
            d['ocr_status']='required_not_performed'
            d['text_extraction_characters']=sum(len(t) for t in json.loads((RAW/'KA4HI_2025/pages.json').read_text(encoding='utf8')))
            d['cover_visual_review']='Cover says CARNIVAL Hi Limousine; PDF page 2 says this book covers Hi Limousine-specific components and refers to the basic vehicle manual for other items.'
            d['base_manual_candidate_ids']=['kia_KA4_2027','kia_KA4KH_2027']
            d['base_manual_exact_year_match']=False
            d['uncertainties'].append('Latest official supplement catalog label is 2025; base-car manuals acquired here are 2027. Do not substitute them for a 2025 vehicle without a matching base manual and powertrain.')
            for row in d.get('warning_locators',[]):row['status']='unknown_ocr_required_not_absent'
        # Initial crawler classified very short navigation-parent pages as empty.
        # Preserve them as acquired navigation, rather than misreporting download failure.
        unresolved=[]
        for error in d.get('acquisition_errors',[]):
            path=RAW/f"{d['model_code']}_{d['source_label_year']}"/'topics'/error['url'].rsplit('/',1)[-1]
            if error['error']=='Empty topic' and path.exists():
                soup=BeautifulSoup(path.read_bytes(),'html.parser')
                if soup.select_one('main,article,h1,h2'):
                    if not any(a['source_url']==error['url'] for a in d['assets']):
                        body=path.read_bytes();d['assets'].append({'source_url':error['url'],'local_path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body),'format':'html','title':soup.title.get_text() if soup.title else '', 'navigation_only':True,'warning_types':[],'review_status':'automated_navigation_page'})
                    continue
            if error not in unresolved:unresolved.append(error)
        d['acquisition_errors']=unresolved
        if 'html_topic_count' in d:d['html_topic_count']=sum(a.get('format')=='html' for a in d['assets'])
        for asset in d['assets']:
            p=ROOT/asset['local_path'];body=p.read_bytes()
            valid=len(body)==asset['bytes'] and hashlib.sha256(body).hexdigest()==asset['sha256']
            content_valid=body.startswith(b'%PDF') if asset.get('format')=='pdf' else b'<html' in body.lower() or b'<!doctype html' in body.lower()
            audits.append({'document_id':d['id'],'local_path':asset['local_path'],'hash_size_match':valid,'file_signature_valid':content_valid})
            if not valid or not content_valid:raise ValueError(asset['local_path'])
    write(OUT/'kia_manifest.json',manifest)
    lineup=json.loads((OUT/'kia_sales_lineup.json').read_text(encoding='utf8'))
    mapping={'ray-ev':['TAMEV'],'ev3':['SV1'],'ev4':['CT1'],'ev5':['OV1K'],'ev6':['CV1'],'ev9':['MV1'],'bongo3-ev':['PUEV'],'morning':['JA'],'ray':['TAM'],'k5':['DL3','DL3KH'],'k8':['GL3','GL3KH'],'k9':['RJ'],'seltos':['SP3'],'niro':['SG2'],'sportage':['NQ5','NQ5KH'],'sorento':['MQ4','MQ4KH'],'tasman':['TK1'],'carnival':['KA4','KA4KH'],'carnival-hi-limousine':['KA4HI'],'bongo3':['PU']}
    rows=[]
    for group in lineup:
        for item in group['links']:
            slug=urlparse(item['url']).path.rsplit('/',1)[-1]
            role='exact_confirmed';reason='Official model family match. This does not certify every trim/year or approve all extracted guidance.'
            codes=mapping.get(slug)
            if slug=='granbird':role='excluded_bus';codes=[];reason='Heavy bus outside passenger/SUV/light-commercial scope.'
            elif slug=='carnival-hi-limousine':role='shared_candidate';reason='Dedicated supplement acquired; basic vehicle exact-year manual is still required.'
            elif codes is None:
                role='shared_candidate'
                if slug.startswith('pv5'):codes=['SW1K']
                elif slug.endswith('-gt'):codes=mapping.get(slug[:-3],[])
                elif slug.startswith('bongo3-ev'):codes=['PUEV']
                elif slug.startswith('bongo3'):codes=['PU']
                elif slug.startswith('tasman'):codes=['TK1']
                elif slug.startswith('k8'):codes=['GL3']
                else:codes=[];role='not_found'
                reason='Base-family manual acquired; GT/body conversion/taxi/passenger-cargo applicability or supplement must be verified before reuse.'
            rows.append({**item,'category':group['category'],'sales_catalog_url':group['source_url'],'coverage_status':role,'manifest_document_ids':[bycode[c]['id'] for c in codes if c in bycode],'reason':reason})
    write(OUT/'kia_sales_coverage.json',{'checked_at_utc':manifest['checked_at_utc'],'denominator':'42 sales product rows, including one excluded bus; HEV may be bundled under a sales family. Not 42 distinct manuals.','products':rows})
    examples=[
        {'id':'kia_sp3_tpms_low','document_id':'kia_SP3_2026','source_url':'https://ownersmanual.kia.com/full_webhelp/SP3/2026/ko_KR/topics/t00940.html','warning_type':'TPMS','condition':'Low-pressure indication and affected tire position; not merely any ON sample','action_ko':'속도를 낮추고 급격한 코너링을 피한 뒤 타이어 상태를 확인한다. 차가운 타이어 기준 권장 공기압으로 조정하고 경고가 남으면 점검받는다.','required_context':['차종/연식/타이어규격','저압 표시와 위치','타이어가 차가운 상태인지']},
        {'id':'kia_sp3_tpms_fault','document_id':'kia_SP3_2026','source_url':'https://ownersmanual.kia.com/full_webhelp/SP3/2026/ko_KR/topics/t00941.html','warning_type':'TPMS','condition':'Approximately one minute flashing followed by steady light','action_ko':'약 1분 점멸 후 계속 켜지는 패턴은 TPMS 이상 안내에 해당한다. 서비스센터 점검이 필요하며, 그 상태에서 저압 경보 기능을 신뢰하지 않는다.','required_context':['점멸 지속시간','점멸 후 점등 전환','동일 관측구간 여부']},
        {'id':'kia_sp3_esc','document_id':'kia_SP3_2026','source_url':'https://ownersmanual.kia.com/full_webhelp/SP3/2026/ko_KR/topics/t00416.html','warning_type':'ESC','condition':'Blinking during intervention versus persistent illumination after startup','action_ko':'주행 중 ESC 작동에 따른 점멸은 정상 작동 표시다. 시동 점검 이후 계속 켜지거나 주행 중 지속 점등되는 경우에는 점검 안내로 구분한다. ESC OFF 표시와도 분리한다.','required_context':['시동 후 경과시간','ESC 작동/해제 구분','지속 점등인지']},
        {'id':'kia_sp3_ebd','document_id':'kia_SP3_2026','source_url':'https://ownersmanual.kia.com/full_webhelp/SP3/2026/ko_KR/topics/t00415.html','warning_type':'BRAKE_EBD','condition':'ABS and brake warning lamps illuminated together','action_ko':'ABS와 브레이크 경고가 동시에 켜진 경우 EBD 기능 문제 가능성을 함께 안내한다. 고속주행과 급제동을 피하고 신속히 정비 점검을 받도록 구분한다. 단일 ABS 신호로 이 조합을 추정하지 않는다.','required_context':['동시 ABS/브레이크 경고','주차브레이크 상태','시동 후 경과시간']},
        {'id':'kia_ev3_powerdown','document_id':'kia_SV1_2027','source_url':'https://ownersmanual.kia.com/full_webhelp/SV1/2027/ko_KR/topics/t00163.html','warning_type':'POWER_DOWN','condition':'Power-down alone versus power-down plus service warning','action_ko':'파워다운만 켜지면 배터리 잔량·전압·온도나 구동계 보호에 따른 출력 제한일 수 있다. 서비스 경고등이 함께 켜지는 경우에는 점검 안내가 추가된다. 단독 파워다운을 곧바로 고장 확정으로 표시하지 않는다.','required_context':['서비스 경고 동시 여부','구동배터리 잔량/온도','동일 관측구간']},
        {'id':'kia_sp3_hev_ready','document_id':'kia_SP3_2026','source_url':'https://ownersmanual.kia.com/full_webhelp/SP3/2026/ko_KR/topics/t00536.html','warning_type':'HEV_SYSTEM','condition':'HEV READY off/flashing or service warning; separate normal EV mode indicator','action_ko':'HEV 주행 가능 표시의 꺼짐·점멸과 서비스 경고는 점검 대상으로 구분한다. 엔진 정지 또는 모터 단독 구동을 알리는 EV 모드 점등은 그 자체로 같은 고장 경고가 아니다.','required_context':['하이브리드 파워트레인','정확한 표시등 종류','시동 후 주행 준비 상태']},
    ]
    for row in examples:
        row['review_status']='source_text_reviewed_not_production_approved'
        row['review_method']='Relevant complete HTML topic read; display icons/layout not visually certified.'
        row['production_mapping_status']='blocked_until_required_context_supported'
    write(OUT/'kia_reviewed_examples.json',examples)
    summary={'checked_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'documents':len(documents),'assets_verified':len(audits),'hash_failures':0,'signature_failures':0,'html_topic_files':sum(d.get('html_topic_count',0) for d in documents),'pdf_files':sum(a.get('format')=='pdf' for d in documents for a in d['assets']),'pdf_pages':sum(d.get('pdf_pages',0) for d in documents),'bytes':sum(a['bytes'] for d in documents for a in d['assets']),'unresolved_acquisition_errors':sum(len(d.get('acquisition_errors',[])) for d in documents),'reviewed_examples':len(examples),'sales_rows':len(rows),'sales_status_counts':{s:sum(r['coverage_status']==s for r in rows) for s in sorted({r['coverage_status'] for r in rows})},'assets':audits}
    write(OUT/'kia_validation.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='assets'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
