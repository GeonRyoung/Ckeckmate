"""Persist explicitly completed reading units; never infer reading from matches."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'.local/manual-review/2026-10-28/hyundai'
INV=json.loads((ROOT/'data/manual-review/2026-10-28/hyundai-inventory.json').read_text(encoding='utf-8'))
DIFFS=[('DN8HEV-2026','MX5HEV-2026'),('CE1-2025','CE1N-2025'),('US4-2026','US4HEV-2026'),('DN8-2026','SX2-2027'),('SX2-2027','SX2HEV-2027'),('NE1-2025','NE1N-2026'),('NE1N-2026','SX2EV-2025')]
DIFFNOTES={
'MX5HEV-2026':'유압 회복 뒤 재시동 요구 보존. 소나타 HEV의 자동 해제 설명과 다름.',
'CE1N-2025':'N 전용 정상 상태 표시, POWER ON/DRIVE READY 전원 상태 및 시동 메시지 차이를 직접 대조.',
'US4HEV-2026':'서비스/EV/회생제동/HEV 시스템 메시지 추가. 비플러그인 HEV 문서의 즉시 충전·30~40km 표현은 적용 불명확.',
'SX2-2027':'차로 표시 초록색 점멸 설명, ISG, 키·변속 메시지와 오일 회복 후 재시동 조건을 대조. 그룹24–25를 별도로 다시 읽어 출력 잘림 해소.',
'SX2HEV-2027':'HEV 주행가능·서비스·EV·회생제동 추가. 클러스터에는 재시동 문장이 생략됐으나 정비 절 PDF651/646에서 유압 회복 후 재시동 요구를 확인함(HY-PROCEDURE-SX2HEV-2027-OIL). P 시동/ACC10초, 정차 후 끄기 및 시동 금지 메시지 분리.',
'NE1N-2026':'차이가 큰 하나의 묶음으로 실제 클러스터 전체를 다시 읽음. N/드리프트/AWD/ESC SPORT/런치 표시 포함. EV 문서의 엔진·벨트 충전 설명은 적용 불명확.',
'SX2EV-2025':'구동벨트 충전 설명은 EV 적용 불명확. N 전용 모드 표시 제거, 운전자주의 및 키·메시지 변화 모두 대조.'}
FULL=['A01-2026','DN8-2026','DN8HEV-2026','DN8c-2025','QX-2027','HR-2026','HREV-2026','CN7N-2026','NE1-2025','US4-2026','US4EV-2027','CE1-2025']
rows=[]
for key in FULL:
 s=next(s for s in INV['sections'] if s['documentId']=='HYUNDAI-'+key and s['title']=='cluster_warning_indicator_and_messages')
 rows.append({'documentId':s['documentId'],'sectionId':s['id'],'sourceURL':s['sourceURL'],'sourceSha256':s['sourceSha256'],'passageSha256':s['passageSha256'],'locator':s['locator'],'reviewStatus':'SOURCE_REVIEWED','reviewMethod':'AI direct complete section reading','runtimeApproved':False,'linkedProceduresClosed':False})
for base,var in DIFFS:
 p=RAW/f'HYUNDAI-{base}--HYUNDAI-{var}-diff.json';d=json.loads(p.read_text(encoding='utf-8'))
 rows.append({'documentId':d['variantDocumentId'],'canonicalDocumentId':d['baseDocumentId'],'sectionId':d['variantSectionId'],'passageSha256':d['variantPassageSha256'],'diffArtifactSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'differenceGroupsRead':len(d['differences']),'reviewStatus':'SOURCE_REVIEWED','reviewMethod':'Complete canonical reading plus every formatting-normalized source difference read with context; no semantic auto-approval','notes':DIFFNOTES[var],'runtimeApproved':False,'linkedProceduresClosed':False})
# The earlier MX5 comparison was prepared with a separate formatting-normalized diff.
s=next(s for s in INV['sections'] if s['documentId']=='HYUNDAI-MX5-2026' and s['title']=='cluster_warning_indicator_and_messages')
rows.append({'documentId':s['documentId'],'sectionId':s['id'],'passageSha256':s['passageSha256'],'locator':s['locator'],'canonicalDocumentId':'HYUNDAI-DN8-2026','differenceGroupsRead':144,'reviewStatus':'SOURCE_REVIEWED','reviewMethod':'Canonical complete reading plus all 144 groups directly read; groups20–119 separately printed to avoid truncation','notes':'유압 회복 후 재시동, SUV 테일게이트·AWD·차로 유지 및 메시지 차이 보존.','runtimeApproved':False,'linkedProceduresClosed':False})
out={'schemaVersion':1,'reviewer':'AI','runtimeApproved':False,'allCountermeasuresReviewed':False,'readingUnits':rows,'note':'Table/numbered row evidence remains in separate review files. This ledger records reading, not execution-ready action encoding or expert approval.'}
(ROOT/'data/manual-review/2026-10-28/hyundai-pdf-reading-ledger.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('Explicit full/difference reading units',len(rows))
