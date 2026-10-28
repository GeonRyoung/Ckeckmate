"""Correct functional associations after actual PV5 page-body review."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'data/manual-review/2026-10-28';RAW=ROOT/'.local/manual-review/2026-10-28/audit/kia-adas/pv5-backstop';p=OUT/'audit-kia-adas-review.json';d=json.loads(p.read_text(encoding='utf8'));allrows=json.loads((RAW/'all.json').read_text(encoding='utf8'));byname={Path(e['sourceURL']).name:e for e in allrows}
mapping={'t00525.html':('FCA','전방 충돌방지 보조','t00535.html'),'t00596.html':('ISLA','지능형 속도 제한 보조','t00606.html'),'t00536.html':('LKA','차로 이탈방지 보조','t00543.html'),'t00565.html':('SEW','안전 하차 경고','t00574.html'),'t00575.html':('SEA','안전 하차 보조','t00582.html'),'t00607.html':('DAW','운전자 주의 경고','t00630.html'),'t00652.html':('HDA','고속도로 주행 보조','t00665.html'),'t00665.html':('RVM','후방 모니터','t00682.html'),'t00682.html':('SVM','서라운드 뷰 모니터','t00693.html'),'t00213.html':('NON_ADAS','와이퍼/워셔','t00212.html')}
corrections=[]
for r in d['rows']+d['additionalRows']:
 if r['documentId']!='kia_SW1K_2027':continue
 name=Path(r['sourceURL']).name
 if name not in mapping:continue
 system,actual,target=mapping[name];r['originalRootScope']=r.get('originalRootScope',r.get('rootScope'));r['originalSystem']=r.get('originalSystem',r.get('system'));r['rootScope']=actual;r['system']=system;r['reviewNote']='공식 목차 기능명과 실제 본문 기능이 다름. 본문에 명시된 '+actual+'에만 연결; 원래 목차의 기능으로 전이 금지.';r['functionalAssociationCorrected']=True
 if system=='NON_ADAS':r['reviewStatus']='SOURCE_READ_OUTSIDE_ADAS_SCOPE'
 corrections.append({'originalURL':r['sourceURL'],'originalLabel':r['originalRootScope'],'actualBodyTitle':byname[name]['title'],'actualBodySystem':actual,'sourceSha256':r['sourceSha256'],'correctedURLForOriginalLabel':r['sourceURL'].rsplit('/',1)[0]+'/'+target,'correctionKind':'BODY_FUNCTION_VERIFIED; target may be title-only hold','runtimeApproved':False})
added=json.loads((RAW/'inventory.json').read_text(encoding='utf8'))+[byname['t00212.html']]
new=[]
for i,e in enumerate(added):
 new.append({k:v for k,v in e.items() if k not in ['text','alreadyRead']}|{'documentId':'kia_SW1K_2027','reviewId':f'AUDIT-PV5-BACKSTOP-{i:02}','reviewStatus':'SOURCE_REVIEWED' if len(e['text'].splitlines())>1 else 'SOURCE_READ_TITLE_ONLY_NO_PROCEDURE','reviewMethod':'AI direct full body reading and exact sentence duplicate comparison','runtimeApproved':False,'locator':'main article','reviewNote':'실제 본문 기능에만 연결. 제목만 있는 절은 대처법 확보로 계산하지 않음.'})
holds=[{'documentId':'kia_SW1K_2027','sourceURL':byname[n]['sourceURL'],'sourceSha256':byname[n]['sourceSha256'],'issue':issue,'resolution':'SOURCE_CONTENT_UNAVAILABLE_IN_RETRIEVED_OFFICIAL_TOPIC; no other-function substitution','runtimeApproved':False} for n,issue in [('t00210.html','HBA 고장 절은 제목만 있음; t00212의 수동 전환 제한은 읽었으나 고장 문구를 추정하지 않음.'),('t00543.html','LFA 이상 절은 제목만 있으며 다음 실제 페이지는 BCA. 독립 고장 상세 보류.')]]
result={'runtimeApproved':False,'reviewerType':'AI_NOT_EXPERT','consecutivePagesAudited':220,'additionalSections':new,'sourceHolds':holds,'corrections':corrections,'originalCorpusUntouched':True,'additionalSourceReadingComplete':True}
(OUT/'audit-kia-link-errata.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');d['pv5LinkErrataArtifact']='audit-kia-link-errata.json';d['sourceHolds'].extend(holds);d['sourceReadingScope']+='; PV5 actual-body linkage corrected in audit-kia-link-errata.json; title-only unavailable procedures held';p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print(len(corrections),'corrections',len(new),'additional pages')
