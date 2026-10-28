"""Serialize explicitly source-read review notes. No keyword-based approval."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/manual-review/2026-10-28'
MANIFEST=json.loads((ROOT/'data/manual-research/2026-10-28/hyundai-manifest.json').read_text(encoding='utf-8'))['documents']
RULES=[]

def rule(code,year,topic,pages,condition,actions,prohibitions=(),restart=None,context=(),visual=(),note=None):
    d=next(d for d in MANIFEST if d['modelCode']==code and d['year']==str(year))
    ps=json.loads((ROOT/d['textPagesPath']).read_text(encoding='utf-8'))
    offset={'QX':78,'HR':44,'HREV':104}.get(code)
    printed=[f"{ {'QX':'4','HR':'3','HREV':'4'}[code]}-{p-offset}" for p in pages] if offset and max(pages)<200 else ([str(p-4) for p in pages] if code=='NE1' and year==2025 else [])
    RULES.append({'ruleId':f'HY-{code}-{year}-{topic}-{len(RULES)+1:03}', 'documentIds':[f'HYUNDAI-{code}-{year}'],'topic':topic,'conditions':condition,'orderedActions':list(actions),'prohibitions':list(prohibitions),'restartCriteria':restart,'requiredContext':list(context),'sources':[{'url':d['sourceURL']+f'#page={pages[0]}','documentSha256':d['sha256'],'locator':{'pdfPages1Based':pages,'printedPageLabels':printed},'passageSha256':hashlib.sha256('\n'.join(ps[p-1] for p in pages).encode()).hexdigest()}],'reviewStatus':'SOURCE_REVIEWED','reviewMethod':'AI direct full-page text review'+(' and rendered-page visual confirmation' if visual else ''),'visualPages1Based':list(visual),'runtimeApproved':False,'expertApproved':False,'reviewScope':'Stated branch only; not certification of every procedure in the manual','reviewNote':note})

# All following branches were read directly; unlisted models are not inherited.
rule('QX',2027,'TPMS_LOW_PRESSURE',[89,331,332,333],['저압 표시가 켜지고 타이어 위치/저압이 표시됨'],['속도를 낮추고 급격한 코너링을 피한다.','정비소에 타이어 상태 점검을 의뢰하고 해당 차량의 권장 공기압에 맞춘다.','차가운 타이어에서 조절한다(원문 기준: 최근 3시간 동안 주행하지 않았거나 주행 거리가 1.6km 이내).'],['TPMS만 믿고 정기 공기압 점검을 생략하지 않는다.','저압 상태로 계속 운행하지 않는다.'],context=['경고 점등/시간 패턴','타이어 상태','차량 타이어 공기압 라벨'],visual=[89],note='추천 압력 수치는 타이어 규격별 제원에서 별도로 확인해야 한다. PDF331~333은 인쇄8-7~8-9.')
rule('QX',2027,'TPMS_MALFUNCTION',[89,333],['시동 때 표시되지 않거나 약70초 점멸 후 점등','저압 감지와 시스템 이상이 함께 생기면 위치표시가 사라질 수 있음'],['TPMS 점검을 즉시 의뢰한다.','저압 경보를 제공하지 못할 수 있으므로 실제 타이어 상태를 별도로 확인한다.'],['약1분이라는 다른 차종의 수치로 바꾸지 않는다.','센서/시스템을 임의 개조하지 않는다.'],context=['점멸 지속시간','시동 상태','저압 위치표시'],visual=[89])
rule('QX',2027,'BRAKE',[86,87],['주차브레이크 해제 후에도 경고 지속 또는 주행 중 점등'],['급제동을 피하고 서서히 안전한 장소로 정차한다.','제동이 부족하면 페달을 평소보다 강하게 밟고 엔진브레이크로 감속하며 주차브레이크를 천천히 조작한다.','브레이크액 부족 여부를 확인하고 보충 후에도 지속되면 점검을 받는다.'],['주차브레이크를 급격히 당기지 않는다.','브레이크액이 부족한 상태로 그대로 주행하지 않는다.'],context=['주차브레이크 체결 여부','실제 제동력','브레이크액량'])
rule('QX',2027,'ABS',[87],['시동ON 약3초 이후에도 점등 또는 주행 중 켜짐'],['안전한 곳에 정차하고 엔진을 끈다.','다시 시동을 걸어 초기 점등 후 약3초 내 소등 여부를 확인한다.','소등되지 않거나 주행 중 다시 켜지면 점검·정비를 받는다.'],restart='원문은 안전 정차 후 재시동 확인을 안내한다. 재점등/지속 시 점검하며 운행 안전 보장으로 확대하지 않는다.',context=['시동 단계','동시 브레이크 경고'])
rule('QX',2027,'EBD',[87],['ABS와 브레이크 경고가 현재 동시에 켜짐'],['고속 주행과 급제동을 피하고 가까운 서비스센터에서 즉시 점검한다.'],['서로 다른 시각의 이력 두 개를 동시점등으로 취급하지 않는다.'],context=['현재 동시 경고 목록'])
rule('QX',2027,'ENGINE_OIL_PRESSURE',[88],['주행 중 엔진오일 압력 경고'],['안전한 도로 옆에 정차한다.','오일량을 점검해 부족하면 보충하고, 보충 후에도 경고가 남으면 정비를 받는다.'],['경고가 켜진 상태로 계속 주행하지 않는다.'],restart='이 클러스터 절은 유압 회복 시 경고 소등·출력제한 해제를 설명한다. 다른 엔진의 재시동 조건을 임의로 추가하지 않는다.',context=['오일 압력 경고','실제 오일량','엔진 사양'],note='실제 오일량 점검/보충 절의 엔진 정지·대기 절차를 함께 검토하기 전 정비 실행 절차로 배포하지 않는다.')
rule('QX',2027,'ENGINE_MIL',[88,89],['시동 초기 약3초 후 지속점등 또는 점멸'],['가능한 빨리 엔진/연료/배기제어 계통 점검을 받는다.','주유캡이 완전히 잠기지 않은 경우 캡을 다시 잠그고 경고가 지속되면 점검한다.','시동이 걸리지 않는 경우 견인한다.'],['단순 캡 문제라고 확정하지 않는다.','점등·점멸 상태로 지속 운행하지 않는다.'],context=['시동 가능 여부','주유캡 상태','경고 지속'])
rule('QX',2027,'CHARGING_12V',[89],['충전경고 점등'],['배터리 충전 상태와 드라이브벨트/충전계통을 점검한다.','경고가 남으면 정비를 받는다.'],['고전압 배터리 충전 안내와 혼동하지 않는다.'],context=['내연기관 충전경고'],visual=[89])
rule('QX',2027,'ESC',[91],['점멸은 제어 작동','계속 켜지거나 주행 중 고정점등은 점검 문맥','ESC OFF는 사용자 해제 표시'],['제어 작동 점멸과 이상 지속점등을 구분한다.','지속점등이면 정비를 받는다.'],['ESC OFF를 동일한 고장 신호로 합치지 않는다.'],context=['ESC와 ESC OFF 구분','시동 초기 여부','동작 패턴'])
rule('QX',2027,'ADAS_FCA_LKA',[90],['FCA 주황=해제/이상, 빨강점멸=개입','LKA 회색대기/초록가능·점멸개입/주황해제·이상'],['해당 안전 기능 설정을 확인한다.','센서 앞 이물질을 제거한 후에도 이상 경고가 지속되면 정비를 받는다.'],['색상 없이 고장과 개입을 확정하지 않는다.'],context=['색상','기능 설정','센서 가림'])
rule('QX',2027,'ENGINE_OVERHEAT',[96],['과열 메시지; 원문 기준 냉각수온120±5℃ 이상'],['운전을 중지하고 서비스센터에 문의한다.'],['일반 점검 예약만 안내하며 계속 주행을 허용하지 않는다.'],context=['정확한 과열 메시지'],note='냉각수 보충 절은 뜨거운 냉각계통 접근 금지 등 별도 절차 검토가 필요하다.')
rule('HR',2026,'OIL_RECOVERY_LPG',[119],['엔진오일 압력 경고','2.5 T-LPDI 엔진 사양'],['안전한 곳에 정차해 오일량을 점검하고 부족분을 보충한다.','보충 후에도 경고가 남으면 정비를 받는다.'],['경고 상태로 계속 운행하지 않는다.','유압 회복이 확인되지 않은 상태에서 재시동으로 경고만 지우려 하지 않는다.'],restart='2.5 T-LPDI는 유압 회복 후 재시동해야 경고와 출력제한이 해제된다고 명시한다.',context=['정확한 엔진 사양','오일량/유압 회복'],visual=[119])
rule('HR',2026,'BRAKE_ABS',[117,118],['주차브레이크 해제 후 경고 지속/주행 중 경고','ABS 초기3초후지속 또는 주행중점등'],['브레이크 경고 주행 중이면 안전 정차한다.','제동이 부족하면 페달을 강하게 밟고 엔진브레이크와 천천히 조작한 주차브레이크로 감속한다.','ABS 단독이면 안전 정차·엔진정지 후 재시동 점검, 지속/재발하면 정비한다.'],['브레이크액 부족 상태로 계속 주행하지 않는다.','주차브레이크를 급격히 조작하지 않는다.'],context=['주차브레이크','제동력','ABS 단독 여부'])
rule('HR',2026,'TPMS',[120],['약1분 점멸 후 점등=시스템 이상 문맥','현저한 저압=저압 경고'],['시스템 이상 패턴이면 정비를 받는다.','저압은 실제 압력을 점검해 적정 압력을 유지한다.'],['베뉴의70초 또는 다른 차종 수치를 대입하지 않는다.'],context=['시간 패턴','타이어 상태'],note='타이어 비상조치 절262~264 직접 검토 전 종합 TPMS 절차 승인 불가.')
rule('HR',2026,'WAIT_START',[122],['시동 대기 표시등; 연료 압력 형성'],['표시등이 꺼진 뒤2~3초 이내에 시동을 건다.'],['디젤 예열등으로 자동 분류하지 않는다.'],context=['연료/엔진 사양','시동 대기 표시등'])
rule('HR',2026,'4WD_PTO_DOOR',[124],['4H/4L 작동 표시, PTO 작동 표시, 도어열림'],['4WD 변환 레버를2H/4H/4L 정위치에 놓는다.','도어가 완전히 닫혔는지 확인한 후 출발한다.'],['4H-4L 중간 위치를 정상 주행단으로 취급하지 않는다.','PTO 켜짐을 고장으로 확정하지 않는다.'],context=['장착 사양','4WD 레버 위치','PTO 상태'])
rule('HREV',2026,'POWER_DOWN',[111,118],['배터리 약7% 이하/저전압/고저온/냉각계통 이상/주행에 문제되는 고장 중 하나 가능'],['급가속·급출발을 피한다.','잔량 부족이면 즉시 충전한다.','경사로에서 밀리거나 오르기 어려울 수 있음을 고려한다.'],['다른 EV 문서의 단독 파워다운은 고장아님 문구를 이 모델에 대입하지 않는다.'],context=['배터리 잔량','온도','추가 메시지'],visual=[111])
rule('HREV',2026,'HV_BATTERY_LOW',[111],['배터리 잔량 약16% 이하 경고'],['즉시 충전한다.'],['예상30~40km를 보장거리로 제시하지 않는다.'],context=['배터리 잔량'],visual=[111])
rule('HREV',2026,'CHARGING_12V',[114],['보조배터리 충전 경고 주행 중 점등'],['안전한 곳으로 이동해 시동을 끄고 다시 걸어 소등을 확인한다.','계속 켜지면 즉시 점검을 받고, 바로 꺼져도 지정 정비소에서 점검한다.'],['소등만으로 점검을 생략하지 않는다.'],restart='안전 정차 후 재시동 확인; 소등되어도 점검 의무 문구 보존.',context=['12V 보조배터리 경고','주행/시동 상태'])
rule('HREV',2026,'BATTERY_OVERHEAT',[119],['배터리 과열 위험 안전정차 메시지'],['시동을 끄고 충분히 정차하여 배터리가 식도록 한다.','충분히 기다린 후에도 메시지가 남으면 운전을 삼가고 즉시 점검·정비를 받는다.'],['즉시 재시동으로 계속 운행하지 않는다.'],context=['정확한 과열 메시지'])
rule('HREV',2026,'STOP_TOW',[119,120],['전원 공급장치 점검 안전정차 또는 브레이크 시스템 점검 안전정차 메시지'],['안전한 곳에 정차한다.','견인하여 정비를 받는다.'],['일반 서비스 경고와 동일하게 계속 운행 가능한 것으로 표현하지 않는다.'],context=['메시지 전문'])
rule('HREV',2026,'COOLANT_LOW',[120],['냉각수 보충 메시지'],['주행을 중지하고 냉각수량을 확인한다.'],['냉각수 부족 상태로 장시간 주행하지 않는다.','뜨거운 냉각계통 보충절차를 임의 안내하지 않는다.'],context=['냉각수 메시지','냉각계통 온도'],note='이 기록은 클러스터의 정지·확인 지시만 검토했다. 보충 작업 절차는 별도 검토 대상.')
rule('NE1',2025,'TPMS',[138],['저압 점등 또는 약1분 점멸 후 점등/시동시표시없음'],['실제 공기압을 확인하고 필요하면 보충한다.','고장 패턴이 남으면 정비를 받는다.'],['한 번의 BLINK만으로1분 패턴을 확정하지 않는다.'],context=['패턴 지속시간','시동 상태','타이어 압력'],visual=[138],note='클러스터 분기 검토; 자세한 타이어 비상조치와 압력 규격은 별도 검토 대상.')
rule('NE1',2025,'POWER_DOWN',[136,145,146],['충전량/전압/온도 보호에 따른 단독 표시','서비스 경고 동시 표시 분기'],['잔량이 낮으면 충전한다.','급가속·급출발을 피한다.','서비스 경고가 함께 표시되면 정비 점검을 받는다.'],['파워다운 단독만으로 배터리 고장을 확정하지 않는다.','출력제한 중 경사로 주행가능을 보장하지 않는다.'],context=['동시 서비스 경고','충전량','온도','메시지 전문'])
rule('NE1',2025,'STOP_TOW',[144,145,146],['브레이크 시스템 점검 안전정차/전기차 시스템 점검/전원 공급장치 점검 안전정차 메시지'],['안전한 곳에 정차한다.','서비스센터로 견인하여 점검·정비한다.'],['경고가 표시된 상태로 계속 주행하지 않는다.'],context=['정확한 메시지 전문'],note='같은 아이콘이어도 일반 서비스 점등과 정차·견인 메시지는 다른 분기다.')
rule('NE1',2025,'BATTERY_OVERHEAT',[146],['고전압 배터리 과열 위험 안전정차 메시지'],['안전한 곳에 정차한 뒤 시동을 끈다.','배터리가 식도록 기다린다.','충분히 기다려도 메시지가 남으면 즉시 견인해 점검한다.'],['정지/냉각 대기 단계를 빼지 않는다.'],context=['과열 메시지','정차 후 메시지 지속'])
rule('NE1',2025,'BATTERY_LOW_THRESHOLDS',[145],['배터리 부족 메시지10% 이하','배터리 부족 파워제한 메시지5% 이하'],['즉시 충전한다.'],['포터EV16%/7% 임계값을 대입하지 않는다.'],context=['메시지 전문','배터리 잔량'])
rule('NE1',2025,'EBD_EPS_EPB',[138],['ABS+브레이크 동시점등','EPS 초기3초후지속/시동시표시없음','EPB 초기3초후지속/주행중점등'],['EBD 동시점등 때 고속주행을 피하고 안전에 유의해 정비를 받는다.','EPS/EPB 이상 점등 때 정비를 받는다.'],['서로 다른 시각의 이력을 동시 경고로 합치지 않는다.'],context=['경고 종류','현재 동시점등','시동 경과'],visual=[138])

# Explicit editorial constraints are not instructions addressed to the driver.
APP_ONLY = {
('QX','TPMS_MALFUNCTION'):[0], ('QX','EBD'):[0], ('QX','CHARGING_12V'):[0],
('QX','ESC'):[0], ('QX','ADAS_FCA_LKA'):[0], ('QX','ENGINE_OVERHEAT'):[0],
('HR','TPMS'):[0], ('HR','WAIT_START'):[0], ('HR','4WD_PTO_DOOR'):[0,1],
('HREV','POWER_DOWN'):[0], ('HREV','HV_BATTERY_LOW'):[0], ('HREV','STOP_TOW'):[0],
('HREV','COOLANT_LOW'):[1], ('NE1','TPMS'):[0], ('NE1','POWER_DOWN'):[0,1],
('NE1','BATTERY_OVERHEAT'):[0], ('NE1','BATTERY_LOW_THRESHOLDS'):[0], ('NE1','EBD_EPS_EPB'):[0]
}
for r in RULES:
    code=r['documentIds'][0].split('-')[1]
    indices=APP_ONLY.get((code,r['topic']),[])
    r['applicationConstraints']=[v for i,v in enumerate(r['prohibitions']) if i in indices]
    r['driverProhibitions']=[v for i,v in enumerate(r['prohibitions']) if i not in indices]
    del r['prohibitions']
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'hyundai-pdf-reviewed-rules.json').write_text(json.dumps({'version':1,'reviewer':'AI','reviewedOn':'2026-10-28','allCountermeasuresReviewed':False,'runtimeApproved':False,'rules':RULES},ensure_ascii=False,indent=2),encoding='utf-8')
print('Explicitly reviewed rules:',len(RULES))
