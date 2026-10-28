"""Encode AI readings of special-equipment warnings; no runtime approval."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/manual-review/2026-10-28'
RAW=ROOT/'.local/manual-review/2026-10-28/audit'
rules=[]
def add(code,key,pages,topic,conditions,actions,prohibitions=None,restart=None):
 year=2026 if code=='US4SV' else 2025
 pdf=ROOT/f'.local/manual-corpus/2026-10-28/hyundai/{code}-{year}-omManual.pdf'
 rules.append(dict(ruleId=f'AUDIT-{code}-{key}',documentIds=[f'HYUNDAI-{code}-{year}'],topic=topic,
 sources=[dict(URL=f'https://ownersmanual.hyundai.com/full_pdf/{code}/{year}/ko_KR',hash=hashlib.sha256(pdf.read_bytes()).hexdigest(),locator={'pdfPages':pages})],
 conditions=conditions,orderedActions=actions,prohibitions=prohibitions or [],restartCriteria=restart or [],
 requiredContext=['특장 장비 종류와 장착 여부','해당 장비 제작사·컨트롤러 형식','기본 차량 설명서 및 정확한 연식'],
 reviewStatus='SOURCE_REVIEWED',reviewMethod='PDF 해당 고장/경보 본문과 연결 절차 직접 읽기; 표 6쪽 이미지 대조',
 reviewer='AI',runtimeApproved=False,scope='special_equipment_supplement',sdkSignal=None))
def main():
 add('US4SV','CHILD-SEAT',[16,26],'어린이 보호차 좌석·벨트 표시',['빨강 미착용, 초록 착용, 노랑 점멸 통신·컨트롤러 이상'],['실제 탑승자를 직접 확인한다.','가방·자세·시트 커버로 인한 감지 오류를 구분하고 통신 이상은 점검한다.'],['표시만 보고 어린이 부재를 확정하지 않는다.','좌석을 임의 개조하지 않는다.'])
 add('US4SV','STOP-SIGN',[19,28],'정지 표시 장치 이상',['정지 표시 장치 표시등 점멸'],['장치 버튼을 꺼 강제 복귀시키고 재작동 조건을 확인한다.','통신 이상이 지속되면 점검한다.'],['장치가 펼쳐진 채 주행하지 않는다.'])
 add('US4SV','SIDE-STEP',[20,21],'어린이차 전동 스텝 작동 불량',['정차·P·스텝 스위치 ON·문 열림 조건에서 작동하지 않음'],['P와 스위치 LED를 확인하고 스위치·문을 재작동한다.','필요 시 해당 엔진 형식의 전동 사이드 스텝 퓨즈를 1분 분리 후 복원하고 자동 작동 1회 및 문 3회 작동을 확인한다.','이상이 지속되면 사용을 중단하고 점검한다.'],['LPG 메인 정션과 HEV SUB 정션을 혼동하지 않는다.','개조·고압 세척·고장 상태 사용을 하지 않는다.'])
 add('US4SV','PASSENGER-CHECK',[22,23,24],'하차 확인 및 안전벨 경보',['시동 종료 후 1분 30초 이내 후방 확인 버튼 미입력 또는 갇힌 어린이 안전벨 작동'],['차내 탑승자를 직접 확인·구조한 후 확인 버튼을 누른다.','안전벨은 우측 도어 잠금 해제·구조 음성·적색 점멸을 동반한다.','고장 초기화는 LPG 메인/HEV SUB의 스쿨버스 퓨즈를 1분 분리 후 복원하며, 지속되면 정비한다.'],['경보를 끄려고 시동만 다시 걸어 탑승자 확인을 생략하지 않는다.','퓨즈 분리 중 모든 특장 장비가 중단됨을 무시하지 않는다.'])
 add('US4SV','LIFT-PLATE',[55,56,57],'휠체어 리프트 안전판 이상',['내측 안전판이 완전히 펴지지 않거나 상승 시 외측 안전판이 서지 않음'],['작동·사용을 중단하고 제작사에 점검을 요청한다.','평탄한 후방 3m 공간에서 한 대만 플랫폼 전체에 놓고 휠체어 브레이크를 체결한다.'],['안전판 이상 상태에서 승강하지 않는다.'])
 add('US4SV','LIFT-EMERGENCY',[58,59,60],'리프트 전원·유압·리모컨 고장',['정상 제어 불가로 비상 수동 조작 필요'],['원문 수동 펌프·밸브 절차에 따라 바닥 높이까지 천천히 내리고 밸브를 닫은 뒤 휠체어를 싣는다.','브레이크 체결 후 천천히 지면까지 내리고 하차시킨 다음 밸브를 닫아 수동 펌프로 수납한다.','비상 조작 후 제작사 점검을 받는다.'],['밸브를 갑자기 열어 급강하시키지 않는다.','본문 DEPLOY/DOWN 표기 불일치가 있어 버튼 이름만으로 자동 안내하지 않는다.'])
 add('US4SV','AMBULANCE-POWER',[75,76,79,81,94,95,99,103],'구급차 보조 전원·전장 고장',['주 배터리 방전 또는 특장 전장 작동 불량'],['장비 형식에 맞는 퓨즈·정격을 확인하고 자격 있는 정비를 받는다.','이중 배터리형 비상 시동은 비상 스위치 ON 후 시동을 걸고 다시 OFF로 복귀한다.','정차 중 전력 사용을 줄이고 해당 220V 인버터는 시동 조건을 지킨다.'],['기본차 퓨즈와 특장 퓨즈를 혼동하지 않는다.','배터리 전압·결선 절차를 다른 배터리 형식에 전용하지 않는다.'])
 add('US4SV','CAMPER-ROOF',[128,133,134,135,143,144,145],'캠퍼 루프 고장·작동 거부',['잠금·좌우 모터·속도·저전압·장애물 관련 오류'],['시동·P·침대 및 창문 위치·실내 확인 조건을 확인한다.','내부 사람과 물건 및 외부 눈·장애물을 제거하고 작동 간 1분 간격을 둔다.','지속되는 오류나 불균형은 강제 작동하지 말고 정비한다.','비상 하강은 비상 상황에 한정한다.'],['열린 루프로 주행하지 않는다.','루프 침대 200kg 이상 적재 및 사람이 남은 상태의 하강을 하지 않는다.'],['원문 속도 오류는 재시동 안내가 있으나 다른 모터·잠금 고장까지 재시동으로 해결된다고 일반화하지 않는다.'])
 add('US4SV','CAMPER-ALARM',[127,134,135],'캠퍼 정상 상태·경보 구분',['빨강 경고/흰색 알림; 배터리 5% 이하·청수 25% 이하·오수 100%'],['잔량·만수 상태를 확인한다.','청수 부족 시 펌프가 제한되므로 물을 확인하고 오수 만수는 비운다.','주행 중 외부등 제한은 정상 조건으로 구분한다.','컨트롤러 통신 오류는 전원을 재작동하고 지속되면 정비한다.'],['컨트롤러 종료 누름 시간이 본문 2초/3초로 달라 하나의 확정값으로 자동 안내하지 않는다.'])
 add('US4SV','CAMPER-HEATER',[129,134,139,150,151],'캠퍼 히터 오류',['저전압 20초, 팬·시동 실패·안전시간·외부 전압 오류 등'],['컨트롤러로 정상 종료하고 약 4분 냉각 팬 운전을 보장한다.','LED가 꺼지면 지정 퓨즈와 전원을 확인하고 지속 고장은 제작사에 문의한다.','Airtronic D2 표의 12V 10.5/16V 및 24V 21/32V 경계는 해당 히터 형식에서만 사용한다.'],['흡배기구를 막지 않는다.','주유 중 사용하거나 후방 텐트로 배기가 유입되게 하지 않는다.','강제 전원 차단으로 냉각을 생략하지 않는다.'])
 add('US4SV','CAMPER-WATER',[152,158,161],'캠퍼 냉장고 성에·물 펌프',['성에, 청수 부족 또는 결빙'],['냉장고 음식물을 옮긴 뒤 온도를 높이고 문을 열어 해동·건조한다.','겨울에는 물을 배수하고 펌프 공급 상태를 확인한다.'],['날카로운 도구로 성에를 제거하지 않는다.','빈 탱크·동결 상태에서 펌프를 운전하지 않는다.'])
 add('US4SV','CAMPER-AC',[162],'캠퍼 220V 전원 이상',['콘센트 전원 불량 또는 물 유입'],['전원 불량은 차단기를 확인한다.','물 유입은 메인 전원과 인버터를 끄고 점검을 받는다.','사용 후 및 차량 이탈 전 인버터를 끈다.'],['젖은 손·금속 물체로 전기 장비를 취급하지 않는다.','원문 권장 1600W 범위를 다른 인버터에 일반화하지 않는다.'])
 add('HRSV','BODY-DAMAGE',[12,15,37,56],'특장 차체·등화 이상',['배수구 막힘, 마개·도어 실 손상, 작업등 사용'],['막힘은 제거하고 손상 부품은 교체한다.','작업등은 하차 전 끄며 장시간 시동 OFF 사용으로 인한 방전을 방지한다.'])
 add('HRSV','WING',[41,43],'윙바디 작동 중 이상',['윙 구동 중 정지 필요 또는 정비 필요'],['버튼을 놓아 작동을 멈추고 사용 후 전원을 끄고 잠근다.','제작사 표지를 확인해 해당 업체에 점검을 요청한다.'],['고정 스토퍼를 잠근 상태에서 구동하지 않는다.'])
 add('HRSV','REFRIG-LEAK',[69,70,74],'냉동기 냉매 누출·냉각 불량',['비정상 소음, 냉각 실패 또는 냉매 누출 의심'],['적재 전이면 운행·적재를 진행하지 않고 점검한다.','이미 실린 냉장 화물은 냉장 보관소로 옮기고 제작사 정비를 받는다.','접합부 누유·기포 확인 시 보호 장갑과 보안경을 사용한다.'],['주기적 약 1초 틱 소리만으로 고장을 단정하지 않는다.'])
 add('HRSV','REFRIG-FROST',[81,102],'냉동기 성에 및 제상',['성에 제거 필요'],['장치를 정지하고 안전한 장소에 주차해 도어를 열어 해동한다.','컨트롤러별 제상 시간과 자동·수동 비활성 조건을 확인한다.'],['0~9분과 0~30분 등 서로 다른 컨트롤러 설정을 합치지 않는다.'])
 add('HRSV','REFRIG-A-SENSOR',[83,89],'냉동기 A형 OPn/OPen·SHt/SHrt',['온도 센서 단선·단락'],['커넥터와 배선 피복·센서를 점검하고 필요한 부품을 교체한다.','센서 이상이어도 설정 0°C 이하 냉방/초과 난방 비상 운전이 가능하므로 고장 표시를 계속 추적한다.'],['계속 작동한다는 이유로 정상이라고 판단하지 않는다.','트윈 컴프레서의 Lo 표시는 정상인 경우가 있어 다른 컨트롤러 오류로 단정하지 않는다.'])
 add('HRSV','REFRIG-A-FANS',[83],'냉동기 A형 팬 고장',['증발기 또는 응축기 팬 작동 불량'],['해당 팬 모터·배선·커넥터를 점검하고 정비한다.'])
 add('HRSV','REFRIG-A-COMMS',[83],'냉동기 A형 통신·무전원',['---. 표시 또는 디스플레이 꺼짐'],['통신 커넥터·케이블·릴레이 박스를 확인한다.','무전원은 통신·접지·전원 경로를 점검한다.'])
 add('HRSV','REFRIG-B-SENSOR',[108,109],'냉동기 B형 SHt·Opn',['센서 단락 또는 단선'],['센서·배선을 점검한다.','이 형식은 센서 오류에서도 연속 냉각하므로 표시와 화물 온도를 함께 확인한다.'],['A형의 설정 온도별 비상 난방 절차를 전용하지 않는다.'])
 add('HRSV','REFRIG-B-FAN',[109],'냉동기 B형 EVAFAN',['증발기 팬 작동 이상'],['퓨즈·릴레이·모터·배선을 점검한다.'])
 add('HRSV','REFRIG-B-PRESSURE',[109],'냉동기 B형 CE.r',['고저압 또는 컴프레서 과부하 관련 오류'],['퓨즈·릴레이·배선 및 원인을 점검한다.','오류 시 컴프레서가 정지함을 확인한다.'],restart=['원인이 해소되면 자동 복귀하나 고장 원인 점검을 생략하지 않는다.'])
 add('HRSV','REFRIG-B-POWER',[109],'냉동기 B형 표시 꺼짐',['컨트롤러 무전원'],['접지·메인 릴레이·전원을 점검한다.'])
 add('HRSV','GATE-WIRE',[121,122,127,128],'파워 게이트 와이어·비상 정지',['와이어 손상 또는 이동 중 정지 필요'],['와이어 한 가닥이라도 끊어지면 사용 전 교체한다.','평지에서 자동 P/수동 N·주차브레이크·고임목을 사용한다.','비상 시 리모컨 전원 스위치를 OFF로 되돌려 정지한다.'],['작동 표시 LED·움직임 경고음을 고장으로 단정하지 않는다.'])
 add('HRSV','GATE-REMOTE',[138,142,155,156,158],'트랜스 파워 게이트 리모컨 고장',['무선 리모컨 고장·분실'],['유선 비상 스위치를 사용하고 원하는 위치에서 버튼을 놓는다.','사용 후 비상 스위치를 분리해 보관하고 전원을 끈다.'],['끝 위치에서 버튼을 계속 누르지 않는다.','해당 형식 600kg 한도를 초과하거나 지게차를 올리지 않는다.','플랫폼 적재 상태로 주행하지 않는다.'])
 add('HRSV','TANK-LEAK',[173,176,180,181,182,183,184,185,186,189],'이동 주유차 누유·화재 비상',['호스 누유 또는 화재'],['누유 시 급유를 중단하고 화재를 예방한다.','화재 시 비상 레버로 양쪽 바닥 밸브를 닫는다.','작업 시 정차·주차브레이크·고임목·정전기 접지 및 감시 인원을 확보한다.','주행 전 PTO를 해제한다.'],['허가되지 않은 연료를 취급하지 않는다.','공회전 펌프 운전·화기·무감시 급유를 하지 않는다.'])
 add('HRSV','DUMP',[194,195,196,197,198,200],'덤프 경고음·유압 이상',['적재함 상승 경고음 또는 호스 누유·균열'],['적재함을 완전히 내려 경고음이 꺼진 뒤 장치 전원을 끈다.','누유·균열 호스는 제작사 규격으로 교체한다.','하부 정비 전 시동을 끄고 적재함 지지대와 고임목으로 확실히 고정한다.'],['적재함 상승 또는 장치 전원 ON 상태로 주행하지 않는다.','연약·경사 지면에서 덤프 작업하지 않는다.','짐을 실은 하강 중간에 임의로 정지하지 않는다.'])
 coverage=[]
 for code,year in [('US4SV',2026),('HRSV',2025)]:
  coverage.append({'documentId':f'HYUNDAI-{code}-{year}','manualRole':'special_equipment_supplement','rules':sum(code in r['ruleId'] for r in rules),
   'reviewedPdfPages':sorted(set(p for r in rules if code in r['ruleId'] for p in r['sources'][0]['locator']['pdfPages'])),
   'scope':'고장표·경고/알림표 및 연결 특장 비상 절차; 일반 조작·배선도·정기 정비 전체의 전수 승인 아님',
   'remainingDependencies':['해당 기본차 정확 연식 설명서','장비 제작사 별도 설명서와 실제 장착 컨트롤러 확인'],
   'runtimeApproved':False})
 (OUT/'audit-hyundai-special-rules.json').write_text(json.dumps({'rules':rules,'coverage':coverage,'visualPdfPages':{'US4SV-2026':[21,24,134,135],'HRSV-2025':[83,109]},'runtimeApproved':False},ensure_ascii=False,indent=2),encoding='utf8')
 p=ROOT/'.local/manual-corpus/2026-10-28/hyundai/A01-2026-omManual.pdf'
 anomaly={'documentId':'HYUNDAI-A01-2026','URL':'https://ownersmanual.hyundai.com/full_pdf/A01/2026/ko_KR','sourceSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'locator':{'pdfPage':126,'printedPage':'4-8'},'finding':'전기차 ST1 충전 경고 항목에 구동벨트 파손·장력 점검 문구가 실제 인쇄되어 있음. OCR 오류가 아님.','reviewMethod':'PDF 페이지 이미지 직접 대조','action':'전기차용 구동벨트 조치 자동 생성 보류; 공식 정정 또는 제작사 확인 필요','runtimeApproved':False}
 anomalies=[anomaly]
 for code,year,page,printed in [('NE1N',2026,179,'174'),('SX2EV',2025,172,'167')]:
  p=ROOT/f'.local/manual-corpus/2026-10-28/hyundai/{code}-{year}-omManual.pdf'
  anomalies.append(dict(documentId=f'HYUNDAI-{code}-{year}',URL=f'https://ownersmanual.hyundai.com/full_pdf/{code}/{year}/ko_KR',sourceSha256=hashlib.sha256(p.read_bytes()).hexdigest(),locator={'pdfPage':page,'printedPage':printed},finding='전기차 충전 경고에 구동/드라이브 벨트 및 엔진 과열 또는 오버히트 문구가 실제 인쇄되어 있음. OCR 오류가 아님.',reviewMethod='PDF 페이지 이미지 직접 대조',action='벨트 점검·엔진 과열 안내를 전기차에 자동 적용하지 않음; 공식 정정 또는 제작사 확인 필요',runtimeApproved=False))
 (OUT/'audit-source-anomalies.json').write_text(json.dumps({'anomalies':anomalies},ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({'rules':len(rules),'documents':coverage},ensure_ascii=False))
if __name__=='__main__':main()
