"""Record the completed direct reading of 1,421 exact-text units."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'.local/manual-review/2026-10-28/audit/kia-adas';OUT=ROOT/'data/manual-review/2026-10-28'
notes={
'FCA':'기능 고장은 지정 정비망 점검, 가림은 해당 카메라·레이더의 오염 제거 및 지속 시 점검으로 구분한다. 재시동만으로 남아 있는 가림이 해소되지 않는다. 센서 충격 후 경고가 없어도 점검하며 임의 탈착·도장·장식물·고압 세척을 피한다.',
'LKA':'고장 경고와 카메라 가림을 구분한다. 가림 제거 후에도 지속하면 점검한다. 다시 시동을 걸어도 남아 있는 가림은 해결되지 않으며 직접 조향 책임을 보존한다.',
'LDW':'차로 이탈 경고는 자동 조향 기능이 아니다. 앞유리/카메라 교체·탈착 후 보정 점검이 필요할 수 있다. PU의 추가 작동 본문 고장 조건은 별도 보충 검토한다.',
'BCA':'센서 이상과 미러 경고등 이상을 구분해 점검한다. 후측방 장비·오염 제거 후 재시동 조건을 보존하고 짐칸·캐리어 사용 중 끈다. 타스만은 코너 스텝 주변 진흙도 포함한다.',
'SEA':'후측방 센서 가림·장착 장비를 제거한 후 원문 재시동 조건을 따른다. 지속하면 점검한다. 도어 차단 방식은 파워 슬라이딩 도어와 전자식 차일드 락 차종을 구분하며 차일드 락 대체로 해석하지 않는다.',
'SEW':'안전 하차 경고 및 미러 표시 장치 고장을 점검한다. 장착 장비·오염 제거 후 재시동과 지속 시 점검을 보존한다. 경고가 없어도 직접 후방을 확인한다.',
'ISLA':'카메라 오염을 제거하며 원문에 따라 주행 후 경고 해제되는 경우를 보존한다. 정상 복구하지 않으면 점검한다. 지도 갱신 및 실제 도로 제한속도 확인 필요성을 유지한다.',
'DAW':'기능 고장은 점검한다. 카메라 오염 제거 후 주행 복구 조건과 단순 제거 조건을 원문별로 구분한다. 피로·휴식 권고를 센서 고장으로 합치지 않는다.',
'FAW':'카메라 앞과 얼굴 사이 가림을 제거하고 얼굴 인식이 회복되는지 확인한다. 지속 시 점검한다. 부드러운 천을 사용하고 화학약품·날카로운 도구·충격을 피하며 건조하게 유지한다.',
'SCC':'기능 고장과 전방 레이더 가림은 다른 원인이다. 오염을 제거하고 지속 시 점검하며 경고 부재·재시동 직후가 정상 인식을 보증하지 않는다.',
'LFA':'기능 이상은 지정 정비망 점검이다. 전방 카메라 및 차로 인식 조건과 운전자의 직접 조향을 보존한다.',
'HDA':'기능 고장과 IC/JC 이탈·내비게이션 부팅·핸즈오프에 의한 정상 해제를 구분한다. 견인 중 사용 금지 및 운전자의 직접 제어 조건을 보존한다.',
'HBA':'하이빔 보조 고장 경고는 지정 정비망 점검이다. 전방 카메라 관리가 연결된다. 제한 절의 수동 전환 안내는 보충 검토와 함께 연결한다.',
'IFS':'지능형 헤드램프 경고 지속 시 지정 정비망에서 점검한다. AFS/IFS 원문 표기 차이를 임의로 동일 표시등으로 확정하지 않는다.',
'PDW':'고장·센서 가림과 정상 접근 경고음을 구분한다. 차종별 R단 확인음 누락 또는 반복, 대상 방향 경고를 확인한다. 오염 제거 후 지속 시 점검하며 자사 인식형 트레일러 키트의 정상 기능 중단을 고장과 구분한다.',
'PCA':'고장 시 자동 해제 또는 대상 방향 제한을 구분한다. 광각 카메라·초음파 센서 오염 제거 후 지속 시 점검한다. 실제 주변 확인과 운전자의 제동 책임을 보존한다.',
'RCCA':'후측방 센서 및 미러 경고등 고장은 점검한다. 오염·캐리어·트레일러 제거 후 재시동 조건과 장비 장착 중 끄기 조건을 보존한다.',
'RSPA':'고장이면 사용을 멈추고 점검한다. 준비 중 대기, 스마트키 배터리 부족, EV 유틸리티 모드는 다른 미작동 조건이다. 센서 표면을 부드러운 천으로 닦고 누르기·긁기·고압 세척을 피한다.',
'BVM':'영상 이상·깜빡임은 점검한다. 렌즈를 깨끗이 하고 강알칼리·휘발유·아세톤을 피한다. 화면 거리와 실제 거리가 다를 수 있어 직접 확인한다.',
'RVM':'영상 색 이상·깜빡임 등은 점검한다. 열린 테일게이트의 정상 영상 변화와 고장을 구분하며 실제 주변을 확인한다.',
'SVM':'비정상 색·영상 깜빡임은 점검한다. 카메라로 보이지 않는 범위까지 안전하다고 해석하지 않는다.'}
es=json.loads((RAW/'review-inventory.json').read_text(encoding='utf8'));us=json.loads((RAW/'review-units.json').read_text(encoding='utf8'));assert len(us)==1421
rows=[]
for i,e in enumerate(es):
 ids=[u['id'] for u in us if i in u['entries']];m=re.search(r'\b('+ '|'.join(notes)+r')\b',e['rootScope']);system=m.group() if m else 'SENSOR'
 rows.append({k:e[k] for k in ['documentId','sourceURL','sourceSha256','title','rootScope','scope']}|dict(reviewId=f'AUDIT-KIA-ADAS-{i:04}',system=system,locator='본문 도입·고장·가림과 연결 센서 관리 문맥, 일반 성능 제한 절 전까지',reviewedUnitHashes=[us[j]['hash'] for j in ids],reviewStatus='SOURCE_TEXT_REVIEWED',reviewMethod='원문 문장 직접 읽음; 공백만 정규화한 정확 동일 문장 공유, 유사 의미 자동 승격 없음',reviewNote=notes.get(system,'센서 종류와 연결 기능을 확인했다. 도해 위치 자체의 시각 검증 및 실제 차량 사양 승인은 별도이며 경고가 없어도 정상 인식을 보증하지 않는다.'),reviewer='AI',runtimeApproved=False))
out=dict(documentCount=len({e['documentId'] for e in es}),sourceSections=len(rows),readUniqueUnits=len(us),rows=rows,remainingRequiredClosure=['구형 PU FCA/LDW/PDW 제목 밖 고장 문맥','구형 조명 장 HBA/IFS 루트 및 고장·수동 전환','PDW/PCA/모니터/RSPA 제한 절의 필수 세척 금지·센서 취급 주의'],scope='경고 대처의 고장·가림·센서관리 문맥. 일반 기능 작동 전체의 전수 승인 아님.',runtimeApproved=False,allCountermeasuresReviewed=False)
(OUT/'audit-kia-adas-review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(len(rows),len(us))
