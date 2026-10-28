"""Record completed direct reading, never infer review from extraction."""
import json,hashlib
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'.local/manual-review/2026-10-28/audit/hyundai-web-closure'
OUT=ROOT/'data/manual-review/2026-10-28'
def read(name):return json.loads((RAW/name).read_text(encoding='utf8'))
entries=[e for e in read('inventory.json') if e['scope']=='adas-fault-and-sensor-reference']
entries+=read('sensor-backstop-inventory.json')+read('gap-inventory.json')
notes={
'sensor':'센서별 청소 방법을 구분한다. 레이더/초음파 고압 분사 금지, 광각 카메라는 순한 비누/중성 세제와 물, 실내 카메라는 부드러운 마른 천 및 화학 약품 금지. 충격·분해 후 점검 조건을 보존한다.',
'restart':'가림 제거 후 정상 복귀와 지속 시 점검을 구분한다. 재시동만으로 고장·가림이 해소된다고 안내하지 않는다. 후측방/교차 안전의 명시적 재시동 조건은 해당 절에서만 적용한다.',
'fallback':'운전자가 직접 조향·제동하고 주변을 확인한다. HBA 수동 상향/하향 조작과 IFS 상향에서 하향 또는 기능 끄기를 구분한다.',
'state':'꺼짐/일시 제한/고장을 구분한다. ESC 완전 해제로 FCA가 함께 꺼지는 상태는 고장이 아니다. 기능이 켜져 있는데 경고가 지속되면 점검한다.',
'modelDifferences':'NH2 DMS와 GN7/GN7HEV FAW 속도/눈감음 조건을 혼합하지 않는다. PMSA 재작동의 5분 경과는 CN8KH/NX5KP 본문에는 없으므로 추가하지 않는다. 스마트 회생 복구 오른쪽 패들 1초는 명시 차량만 적용한다.'}
rows=[]
for e in entries:
 rows.append({k:v for k,v in e.items() if k not in ['lines','reviewStatus']}|{'reviewStatus':'SOURCE_REVIEWED','reviewMethod':'AI_DIRECT_SOURCE_READING_WITH_EXACT_WHITESPACE_DEDUP','runtimeApproved':False,'sourcePassageSha256':hashlib.sha256('\n'.join(e['lines']).encode()).hexdigest(),'reviewNote':'경고/고장·센서 가림·복구와 연결 청소 금지/수동 대체 조치 직접 독해. 일반 성능 한계 전체 실행 규칙 승인 아님.'})
holds=[]
for e in entries:
 s='\n'.join(e['lines'])
 if e['documentId']=='HYUNDAI-NH2-2027' and e['title'].startswith('운전자 주의 경고 제한'):
  holds.append({'documentId':e['documentId'],'sourceURL':e['sourceURL'],'sourceSha256':e['sourceSha256'],'locator':e['topicId'],'issue':'DAW 고장/가림 절에서 복귀 기능을 지능형 속도 제한 보조로 기재. 기능명 교차 복사 의심; 자동 교정/전이 보류.','runtimeApproved':False})
data={'reviewerType':'AI_REVIEW_NOT_EXPERT_APPROVAL','runtimeApproved':False,'scope':'Hyundai web 7 warning fault/obstruction, sensor care prohibitions, required restart and manual fallback; general performance diagrams not globally validated','sourceReadingCompleteWithinStatedScope':True,'sectionsRead':len(rows),'uniqueNewUnitsRead':893+139+647,'readingBatches':{'adas-read-00..11':893,'sensor-read-00..01':139,'gap-read-00..06':647},'documentCounts':dict(Counter(r['documentId'] for r in rows)),'rows':rows,'reviewNotes':notes,'sourceHolds':holds,'requiredRemainingWithinThisScope':[],'separatePendingScope':{'owner':'hyundai_response_review','sections':200,'scope':'emergency, EPB/brakes, key/start','readingStatus':'PENDING_OWNER_ARTIFACT'}}
(OUT/'audit-hyundai-web-adas-closure.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
print('Saved',len(rows),'sections;',data['uniqueNewUnitsRead'],'unique units')
