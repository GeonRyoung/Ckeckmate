"""Persist supplementary warning panels and low-voltage emergency references read by AI."""
import json,hashlib
from hyundai_review_tpms_legacy_adas import ROOT, OUT, RAW, rule

def main():
 rules=[]
 units=json.loads((RAW/'jump-units.json').read_text(encoding='utf-8'))
 sentences=json.loads((RAW/'jump-sentences.json').read_text(encoding='utf-8'))
 for u in units:
  c,y=u['id'].split('-')[:2]
  r=rule(c,y,'LOW_VOLTAGE_JUMP',u['pages'],['12V 전원 부족 또는 EPB 해제 불능의 원인이 저전압일 때 해당 차량의 비상 시동 절을 적용한다.'],['전문가의 도움을 받아 전기장치를 끄고 지정된 + 충전단자→보조 배터리 +, 보조 −→차량의 지정 −충전단자/차체 접지 순서로 연결한다.','다른 차량 전원을 이용하면 그 차량 시동 후 기다렸다가 대상 차량을 시동한다. 분리는 −측부터 하고 +측을 분리한다.','시동 성공 후에도 방전 원인이 불명확하면 정비한다. EPB 정상 해제·경고 소등을 별도로 확인한다.'],['12V가 아닌 보조 전원, 극성 뒤바뀜·집게 접촉·불꽃·잘못된 차체 접촉을 피한다.','얼거나 전해액이 부족한 배터리는 파열/폭발 위험이 있어 무리하게 점프하지 않는다.','충전단자 점프 실패 후 배터리 직접 연결에서 방전 배터리 −단자에 직접 연결하지 않는다.'],['지정 −충전단자와 실제 배터리 −극을 동일시하지 않는다. 차량별 단자 그림을 함께 제공해야 하며 이 요약으로 위치를 추측하지 않는다.','점프 시동은 모든 충전 경고의 해결책이 아니다. 구동 중 발전/전원계 고장 경고와 방전은 구분한다.'])
  r['reviewMethod']='All 603 exact-normalized unique sentence/context units directly read with all 26 source associations; model reset and cable conditions retained.'
  if c in ['DN8HEV','US4HEV','SX2HEV']:
   r['orderedActions'].insert(0,'해당 내장 리튬 12V 사양은 우선 12V BATT RESET 또는 문서에 지정된 트렁크/테일게이트 버튼으로 보호 차단을 해제하고 30초 이내 시동한다. READY 상태로 외부에서 약 30분 충전한다. 실패·과방전 시 점프 절차로 간다.')
   r['driverProhibitions']+=['충전 전 리셋 버튼을 반복해 과방전시키지 않는다. 이 하이브리드 차량을 다른 차량 점프 전원으로 사용하지 않는다.']
   r['modelSpecificConditions']=['충전기 13.3–14V, 권장 13.8V, 60A 이하. 전원 차단 후 부적합 충전기를 계속 사용하지 않는다.']
  if c=='HREV':r['modelSpecificConditions']=['점프 후 약 15초 이내 시동, READY 30분 정차/주행. 지정 래치 또는 도장 없는 차체 접지. 충전기 13.3–14V, 권장13.8V,60A 이하. 다른 HEV의 RESET 버튼 조건을 추정 적용하지 않는다.']
  if c=='HR':r['modelSpecificConditions']=['보조 차량 시동 후 2,000RPM 이상 유지하며 수분 대기. 성공 후 일정 시간 시동을 유지한다. 더블캡 배터리는 뒷좌석 쿠션/커버 아래에 있다.']
  if c in ['MX5HEV','LX3HEV']:r['applicationConstraints']+=['다른 HEV 문서의 내장 리튬 12V RESET 버튼·30초 조건을 이 문서에 전이하지 않는다.']
  rules.append(r)
 extra=[('A01',2026,54,58),('HREV',2026,41,49),('NE1N',2026,63,66),('SX2EV',2025,58,61),('DN8HEV',2026,12,14),('US4HEV',2026,14,15),('MX5HEV',2026,14,17),('SX2HEV',2027,14,17),('LX3HEV',2027,14,15)]
 for c,y,a,b in extra:
  hev=c.endswith('HEV')
  r=rule(c,y,'POWERTRAIN_WARNING_PANEL',list(range(a,b+1)),['계기판 경고 절과 별도로 제공되는 EV/HEV 시작 장의 경고·메시지.'],['서비스 경고가 자가점검 뒤 지속되거나 주행 중 켜지면 정비한다. READY 소등·점멸과 정상 EV 모드 표시를 구분한다.','전원 공급 장치 정차 경고는 안전 정차 후 견인 점검한다. 회생제동 경고와 브레이크 경고 동시 점등은 제동 성능 저하를 전제로 주의하여 정비한다.'],[],['모든 경고를 재시동만으로 해제하려 하지 않는다. 메시지 제목의 정차·시동 금지를 본문 요약에서 누락하지 않는다.'])
  if hev:
   r['orderedActions']+=['하이브리드 시스템 점검은 정비하며, 안전 정차 문구·READY 점멸·약10초 경고음이면 정차한다. 시동 금지 메시지와 1회 경고음/매우 낮은 SOC는 시동을 반복하지 않고 정비한다.']
   if c in ['US4HEV','LX3HEV']:r['orderedActions']+=['충전을 위해 정차하라는 배터리 부족 메시지는 안전 정차 후 P로 변속한다. 외부 충전 커넥터 사용으로 바꾸지 않는다.']
   if c!='LX3HEV':r['orderedActions']+=['배터리 시스템 냉각수 메시지는 주행 중지 후 냉각수량을 확인하고 해당 냉각수 절의 냉간·규격·주의에 따라 조치한다.']
  else:
   low,limit={'A01':(20,10),'HREV':(16,7),'NE1N':(15,7),'SX2EV':(20,10)}[c]
   r['modelSpecificConditions']=[f'저충전/출력 제한 메시지 SOC 기준은 각각 {low}%/{limit}%. 주행 가능 거리는 조건부 예시이며 남은 거리 보장이 아니다.']
   r['orderedActions']+=['저충전은 즉시 충전한다. 출력 제한 시 급가속·급출발을 피하고 경사로 후퇴 가능성에 유의한다. 낮은 배터리 온도는 출발 전 충전하며 온도가 올라간 뒤에도 메시지가 남으면 정비한다.','배터리 과열은 안전 정차·시동 OFF 후 충분히 식힌다. 계속 경고되면 운행을 삼가고 견인/정비한다.','연결된 충전 커넥터는 분리 후 시동한다. 충전 중단은 커넥터·인렛 손상/이물질과 충전기를 확인하고 정상 충전기에서 반복되면 정비한다.']
   if c=='HREV':r['applicationConstraints']+=['출력 제한 원인에 냉각 계통 이상/주행 고장도 포함한다. 단독 점등=무조건 정상으로 분류하지 않는다. 충전 중 적색은 정상 표시다.']
   if c=='NE1N':r['sourceAmbiguities']=['과열 메시지 제목은 즉시 정차 후 대피, 조치 열은 시동 OFF 후 냉각 대기. PDF65/인쇄60 원본 이미지로 둘 다 확인. 대피 요구를 삭제하거나 차량 옆 대기로 자동 바꾸지 않는다.'];r['orderedActions']+=['과열 경고의 메시지 제목에 명시된 정차 후 대피 지시를 보존한다.']
  rules.append(r)
 accident=json.loads((RAW/'ev-accident-units.json').read_text(encoding='utf-8'))+[{'id':'HREV-2026-EV_ACCIDENT','pages':[50,51,52]}]
 for u in accident:
  c,y=u['id'].split('-')[:2]
  r=rule(c,y,'EV_ACCIDENT',u['pages'],['EV 사고·화재·침수 또는 비상 제동 필요 상황.'],['사고 시 비상 경고 후 안전 정차·시동 OFF·대피하고 접근을 통제한다. 가스 누출이 의심되면 환기 후 즉시 대피한다.','화재는 대피·접근 통제 후 소방서에 EV 화재임을 알리고 지시를 따른다. 침수는 시동 OFF 후 키를 들고 대피하여 긴급출동에 알린다.','배터리 화재 차량 이동·견인은 재발화 가능성 때문에 소방차 동행을 요청한다.'],['침수 EV에 접근·접촉하지 않는다. 누출액·고전압 부품에 접촉하지 않는다.','배터리 화재를 진압하려 무리하게 차량에 접근하지 않는다.'],['물 대량 공급 필요성은 소방 대응 설명이며 운전자에게 화재 접근을 권장하는 지시로 바꾸지 않는다.'])
  r['reviewMethod']='217 exact-normalized source sentences and source associations directly read; HREV50–52 additionally read in full.'
  if c=='HREV':r['modelSpecificConditions']=['견인은 전륜/후륜 구동 차이를 지운 공통 규칙 금지. HREV는 네 바퀴 상차를 우선하며 두 바퀴 견인은 구동 후륜을 들어 올린다.']
  else:r['modelSpecificConditions']=['해당 EV 절의 모든 바퀴 들기 요구가 있는 경우 구동 바퀴를 접지시키지 않는다. 차량별 견인 장비 조건을 별도 보존한다.']
  if c=='ME':r['orderedActions']+=['비상시 매립형 외부 손잡이 앞부분(차량 전면 쪽)을 눌러 돌출시킨 후 최대한 당겨 문을 연다.']
  rules.append(r)
 b=(RAW/'jump-sentences.json').read_bytes()
 (OUT/'hyundai-pdf-supplement-review.json').write_text(json.dumps({'schemaVersion':1,'rules':rules,'readingLedger':{'uniqueUnitsRead':603,'allUnitIndicesRead':list(range(603)),'sha256':hashlib.sha256(b).hexdigest()},'runtimeApproved':False},ensure_ascii=False,indent=2),encoding='utf-8')
 print(len(rules))
if __name__=='__main__':main()
