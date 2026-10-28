"""Explicit completed EPB/Auto Hold/ABS/ESC source review ledger and summaries."""
import json,hashlib
from pathlib import Path
from hyundai_review_tpms_legacy_adas import rule,ROOT,OUT,RAW
def main():
 units=json.loads((RAW/'brake-units.json').read_text(encoding='utf-8'))
 esc=[x for x in json.loads((RAW/'units.json').read_text(encoding='utf-8')) if x['topic']=='ESC']
 rules=[]
 for u in units+[{'id':'HREV-2026-BRAKE','pages':list(range(180,190))}]:
  code,year=u['id'].split('-')[:2];pages=u['pages']
  r=rule(code,year,'EPB_AUTOHOLD_ABS',pages,['EPB 고장·체결 실패·자동 해제 조건 불충족·AUTO HOLD 전환 실패·ABS 경고를 분리한다.'],['과도한 EPB 조작 뒤 경고이면 안전 정차 상태에서 시동 OFF 후 잠시 기다리고 다시 시동하여 소등·정상 작동을 확인한다. 지속 경고는 정비한다.','EPB 경고와 브레이크 점멸이 함께 있으면 브레이크로 정차를 유지하고 EPB 스위치를 눌렀다 당긴 뒤 원위치에서 다시 당겨 체결을 확인한다. 정상 절차로 해제되지 않으면 견인 점검한다.','자동 해제 조건 불충족 경고이면 브레이크를 밟고 EPB를 수동 해제하며 소등 확인 후 출발한다.','AUTO HOLD 해제/EPB 전환 불가 경고는 브레이크 페달로 직접 정차 상태를 유지한다. AUTO HOLD 고장색 표시는 정비한다.','빙판 등에서 ABS 연속 작동 뒤 경고는 안전 정차 후 재시동하여 소등을 확인한다. 지속 경고는 신속히 정비한다. 점프 시동 후에는 배터리 전압 회복 후 주행한다.','브레이크 페달 고장이라는 비상시에만 EPB 스위치를 당겨 유지한다. 놓으면 비상제동이 중단된다. 정차 시 체결되고 정상보다 정지거리가 길 수 있다. 소음/탄 냄새가 계속되면 정비한다.'],['EPB 체결 상태 주행 금지. 비상상황이 아닌 주행 중 EPB 조작 금지.','ABS 급제동 중 페달에서 발을 떼거나 펌프질하지 않는다.','동시 ABS+브레이크 경고 시 고속·급제동을 피한다.'],['EPB/ABS 재시동 확인은 해당 조건의 절차이며 모든 제동 고장·유압 부족·경고 조합에 적용하지 않는다.','부족한 12V 전원으로 EPB가 동작하지 않을 때 보조 배터리 연결은 해당 점프 절차/금지조건을 따르며 임의 전압·단자를 안내하지 않는다.','고장 색·도어/후드/트렁크/테일게이트·변속기 사양별 자동해제 조건은 개별 원문과 함께 제공해야 한다.'])
  r['reviewMethod']='DN8 full paragraph reading, all 859 unique source sentence/context units read, then source-specific conditions reconciled; source section order retained in local ledger'
  if code in ['US4EV','US4','US4HEV','CE1','ME','AXEV','AX','CE1N']:r['modelSpecificConditions']=['해당 본문은 AUTO HOLD 고장색 주황색 표기를 사용한다. 원문 클러스터 표와 색 차이가 있으면 통합하지 않는다.']
  else:r['modelSpecificConditions']=['AUTO HOLD 고장색 노란색/황색 원문 표기. 흰색 대기·녹색 작동과 구분.']
  if code in ['A01','HREV']:r['modelSpecificConditions']+=['EPB 수동 해제 시 ON 상태 명시; 일반 차량의 시동을 거십시오와 구별.']
  if code=='HREV':r['modelSpecificConditions']+=['AUTO HOLD는 R에서 비작동. 자동 해제 조건은 운전석 도어·안전벨트·시동·R/D이며 후드/테일게이트 조건을 추가 추정하지 않는다.']
  if code=='CN7N':r['modelSpecificConditions']+=['AUTO HOLD 30분 이상 정차 비작동 및 10분 이상 정차 시 EPB 전환이라는 각 문맥을 보존. R 비작동. 수동/전자식 주차 브레이크 사양 구분.']
  if code=='DN8':r['modelSpecificConditions']+=['변속 레버형 R 비작동과 변속 다이얼형 트렁크 열림 조건을 구분.']
  if code=='AX':r['modelSpecificConditions']+=['풋 주차 브레이크 사양: 완전히 해제했는데 경고가 남으면 정비. EPB 스위치 절차를 풋 브레이크 사양에 적용하지 않는다.']
  if code=='A01':r['applicationConstraints']+=['일부 과도조작 단락은 EPB 대신 브레이크 경고 기호를 반복하고 이후 이상 절은 EPB 기호를 명시한다. 경고 아이콘 조합은 원본 이미지와 대조 전 자동 분기 보류.']
  rules.append(r)
 for code,year,pages in [('QX',2027,[217,218,219]),('HR',2026,[224,225,226,227,228])]:
  r=rule(code,year,'MANUAL_PARKING_ABS',pages,['수동 주차브레이크 해제 후 경고 지속 또는 ABS 이상.'],['주차브레이크를 완전히 해제하고 소등을 확인한다. 지속 경고는 정비한다.','ABS 경고 시 해당 절의 안전 정차·재시동 확인을 하고 지속/재발하면 정비한다.'],['비상 외 주행 중 주차브레이크 작동 금지.','ABS 급제동 중 반복 펌프질 금지.'],['EPB 스위치 조작을 이 수동 브레이크 사양에 전이하지 않는다.'])
  if code=='HR':r['modelSpecificConditions']=['주행 중 ABS 점등이면 안전 정차·엔진 OFF·재시동 후 약3초 소등 확인. 시작 시 아예 안 켜짐/3초 뒤 미소등/주행 후 재점등이면 정비. 점프 후 저전압이면 공회전 충전 뒤 주행.']
  rules.append(r)
 for u in esc+[{'id':'QX-2027-ESC','locator':{'pdfPages1Based':[220,221,222]}},{'id':'HR-2026-ESC','locator':{'pdfPages1Based':[229,230,231]}},{'id':'HREV-2026-ESC','locator':{'pdfPages1Based':[189,190,191]}}]:
  code,year=u['id'].split('-')[:2]
  r=rule(code,year,'ESC_VSM',u['locator']['pdfPages1Based'],['시동 자가 점검, 작동 점멸, 고장 지속 점등, 운전자 선택 OFF를 구분한다.'],['ESC 작동 중 점멸이면 가속하지 말고 서행한다. 작동 표시등이 지속 점등/주행 중 점등이면 정비한다.','운전자가 끈 OFF 모드는 해당 버튼 또는 재시동으로 작동 가능 상태로 복귀한다.'],['ESC 작동 점멸 중 기능 해제 금지.'],['OFF 표시 자체를 고장으로 단정하지 않는다. VSM 절에 OFF 표시 지속 시 정비 문구가 있지만 운전자 OFF 선택 여부를 구별하는 조건이 생략되어 자동 진단 보류.','재시동으로 OFF 선택이 초기화된다는 설명은 고장 복구를 보장하지 않는다.'])
  r['reviewMethod']='All 434 distinct exact-normalized ESC source sentences read with canonical full paragraph and document associations; legacy QX/HR/HREV full source pages read separately'
  if code=='HR':r['modelSpecificConditions']=['장치 보호를 위한 일시 정지에도 점등. OFF 버튼0.5초 이상 사용 문맥. 2단계/3초 규칙을 추정 적용하지 않는다.']
  if code=='CN7N':r['driverProhibitions']+=['미니 예비타이어 또는 TMK 사용 중 ESC SPORT/OFF 금지. ESC·ABS·주차브레이크 경고 동안 한 축 바퀴를 과도하게 회전시키지 않는다.'];r['modelSpecificConditions']=['NORMAL/SPORT/OFF를 구분하며 시동을 다시 걸면 NORMAL 작동 가능 상태.']
  if code in ['NE1N','CE1N']:r['modelSpecificConditions']=['SPORT와 OFF 분리. 스포츠모드 동작/길게 누름 설명을 일반 1단계 구동력 해제와 동일시하지 않는다.']
  rules.append(r)
 led=[]
 for name,count in [('brake-sentence-units.json',859),('esc-sentence-units.json',434)]:
  b=(RAW/name).read_bytes();led.append({'localPath':str((RAW/name).relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest(),'uniqueUnitsRead':count,'allUnitIndicesRead':list(range(count)),'normalization':'Whitespace and layout image IDs only; conditions, numbers and negations retained. Source association and original order preserved in units files.'})
 (OUT/'hyundai-pdf-brake-review.json').write_text(json.dumps({'schemaVersion':1,'rules':rules,'readingLedger':led,'runtimeApproved':False},ensure_ascii=False,indent=2),encoding='utf-8');print(len(rules))
if __name__=='__main__':main()
