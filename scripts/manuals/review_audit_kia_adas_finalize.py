"""Persist completed additional direct source readings and validate scope counts."""
import json,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'.local/manual-review/2026-10-28/audit/kia-adas';OUT=ROOT/'data/manual-review/2026-10-28'
def read(p):return json.loads(p.read_text(encoding='utf8'))
base=read(OUT/'audit-kia-adas-review.json');es=read(RAW/'extra-review-inventory.json');us=read(RAW/'extra-review-units.json');assert len(us)==1037
rows=[]
for i,e in enumerate(es):
 ids=[u['id'] for u in us if i in u['entries']]
 if e['reason']=='PU legacy hidden faults':note='봉고 PU의 제목 밖 FCA 고장·LDW 고장·PDW 문맥을 추가 확인했다. ESC 완전 해제에 따른 FCA 꺼짐은 고장과 다르다. FCA 제동 유지 약 2초 후 운전자 제동이 필요하며 견인 시 해제한다. LDW는 약 60km/h 이상에서 경고하며 자동 조향 기능이 아니다. 영구 경고는 지정 정비망 점검이다.'
 elif e['reason']=='legacy lighting fault and fallback':note='조명 장에 포함된 HBA/IFS 고장과 수동 전환 조건을 직접 확인했다. 비정상 보조는 수동 하향 전환 또는 기능 해제로 대응하고 경고 지속은 점검한다. RJ의 40/25km/h 전환과 다른 차종의 30/20km/h를 공통값으로 합치지 않는다. 센서 가림은 제거하며 남은 가림을 재시동으로 해결했다고 간주하지 않는다.'
 else:note='고장 대처 뒤 제한 절의 필수 금지 조건까지 확인했다. 광각 렌즈는 원문 허용 순한 비누/중성 세제와 물로 세척하고 산성·알칼리성·휘발성 용제를 피한다. 센서 고압 분사·충격·탈착·도장·가림을 금지한다. 주차 보조의 제동 불가, 연속 접근 경고, 위험 시 버튼에서 손을 떼어 중지, 트렁크/테일게이트 열림 조건과 운전자 직접 제어를 보존한다. 하이빔·IFS 비정상은 수동 전환한다. 각 조건의 적용 기능은 해당 원문으로 한정한다.'
 rows.append({k:e[k] for k in ['documentId','sourceURL','sourceSha256','title','rootScope','reason']}|dict(reviewId=f'AUDIT-KIA-ADAS-EXTRA-{i:04}',locator='해당 본문 전체와 이미 검토한 동일 문장, 일반 재귀 참조는 제외',newReadUnitHashes=[us[j]['hash'] for j in ids],reviewStatus='SOURCE_TEXT_REVIEWED',reviewNote=note,reviewMethod='기존 1421개 정확 동일 문장 제외 후 신규 1037개 문장 직접 읽음',reviewer='AI',runtimeApproved=False))
base['additionalRows']=rows;base['additionalUniqueUnits']=len(us);base['totalUniqueReadUnits']=1421+len(us);base['distinctSourceURLs']=len({r['sourceURL'] for r in base['rows']+rows});base['remainingRequiredClosure']=[];base['sourceReadingComplete']=True
base['sourceReadingScope']='28개 기본 웹 설명서의 ADAS 고장·가림·복구, 센서 취급·세척 금지, HBA/IFS 수동 전환, PU 제목 밖 고장 설명. 같은 문장의 정확 일치만 공유하여 읽음. 모든 기능의 모든 일반 성능 도해나 앱 실행 승인까지 완료했다는 뜻은 아님.'
base['scopeExclusions']=['일반 ADAS 성능 제한 도해 전체의 시각 검증과 모든 재귀 참조','실제 판매 사양/VIN의 센서 탑재 여부 및 SDK 매핑 승인','인포테인먼트 별도 매뉴얼 전체 업데이트 조작 절차','소스의 LiDAR/AFS/IFS 표기를 실제 장비 동일성으로 확정']
base['sourceHolds']=[]
for uid,reason in [(570,'EV6 CV1 주차 충돌방지 제한 문장에 LiDAR가 등장한다. 실제 해당 사양의 센서 탑재를 이 문구만으로 확정하지 않는다.'),(943,'NQ5KH HBA 상향 작동 중 레버를 당길 때 원문이 하향을 명시하지 않고 전조등으로만 적는다. 수동 전환 버튼별 실행 규칙으로 자동 정규화하지 않는다.')]:
 u=us[uid];sources=[{k:es[j][k] for k in ['documentId','sourceURL','sourceSha256']} for j in u['entries']]
 base['sourceHolds'].append(dict(unitHash=u['hash'],reason=reason,sources=sources,runtimeApproved=False))
(OUT/'audit-kia-adas-review.json').write_text(json.dumps(base,ensure_ascii=False,indent=2),encoding='utf8')
checks=[]
for inv in ['review-inventory.json','extra-review-inventory.json']:
 for e in read(RAW/inv):assert hashlib.sha256((ROOT/e['localPath']).read_bytes()).hexdigest()==e['sourceSha256'],e['sourceURL']
checks.append(dict(check='all_kia_adas_source_hashes_match_local_originals',passed=True,baseSections=1495,additionalSections=431,distinctURLs=base['distinctSourceURLs'],uniqueReadUnits=2458))
for e in base['rows']+rows:assert e['runtimeApproved'] is False and e['reviewer']=='AI'
checks.append(dict(check='runtime_and_expert_approval_not_claimed',passed=True))
paths=list(OUT.glob('audit-*.json'))+[OUT/'hyundai-web-rules-audit.json',OUT/'hyundai-web-coverage.json']
bad=[]
for p in paths:
 t=p.read_text(encoding='utf8');json.loads(t)
 if '\ufffd' in t:bad.append(p.name)
checks.append(dict(check='utf8_json_and_no_replacement_codepoint',passed=not bad,files=len(paths),failed=bad))
(OUT/'audit-adas-validation.json').write_text(json.dumps(dict(checks=checks,sourceReadingComplete=True,scope=base['sourceReadingScope'],runtimeApproved=False),ensure_ascii=False,indent=2),encoding='utf8')
print(base['distinctSourceURLs'],2458,checks)
