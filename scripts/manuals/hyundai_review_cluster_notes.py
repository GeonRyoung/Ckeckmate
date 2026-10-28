"""Curated semantic cluster review. Entries are authored after reading the specified pages.

Shared text is a reviewed paraphrase, not a rule inferred from a keyword hit.
Linked procedures retain a separate completion gate.
"""
import json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MAN=json.loads((ROOT/'data/manual-research/2026-10-28/hyundai-manifest.json').read_text(encoding='utf-8'))['documents']
OUT=ROOT/'data/manual-review/2026-10-28/hyundai-pdf-cluster-review.json'
TOPICS={
 'BELT':('미착용 상태의 시동 ON/벨트 해제, 6초 경고음 및 20km/h 이상 재경고','안전벨트를 착용한다. 착용하면 표시와 경고음이 멈춘다.'),
 'SRS':('시동 ON 초기 3~6초 점등은 정상; 처음부터 표시되지 않거나 이후에도 남음','에어백·프리텐셔너 점검을 받는다.'),
 'BRAKE':('주차브레이크 해제 후 경고 지속 또는 주행 중 경고','급제동을 피하여 안전한 곳에 서서히 정차한다. 제동이 부족하면 페달을 강하게 밟고, 해당 사양의 비상 제동 방법을 따른다. 브레이크액을 확인하고 보충 후에도 지속되면 정비한다. 브레이크액 부족 상태로 출발하지 않는다.'),
 'ABS':('초기 약3초 이후 지속 또는 주행 중 점등','안전 정차 후 시동을 끄고 다시 켠다. 약3초 내 소등되지 않거나 주행 중 재발하면 정비한다.'),
 'EBD':('ABS와 브레이크 경고가 현재 동시에 점등','고속 주행과 급제동을 피하고 즉시 정비 점검을 받는다.'),
 'EPS':('초기 약3초 이후 지속하거나 깜빡임','전동 파워 스티어링 점검을 받는다.'),
 'FUEL':('연료 부족 노란색 경고 또는 부족 메시지','즉시 연료를 보충한다. 완전 소진 상태로 운전하지 않는다.'),
 'LPG_OVERFILL':('LPG 사양에서 빨간색 연료 표시','LPG 과충전 점검을 받는다. 노란색 연료 부족과 구별한다.'),
 'OIL':('주행 중 엔진오일 압력 경고','안전 정차 후 오일량을 확인하고 부족하면 보충한다. 보충해도 지속되면 정비한다. 켜진 상태로 계속 운전하지 않는다. 실제 오일 점검 절차는 별도 절을 따른다.'),
 'MIL':('초기 약3초 이후 엔진 경고가 남거나 점멸','가능한 빨리 엔진·연료·배기 제어 점검을 받는다. 시동이 걸리지 않으면 견인한다. 연료캡 관련 분기는 해당 연료 사양에 한해 확인하며, 다시 잠가도 지속되면 점검한다.'),
 'CHARGE12':('12V 충전 경고','배터리·충전 계통을 확인하고 경고가 남으면 정비한다. 내연기관/HEV는 원문이 드라이브벨트 점검도 안내한다.'),
 'TPMS':('저압 점등 또는 약1분 점멸 후 고정점등; 시동 초기 약3초','실제 타이어 압력을 확인해 차량 권장 압력으로 유지한다. 최초 표시 누락 또는 점멸 후 지속점등은 시스템 점검을 받는다. 저압과 시스템 이상을 분리한다.'),
 'EPB':('초기 약3초 이후 지속 또는 주행 중 점등','전자식 파킹 브레이크 점검을 받는다.'),
 'AUTO_HOLD':('흰색 준비/초록색 정차 유지/노랑 또는 주황색 이상','이상 색상인 경우 정비 점검을 받는다. 정상 준비·작동을 고장으로 안내하지 않는다.'),
 'FCA':('초기 주황 약3초; 주황 지속은 해제/이상, 빨강 점멸은 제어 개입','안전 기능 설정과 센서 가림을 확인한다. 설정하고 이물질을 제거해도 경고가 남으면 정비한다.'),
 'LKA':('초기 주황 약3초; 회색 대기, 초록 가능/점멸 개입, 주황 해제·이상','차로 안전 설정 및 전방 카메라 가림을 확인한다. 설정하고 이물질을 제거해도 이상 표시가 남으면 정비한다.'),
 'LFA':('초록색 작동/회색 준비/흰색 점멸 후 준비','현재 보조 작동 상태를 확인한다. 이 정상 상태 표시만으로 정비를 권하지 않는다.'),
 'ISLA':('주황색은 해제/고장; 작동 중 제한속도 표시, 초과 시 빨강','전방 카메라 가림을 확인하고 제거 후에도 이상 표시가 지속되면 정비한다.'),
 'DAW':('주황 고정은 카메라 가림·기능 이상; 주황 점멸은 주의 경고','가림을 제거해도 이상 표시가 남으면 점검한다. 주의 경고 점멸을 고장 점멸로 합치지 않는다.'),
 'MASTER':('여러 보조 기능의 고장 또는 센서 가림 중 하나 이상','클러스터의 구체 경고 내용을 확인해 해당 기능의 조치로 분기한다. 통합등 하나로 원인을 확정할 수 없다.'),
 'LED':('LED 전조등 이상 점등 또는 부품 이상 점멸','즉시 전조등 점검을 받는다. 장기간 그대로 운행하면 수명에 영향을 줄 수 있다.'),
 'ESC':('초기 약3초; 주행 중 점멸은 자세제어 작동, 이후 고정은 이상 가능','초기 점등 후 지속 또는 주행 중 고정점등이면 정비한다. ESC OFF는 사용자가 기능을 해제한 상태로 따로 취급한다.'),
 'ISG':('흰색 대기/초록색 자동 정지/노란색 시스템 이상','정상 자동 정지와 이상 상태를 구분한다. 자세한 이상 조치는 ISG 절을 확인한다.'),
 'KEY':('키가 실내에 있으면 ACC/ON 잠시 점등, 없으면 시동 버튼 시 잠시 점멸','등록된 스마트키/지원되는 디지털키를 확인한다. 키 없음 상태에서는 시동이 걸리지 않는다.'),
 'TURN':('방향지시·비상등 정상 점멸; 비정상적으로 빠르거나 느린 점멸','전구·접지 상태를 점검한다. LED 사양은 헤드램프 문제도 점검 대상이다.'),
 'LIGHTS':('미등/하향/상향 및 하이빔 보조의 정상 상태 표시','현재 조명 상태를 확인한다. 상향등으로 마주 오는 운전자 시야를 방해하지 않도록 사용한다. 하이빔 보조는 흰색 준비·초록 작동이다.'),
 'DOOR':('도어·후드·트렁크/적재함·테일게이트 열림','주행 전 해당 개구부를 완전히 닫고 표시 소멸을 확인한다. 하차 시 닫고 잠근다. 열림 상태 방치는 배터리 방전을 일으킬 수 있다.'),
 'KEY_MESSAGES':('키 없음/인식 불가/키 전압 저하/스마트키 또는 사용자 인증 시스템 이상','키를 휴대하고 인식 불가 메시지에 따라 스마트키로 시동 버튼을 누르거나 등록된 디지털키를 지정 패드에 둔다. 키 건전지 부족이면 교체하고 시스템 이상은 정비한다.'),
 'START_MESSAGES':('브레이크 요구/P 전환/시동버튼 재시도/퓨즈 이상 메시지','브레이크를 밟고 지정 변속 위치에서 시동한다. N 종료로 ACC가 남으면 ON 전환→P→전원 종료 순서를 따른다. 반복 재시도 메시지는 정비한다. 제동 스위치 퓨즈 단선은 교체하며 즉시 교체가 불가능할 때에만 해당 모델의 비상 시동 절차를 적용한다.'),
 'DRAIN':('주차 중 외부 전기장치에 의한 과다 전류 경고','외부 전기장치를 제거한다. 제거 후에도 경고가 남으면 정비한다.'),
 'DIGITAL_KEY':('원격시동 유지·등록 키·디지털키 사용 상태 메시지','원격시동 유지 요구 시 등록된 키를 충전 패드에 두고 메시지가 사라진 뒤 주행한다. 키 등록 안내는 정상 정보다. 키가 주변에 없으면 시동을 끈 뒤 다시 켜기 어려울 수 있다.'),
 'WASHER':('워셔액 부족 메시지','워셔액을 보충한다.'),
 'OVERHEAT':('엔진 과열 메시지','주행을 중지하고 정비 점검을 받는다. 냉각계통 작업은 별도의 과열 응급 절차가 필요하다.'),
 'LAMP_MESSAGE':('방향지시등/헤드램프 LED 점검 메시지','규격에 맞지 않는 전구 또는 고장 가능성이 있으므로 점검한다.'),
 'BATTERY12_HOT':('12V 리튬 보조 배터리 과온·과충전 경고','메시지가 안전 정차를 요구하면 즉시 안전한 곳에 정차하고 정비한다. 단순 배터리 점검 메시지와 구분한다.'),
 'READY':('주행 가능 표시가 켜짐=준비 완료; 꺼짐 또는 깜빡임은 정상 주행 불가/이상 문맥','고장 상태의 꺼짐·점멸이면 정비 점검을 받는다. 단순 전원 OFF와 구분한다.'),
 'SERVICE':('전기차/HEV 서비스 경고 초기3초 이후 지속 또는 주행 중 발생','해당 구동 시스템 점검을 받는다.'),
 'REGEN':('브레이크 경고와 회생 제동 경고가 동시에 표시','제동 성능 저하를 고려하여 정비한다. 일반 회생제동 단계 표시와 다르다.'),
 'POWER':('저전압·잔량·온도 보호에 따른 출력제한 단독 표시; 서비스 경고 동시 분기','급가속·급출발을 피한다. 저잔량이면 충전한다. 서비스 경고가 함께 켜지면 정비한다. 언덕에서 밀릴 수 있다.'),
 'HV_LOW':('구동 배터리 잔량 부족 경고','즉시 충전한다. 잔여 거리 표시는 주행 조건에 따라 달라진다.'),
 'CHARGE_INDICATOR':('충전 커넥터 초록 표시','고전압 배터리 충전 상태를 나타내는 정상 표시다.'),
 'ICE':('낮은 외기온도에서 결빙 표시가 깜빡인 후 켜짐','미끄러울 수 있으므로 안전 운전한다.'),
 'LPI_WAIT':('LPI 사양에서 브레이크를 밟고 시동 버튼을 누른 뒤 시동 대기 표시','꺼질 때까지 브레이크를 계속 밟으면 자동으로 시동이 걸린다.'),
 'HEV_EV_MODE':('EV 켜짐은 모터 구동/일부 회생 및 정차 엔진정지, 꺼짐은 엔진 이용','정상 구동 모드 표시다. EV 꺼짐만으로 고장을 판정하지 않는다.'),
 'GREEN_ZONE':('내비게이션·ECO·환경보호 설정 상태에서 지정 구역 진입','정상 대기환경 보호 주행 상태다.'),
 'HEV_CHECK':('하이브리드 일반 점검/정차 후 시동 끄기/시동 걸지 말기 메시지','일반 점검은 정비한다. 정차·시동 끄기 메시지는 정차 후 끈다. 시동 금지 메시지와 극저 SOC·시동불가에서는 재시동하지 말고 정비를 요청한다.'),
 'STOP_TOW':('전원공급장치 또는 브레이크 시스템 안전 정차 메시지','안전한 곳에 정차하고 견인하여 정비한다.'),
 'HEV_CHARGE_P':('고전압 배터리 SOC가 매우 낮아 충전용 정차를 요구','안전한 곳에 정차하고 P로 변속한다.'),
 'COOLANT_LOW':('배터리 시스템 냉각수 부족','주행을 중지하고 냉각수량을 확인한다. 부족 상태로 장시간 주행하지 않는다.'),
 'BRAKE_MESSAGE':('브레이크 점검 메시지; 성능 저하/회생 불가/페달 이동량·제동거리 증가 가능','운전을 삼가고 즉시 정비한다.'),
 'START_12V':('ACC/ON 장시간 유지에 따른12V 방전 경고와 시동 요구','시동을 걸어 배터리 방전을 방지한다. 시동 금지 경고가 동시에 있으면 이 분기만 단독 적용하지 않는다.'),
 'AAF':('공기유동 플랩·제어기 점검 메시지','겨울철 동결 또는 이물질을 확인한다. 동결에 따른 표시를 무조건 부품 고장으로 단정하지 않는다.'),
 'VESS':('가상 엔진 사운드 시스템 점검 메시지','정비 점검을 받는다.')
}

# Page assignments were recorded while reading each complete cluster section.
DOCS=[]
def doc(code,year,first,last,offset,mapping,overrides=None):
    DOCS.append((code,year,first,last,offset,mapping,overrides or {}))
doc('A01',2026,123,133,118,{
 'READY':123,'SERVICE':123,'POWER':124,'CHARGE_INDICATOR':124,'HV_LOW':124,'BELT':124,'SRS':124,'REGEN':125,'BRAKE':125,'ABS':125,'EBD':126,'EPS':126,'CHARGE12':126,'TPMS':[126,127],'EPB':127,'AUTO_HOLD':127,'FCA':127,'LKA':128,'LFA':128,'DAW':128,'MASTER':129,'ICE':129,'ESC':129,'KEY':130,'TURN':130,'LIGHTS':[130,131],'DOOR':[131,132],'KEY_MESSAGES':131,'START_MESSAGES':[131,132],'LAMP_MESSAGE':133},
 {'CHARGE12':{'reviewStatus':'SOURCE_AMBIGUITY','reviewNote':'전기차 문서가 드라이브벨트와 모터 과열을 언급한다. 제조사 정정/설명 확인 전 벨트 점검을 운전자 지시로 배포하지 않는다.'},'START_MESSAGES':{'modelSpecific':'P 또는 N 시동, 퓨즈 비상시동은 ACC에서 버튼10초. 브레이크 고장에 대한 운행 허가가 아니다.'},'BRAKE':{'modelSpecific':'제동 부족 시 페달을 강하게 밟고 EPB 스위치를 당겨 비상 제동. 파킹브레이크는 급격히 조작하지 않는다.'},'AUTO_HOLD':{'modelSpecific':'이상 색상=주황색'}})
doc('DN8',2026,91,103,84,{
 'BELT':91,'SRS':92,'BRAKE':92,'ABS':[92,93],'EBD':93,'EPS':93,'FUEL':93,'LPG_OVERFILL':93,'OIL':94,'MIL':94,'CHARGE12':94,'TPMS':95,'EPB':95,'AUTO_HOLD':95,'FCA':96,'LKA':96,'ISLA':96,'DAW':97,'MASTER':97,'LED':97,'ESC':98,'ISG':98,'KEY':98,'TURN':99,'LIGHTS':99,'LPI_WAIT':99,'DOOR':[100,102],'KEY_MESSAGES':[100,101,102],'START_MESSAGES':[100,101],'DRAIN':101,'DIGITAL_KEY':101,'WASHER':103,'OVERHEAT':103,'LAMP_MESSAGE':103,'BATTERY12_HOT':103},
 {'OIL':{'restartCriteria':'유압이 회복된 후 재시동해야 경고 및 출력제한이 해제된다고 명시.'},'BRAKE':{'modelSpecific':'제동 부족 시 강한 페달 조작, 엔진브레이크 감속, 파킹브레이크를 천천히 조작.'},'START_MESSAGES':{'modelSpecific':'P 또는 N 시동, 퓨즈 비상시동은 ACC에서10초.'},'AUTO_HOLD':{'modelSpecific':'이상 색상=노란색'},'BATTERY12_HOT':{'modelSpecific':'안전 정차를 요구하는 메시지.'}})
doc('DN8HEV',2026,113,128,104,{
 'READY':113,'SERVICE':113,'HEV_EV_MODE':113,'BELT':113,'SRS':114,'REGEN':114,'BRAKE':[114,115],'ABS':115,'EBD':115,'EPS':115,'FUEL':115,'OIL':116,'MIL':116,'CHARGE12':117,'TPMS':117,'EPB':118,'AUTO_HOLD':118,'FCA':118,'LKA':119,'ISLA':119,'DAW':120,'MASTER':120,'LED':121,'ESC':121,'KEY':121,'TURN':122,'LIGHTS':[122,123],'GREEN_ZONE':123,'DOOR':[123,126],'KEY_MESSAGES':[124,125],'START_MESSAGES':124,'DRAIN':125,'DIGITAL_KEY':125,'WASHER':127,'OVERHEAT':[117,127],'LAMP_MESSAGE':127,'VESS':127,'HEV_CHECK':[127,128],'STOP_TOW':128,'HEV_CHARGE_P':128,'COOLANT_LOW':128,'BRAKE_MESSAGE':128,'START_12V':128,'AAF':128,'BATTERY12_HOT':128},
 {'OIL':{'restartCriteria':'유압 회복 시 경고 소등 및 출력 제한 해제. 해당 문장은 재시동을 요구하지 않음.'},'START_MESSAGES':{'modelSpecific':'P에서 시동. 퓨즈 비상시동은 ACC에서10초.'},'BRAKE':{'modelSpecific':'제동 부족 시 강한 페달 조작, 엔진브레이크 감속, 파킹브레이크를 천천히 조작.'},'AUTO_HOLD':{'modelSpecific':'이상 색상=노란색'},'OVERHEAT':{'modelSpecific':'냉각수 수온 적색 경고는 적정 범위 초과. 정상 온도에서 소등.'},'BATTERY12_HOT':{'modelSpecific':'안전 정차를 요구하는 메시지.'}})
doc('DN8c',2025,80,93,74,{
 'BELT':80,'SRS':80,'BRAKE':81,'ABS':81,'EBD':81,'EPS':82,'FUEL':82,'LPG_OVERFILL':82,'OIL':82,'MIL':83,'CHARGE12':83,'TPMS':84,'EPB':84,'AUTO_HOLD':84,'FCA':85,'LKA':85,'LFA':86,'ISLA':86,'DAW':87,'MASTER':87,'LED':88,'ESC':88,'KEY':88,'TURN':89,'LIGHTS':[89,90],'LPI_WAIT':90,'DOOR':[90,92],'KEY_MESSAGES':[91,92],'START_MESSAGES':91,'DRAIN':92,'WASHER':93,'OVERHEAT':93,'LAMP_MESSAGE':93,'BATTERY12_HOT':93},
 {'OIL':{'restartCriteria':'유압 회복 후 재시동해야 경고/출력제한이 해제된다고 명시.'},'MIL':{'modelSpecific':'연료캡 분기는 가솔린 차량 조건. 택시 LPG에 그대로 대입하지 않는다.'},'START_MESSAGES':{'modelSpecific':'P 또는 N 시동. 퓨즈 비상시동은 ACC에서10초.'},'BRAKE':{'modelSpecific':'제동 부족 시 강한 페달 조작, 엔진브레이크 감속, 파킹브레이크를 천천히 조작.'},'AUTO_HOLD':{'modelSpecific':'이상 색상=노란색'},'BATTERY12_HOT':{'modelSpecific':'배터리 점검 메시지이며 이 문구 자체에는 안전정차 요구가 없음.'}})

def main():
    rules=[];documents=[]
    for code,year,first,last,offset,mapping,overrides in DOCS:
        d=next(x for x in MAN if x['modelCode']==code and x['year']==str(year))
        pages=json.loads((ROOT/d['textPagesPath']).read_text(encoding='utf-8'))
        ids=[]
        for topic,loc in mapping.items():
            nums=loc if isinstance(loc,list) else [loc]
            condition,action=TOPICS[topic]
            r={'ruleId':f'HY-CLUSTER-{code}-{year}-{topic}','documentIds':[f'HYUNDAI-{code}-{year}'],'topic':topic,'conditions':[condition],'orderedActions':[action],'driverProhibitions':[],'applicationConstraints':['다른 모델/연식/파워트레인으로 자동 전파하지 않는다.','연결된 정비 절차 검토가 필요한 작업은 이 클러스터 요약만으로 실행 절차를 생성하지 않는다.'],'restartCriteria':None,'requiredContext':['정확한 모델·연식·파워트레인 및 장착 사양','경고 이름·색상·점등 패턴·시동 경과·동시 메시지'],'reviewStatus':'SOURCE_REVIEWED','reviewMethod':'AI direct reading of complete cluster pages, individually assigned topics and paraphrased actions','sources':[{'url':d['sourceURL']+f'#page={nums[0]}','documentSha256':d['sha256'],'passageSha256':hashlib.sha256('\n'.join(pages[n-1] for n in nums).encode()).hexdigest(),'locator':{'pdfPages1Based':nums,'printedPageLabels':[f'4-{n-offset}' for n in nums]}}],'runtimeApproved':False,'expertApproved':False}
            r.update(overrides.get(topic,{}));rules.append(r);ids.append(r['ruleId'])
            if code=='DN8HEV' and topic=='OIL':
                r['restartCriteria']='정비 절 PDF485/9-13까지 확인한 결과 유압 회복 후 재시동 필요. 클러스터 단락의 생략을 재시동 불필요로 해석하지 않는다.'
                r['linkedProcedureRuleId']='HY-PROCEDURE-DN8HEV-2026-OIL'
                r['crossSectionReconciliation']='초기 클러스터 단락 요약을 연결 정비 절 근거로 보완함.'
        documents.append({'documentId':f'HYUNDAI-{code}-{year}','clusterPagesRead1Based':list(range(first,last+1)),'clusterReadMethod':'AI full text reading; review not inferred from presence of keyword','topicRuleIds':ids,'linkedProceduresReviewed':False,'allCountermeasuresReviewed':False,'runtimeApproved':False})
    OUT.write_text(json.dumps({'schemaVersion':1,'reviewer':'AI','runtimeApproved':False,'allCountermeasuresReviewed':False,'rules':rules,'documents':documents},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Cluster review rules',len(rules),'documents',len(documents))
if __name__=='__main__':main()
