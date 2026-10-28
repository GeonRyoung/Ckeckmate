"""Persist explicit source reading completed for TPMS and Porter ADAS references."""
import json, hashlib, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/manual-review/2026-10-28'
RAW=ROOT/'.local/manual-review/2026-10-28/hyundai/procedures'
MAN=json.loads((ROOT/'data/manual-research/2026-10-28/hyundai-manifest.json').read_text(encoding='utf-8'))['documents']
def source(code,year,nums):
 d=next(x for x in MAN if x['modelCode']==code and x['year']==str(year));p=json.loads((ROOT/d['textPagesPath']).read_text(encoding='utf-8'))
 return {'url':d['sourceURL'],'documentSha256':d['sha256'],'locator':{'pdfPages1Based':nums},'passageSha256':hashlib.sha256('\n'.join(p[n-1] for n in nums).encode()).hexdigest()}
def rule(code,year,topic,pages,conditions,actions,prohibitions=(),notes=()):
 return {'ruleId':f'HY-REF-{code}-{year}-{topic}','documentIds':[f'HYUNDAI-{code}-{year}'],'topic':topic,'conditions':conditions,'orderedActions':actions,'driverProhibitions':list(prohibitions),'applicationConstraints':list(notes),'restartCriteria':None,'sources':[source(code,year,pages)],'reviewStatus':'SOURCE_REVIEWED','reviewer':'AI','reviewMethod':'Direct full source passage reading; repeated TPMS passages compared against fully read DN8/NE1 canonical with every changed group read','runtimeApproved':False,'expertApproved':False,'structuredEncodingComplete':False}
def main():
 units=json.loads((RAW/'tpms-bounded-units.json').read_text(encoding='utf-8'));rules=[]
 for u in units:
  code,year=u['id'].split('-')[:2]
  r=rule(code,year,'TPMS',u['locator']['pdfPages1Based'],['저압 점등과 시스템 이상 점멸 후 점등을 구분한다.'],['저압이면 속도를 낮추고 급격한 조향을 피하며 타이어 상태와 해당 규격 공기압을 점검한다.','냉간 상태(주행 종료 후 3시간 이상 또는 1.6km 이내 주행)에서 추천 압력에 맞춘다.','시스템 이상은 정비 점검한다. 갑작스러운 타이어 손상으로 차체가 불안정하면 가속페달에서 발을 떼고 안전하게 정차하여 확인한다.'],['저압 상태로 계속 주행하거나 시스템을 임의 개조하지 않는다.'],['TMK 주입·봉합과 차종별 압력 수치는 별도 절차와 규격 대조가 필요하며 이 규칙에서 임의 수치를 생성하지 않는다.'])
  r['sources'][0]['boundedPassageSha256']=u.get('boundedSha256');r['sources'][0]['boundedLocalPath']=u['localPath']
  r['sources'][0]['scope']='TPMS section only; source page range can include adjacent puncture chapter, not approved by this record'
  if code in ['AX','AXEV']:
   r['conditions']=['휠 속도로 반경·진동을 판단하는 간접식 TPMS. 저압은 점등, 고장은 70초 점멸 뒤 점등, 초기화 완료는 4초 점멸 뒤 소등.']
   r['orderedActions']+=['모든 타이어를 추천 압력으로 맞춘 뒤 시동 ON·정차 상태에서 모드 버튼→타이어 공기압→OK 길게→저장을 선택한다. 완료 팝업과 4초 점멸 후 소등을 확인한다.','완료 신호가 없으면 정차 상태의 메뉴 진입부터 다시 시도한다. 정차 후 설정 메시지가 뜨면 정차 후 OK를 길게 누른다. 초기화 뒤에도 고장 표시가 남으면 정비한다.']
   r['driverProhibitions']+=['압력을 조정하지 않은 상태에서 초기화하지 않는다.']
   r['applicationConstraints']+=['직접식 압력 센서·예비 휠 10분 경고·RF 간섭 설명을 이 간접식에 전이하지 않는다. 타이어/휠 수리·교환·위치 변경·압력 조정·저압 경고·서스펜션 또는 원문 ABC/ESC 교환 시 초기화 요구.']
  else:
   r['orderedActions']+=['압력 센서가 장착된 휠로 교환한 후 몇 분 주행해도 경고가 꺼지지 않으면 정비한다.']
   r['applicationConstraints']+=['시스템 고장 때 저압 위치 표시가 없어질 수 있어 화면만으로 정상 압력을 단정하지 않는다. RF 간섭 가능성만으로 고장을 정상 처리하지 않는다.']
  rules.append(r)
 for code,year,pages in [('QX',2027,[331,332,333]),('HR',2026,[262,263,264])]:
  rules.append(rule(code,year,'TPMS',pages,['직접식 TPMS 적용 사양의 저압 또는 고장 경고.'],['감속하고 급커브를 피한다. 타이어 상태·추천 압력을 점검하고 조절이 불가능하면 해당 차량의 예비 타이어 교환 절차를 따른다.','냉간(최근 3시간 주행하지 않음 또는 1.6km 이내 주행)에서 압력을 맞춘다. 점멸 후 점등은 정비한다.','센서 휠 교환 후 몇 분 주행해도 소등되지 않으면 정비한다.'],['시스템을 임의 조절·개조하지 않는다.'],['QX 고장 점멸은 클러스터 원문 70초를 보존한다. HR에 같은 수치를 추정 적용하지 않는다.']))
 (OUT/'hyundai-pdf-tpms-review.json').write_text(json.dumps({'schemaVersion':1,'rules':rules,'notFound':[{'documentId':'HYUNDAI-HREV-2026','topic':'TPMS','status':'NO_DEDICATED_WARNING_SECTION_FOUND','basis':'cluster and emergency chapter read; entire text TPMS hits only TMK cautions, not proof of no equipment'}]},ensure_ascii=False,indent=2),encoding='utf-8')
 ad=[]
 for code,pages in [('HR',[138]),('HREV',[220])]:
  ad.append(rule(code,2026,'RVM',pages,['영상이 비정상 색·깜빡임 또는 정상 표시되지 않음.'],['주변을 직접 확인하고 지속 이상은 정비한다. 렌즈를 깨끗하게 유지한다.'],['강한 염기성·휘발유·아세톤 등 용제로 렌즈를 닦지 않는다.'],['영상 거리와 실거리가 다를 수 있음.']))
 for code,pages in [('HR',[139,140,141]),('HREV',[220,221,222])]:
  ad.append(rule(code,2026,'PDW',pages,['초음파 센서 오염·결빙 또는 경고음 이상.'],['오염을 제거하고 결빙이 녹은 뒤 작동을 확인한다. 지속 이상은 정비한다. 후방 장애물은 직접 확인한다.']+(['부드러운 헝겊으로 닦는다. R 진입 때 정상 1회 경고음 대신 무음·반복음이면 손상/비작동 조건을 확인하고 고장이면 정비한다.'] if code=='HREV' else []),['센서를 누르거나 충격·긁힘·직접 고압세척을 하지 않는다.'],['HR 거리 단계 60–120/30–60/30cm 이내, HREV 80–120/40–80/40cm 이내를 섞지 않는다. HREV는 5km/h 이상 성능 제한, 10km/h 이상 장애물 경고 없음.']))
 for code,pages in [('HR',[232,235,236,237]),('HREV',[194,197,198,203])]:
  ad.append(rule(code,2026,'FCA',pages,['기능 OFF 표시, 카메라 가림, 고장 경고를 구분한다.'],['가림이면 카메라 주변 이물질을 제거한다. 기능 ON 상태의 지속 경고 또는 고장 문구는 정비한다.','긴급제동 정차는 약2초 유지되므로 즉시 브레이크 페달을 밟고 주변을 확인한다.','센서 충격·유리/카메라 교환·재장착은 경고가 없어도 점검한다.'],['카메라 임의 탈거·충격·물기 유입·앞유리 스티커/필름 부착을 피한다.','사람·물체로 기능을 시험하지 않는다.'],['경고문이 일정 시간 후 사라지는 것은 고장 해소 증명이 아니다. 시동 직후 오염/개활지 등은 경고 없이 제한될 수 있다. ESC 경고와 동시 표시 가능.']))
 ad.append(rule('HR',2026,'LDW',[248,249,250,251],['흰색 미인식/약60km/h 미만, 초록 인식/약60km/h 이상, 황색·고장 문구를 구분한다.'],['차선 이탈 경고 시 운전자가 직접 조향한다. 황색 고장 표시와 문구는 정비한다. 유리·카메라 교환/재장착 후 보정 점검한다.'],['불필요한 급조향·카메라 탈거·충격·물기·반사물 배치를 피한다.'],['LDW는 자동 조향 기능이 아니다. HREV의 LKA 동작을 전이하지 않는다.']))
 ad.append(rule('HREV',2026,'LKA',[203,204,205,206,207,208],['황색 고장 표시·경고문 또는 핸즈오프.'],['핸들을 잡고 직접 조향한다. 황색 고장 표시·문구는 정비한다. 유리·카메라·조향 부품 교환 후 점검한다.','악천후·불량 노면·잦은 조향·견인 때 기능을 끄고 직접 집중 조향한다.'],['핸들에 물체를 붙이거나 카메라 임의 탈거·필름 부착을 하지 않는다.'],['시동/카메라 재부팅 뒤 약15초 비작동은 고장 복구 보증이 아니다.']))
 ad.append(rule('HREV',2026,'DAW',[209,210,211],['휴식 권유 또는 주의 경고 시스템 고장.'],['피곤하면 권유 여부와 무관하게 안전하게 주정차하여 쉰다. 시스템 고장 문구는 정비한다.','전방 차량 출발 알림 후 주변을 직접 판단하고 출발한다.'],[],['시동 OFF/벨트 해제 후 도어 개방/10분 정차에 의한 주의 수준 초기화는 고장 수리나 실제 피로 회복의 증거가 아니다. 카메라 관리 참조는 LKA와 연결하여 읽음.']))
 ad.append(rule('HR',2026,'CRUISE_UNEXPECTED_CANCEL',[246,247],['명시된 자동 해제 조건 외의 일시 해제.'],['정비 점검한다. RES 재설정은 이전 속도와 도로 상황을 확인할 수 있을 때만 사용한다.'],['불량 노면·악천후·급커브·급경사·견인 때 사용하지 않는다.'],['정상 자동 해제 목록을 고장으로 단정하지 않는다.']))
 (OUT/'hyundai-legacy-adas-review.json').write_text(json.dumps({'schemaVersion':1,'rules':ad,'inventoryCorrection':'HREV106–107 was TOC; actual FCA/LKA/DAW linked passages added. HR additionally FCA/LDW/cruise fault references found outside two original candidates.','excludedGeneralPerformanceScope':True},ensure_ascii=False,indent=2),encoding='utf-8')
 print('TPMS',len(rules),'legacy ADAS',len(ad))
if __name__=='__main__':main()
