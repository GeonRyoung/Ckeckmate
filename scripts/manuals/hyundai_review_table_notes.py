"""Human-authored AI reading log for all 426 deduplicated table rows.

Indexes are explicit assignments made after reading each complete extracted row;
they are not classifier output. Row hashes prevent silently applying assignments
to a changed extraction. Executable branch encoding and linked procedures remain separate.
"""
import json,re,hashlib
from pathlib import Path
from hyundai_review_cluster_notes import TOPICS,ROOT
RAW=ROOT/'.local/manual-review/2026-10-28/hyundai/table-row-candidates.json'
DATA=json.loads(RAW.read_text(encoding='utf-8'))
ROWS=DATA['uniqueRows']
assert len(ROWS)==426
GROUPS={
'KEY_MESSAGES':[7,8,9,18,19,21,83,84,85,92,97,137,138,145,146,151,153,154,156,204,205,211,213,214,216,217,275,276,278,295,299,333,334,335,372,373,375,404],
'START_MESSAGES':[10,11,12,13,14,15,16,86,87,88,89,90,91,139,147,148,149,150,206,207,208,209,210,273,274,296,297,298,336,337,338,339,423],
'DIGITAL_KEY':[17,94,95,96,152,155,215,225,277,377],
'DRAIN':[20,93,212,300,301,340,374,376],
'VESS':[22,98,226,279],
'BRAKE_MESSAGE':[23,99,157,227],
'STOP_TOW':[24,100,114,308,408,41],
'DOOR':[25,26,74,101,158,159,228,229,280],
'LOW_TIRE_MESSAGE':[29,104,140,162,230,283,341,380],
'LAMP_MESSAGE':[30,31,32,105,106,163,165,231,233,234,284,344,384,385],
'AAF':[33,107,387],
'BATTERY12_HOT':[34,166,235,304,312,313,386],
'HV_LOW':[35,36,50,108,109,171,236,237,240,285,286],
'EV_TOW':[37,110,141],
'POWER':[38,49,111,142,167,194,238,260,425],
'BATTERY_COLD':[39,112,168],
'BATTERY_HOT':[40,113],
'PLUG_REMOVE':[42,115],
'CHARGE_DOOR':[43,116],
'CHARGER_FAILURE':[44,117,143],
'CABLE_FAILURE':[45,118,144,169],
'SERVICE':[48,119,170,239,389],
'BELT':[51,120,172,241],
'SRS':[52,121,173,242,347],
'REGEN':[53,174,175,243,244,245,390],
'BRAKE':[54,122,176,246,315,348],
'ABS':[55,123,177,247,316,349],
'EBD':[56,178,248,317,350],
'EPS':[57,124,180,250],
'CHARGE12':[58,125,179,249,321,354,393],
'TPMS':[59,126,181,251,322,394],
'EPB':[60,127,182,252,324,357],
'FCA':[61,128,183,253,325,358,395],
'STEERING_SAFETY':[62,129,184,359,396],
'LKA':[63,130,185,254,326,360],
'DAW':[64,131,186,255],
'MASTER':[65,132,188,256,327,362],
'LED':[66,257,328,398],
'AWD':[67,133,363],
'ICE':[68,191,329,365,399],
'CHARGE_INDICATOR':[69,192,258],
'READY':[70,193,259],
'AUTO_HOLD':[71,195,261,330,366],
'LFA':[72,134,197,262,367],
'ISLA':[73,135,198,263],
'ESC':[75,200,264,402,403],
'ESC_OFF':[76,201,265],
'KEY':[77,202,266,331],
'TURN':[78,267],
'LIGHTS':[79,80,81,82,136,268,269,270,271,369,370,371],
'WASHER':[164,232,381],
'DMS':[187,361,397],
'IFS_FAULT':[189],
'DBC':[190,364],
'NORMAL_OTHER':[196,199,203,272,400,401],
'FINGERPRINT':[218,219,220,221,222,223,224],
'FUEL':[302,318,342,351,382],
'OVERHEAT':[303,311,343,383,411],
'HEV_CHECK':[305,306,307,405,406,407],
'HEV_CHARGE_P':[309,409],
'COOLANT_LOW':[310],
'OIL':[319,352,391],
'MIL':[320,353,392],
'IMMOBILIZER':[323,356],
'COOLANT_RED':[355],
'ISG':[368],
'START_12V':[412]
}
CUSTOM={
'LOW_TIRE_MESSAGE':('저압 메시지와 표시된 타이어 위치','해당 차량 TPMS 절에 따라 공기압을 보충한다. 저장 요구가 있는 차량은 모든 타이어 점검 후 지정 저장 절차를 따른다.'),
'EV_TOW':('전기차 시스템 점검 메시지','주행을 계속하지 않고 즉시 견인해 정비한다.'),
'BATTERY_COLD':('저온·저잔량 장시간 주차에 따른 출력제한 메시지','출발 전 충전한다. 주변 온도가 충분히 오른 뒤에도 지속되면 정비한다.'),
'BATTERY_HOT':('고전압 배터리 과열과 안전정차 메시지','안전 정차→시동 끄기→충분히 식히기 순서를 따른다. 충분히 기다려도 메시지가 남으면 즉시 견인 정비한다.'),
'PLUG_REMOVE':('충전 커넥터 연결 상태에서 시동','커넥터를 분리한 뒤 시동한다.'),
'CHARGE_DOOR':('충전 도어 열림','충전 도어를 완전히 닫는다.'),
'CHARGER_FAILURE':('충전기 고장·충전기 중단·케이블 손상에 따른 충전중단','충전기와 케이블을 확인한다. 정상 작동 확인된 완속 충전기 또는 정품 휴대용 충전기로 시도하고 재발하면 정비한다.'),
'CABLE_FAILURE':('커넥터 불완전 연결 또는 잠금해제 버튼 눌림에 따른 충전중단','분리 후 다시 연결하고 커넥터·인렛의 손상/이물질을 확인한다. 정상 작동 확인된 다른 충전기/정품 휴대용 충전기로도 재발하면 정비한다.'),
'STEERING_SAFETY':('주황색은 전방·측방 안전 해제/이상, 빨강 점멸은 개입; 초기3초 정상','관련 설정과 센서 가림을 확인하고 제거 후에도 지속되면 정비한다.'),
'AWD':('사륜구동 경고 지속 또는 자주 재발','사륜구동 점검을 받는다.'),
'ESC_OFF':('초기3초 후 소등; ESC OFF 버튼으로 해제 시 표시','기능 해제 상태를 확인한다. 작동 중 깜빡이는 ESC 표시와 혼동하지 않는다.'),
'DMS':('실내 카메라 가림 또는 운전자 모니터링 이상; 초기3초 정상','실내 카메라 이물질을 확인·제거하고 계속 경고하면 정비한다.'),
'IFS_FAULT':('지능형 헤드램프 초기3초 이후 경고 지속','일시적 통신·진동 장애는 다시 POWER ON하면 해소될 수 있다. 계속 켜지면 정비한다.'),
'DBC':('초록 고정 준비/초록 점멸 제어 작동/주황 이상; 초기3초 정상','주황색 이상 경고이면 정비한다. 정상 제어 점멸을 고장으로 처리하지 않는다.'),
'NORMAL_OTHER':('해당 기능의 정상 상태 표시','상태를 확인한다. 이 표시만으로 고장이나 정비 필요를 확정하지 않는다.'),
'FINGERPRINT':('등록·설정 여부와 인증 성공/실패/원격시동 유지 메시지','해당 메시지의 인증 제한시간과 재시도 시간을 따른다. 등록된 키/지문 인증이 완료되어 메시지가 사라진 후 주행한다.'),
'IMMOBILIZER':('리모컨 키 사양, ON에서 약30초 켜짐은 정상;5초 점멸은 고장 예상','5초 점멸 패턴은 즉시 이모빌라이저 점검을 받는다.'),
'COOLANT_RED':('냉각수 온도가 적정 범위를 넘으면 적색 경고','과열 메시지·응급조치와 함께 확인한다. 적정 온도로 돌아오면 소등되는 표시다.')
}
TOPICS={**TOPICS,**CUSTOM}
NOT_WARNING=[*range(0,7),27,28,46,47,102,103,160,161,281,282,*range(287,295),314,332,345,346,378,379,388,410,*range(413,423)]
# Explicit corrections/conditions discovered during direct reading, retained separately.
SPECIAL={
16:'퓨즈 비상시동은 OFF에서10초. 정상 시동/주행 허가가 아니라 퓨즈 단선으로 시동할 수 없는 분기이다.',
91:'퓨즈 비상시동은 ACC에서10초.',
210:'퓨즈 비상시동은 OFF에서10초.',
298:'퓨즈 비상시동은 ACC에서10초.',339:'퓨즈 비상시동은 ACC에서10초.',
12:'DRIVE READY로 전환한 후 P로 변속하고 전원을 끈다.',
88:'N 종료 시 ACC가 남음. ON→P→OFF 순서.',139:'N 종료 시 ACC가 남음. ON→P→OFF 순서.',273:'N 종료 시 ACC가 남음. ON→P→OFF 순서.',
148:'N 종료 시 POWER ON이 남음. DRIVE READY→P→OFF 순서.',207:'N 종료 시 POWER ON이 남음. DRIVE READY→P→OFF 순서.',
15:'운전석 도어 열린 POWER ON/DRIVE READY에서 P 외 변속. 브레이크를 밟고 P로 옮긴 후 시동을 끈다.',
150:'운전석 도어 열린 POWER ON/DRIVE READY에서 P 외 변속. 브레이크를 밟고 P로 옮긴다. 이 행은 시동 끄기까지 요구하지 않는다.',
35:'SOC20% 이하',36:'SOC10% 이하; 출력제한 동반',108:'SOC10% 이하',109:'SOC5% 이하; 출력제한 동반',236:'SOC20% 이하',237:'SOC10% 이하; 출력제한 동반',
285:'기본형25% 이하; 향속형·크로스·라운지20% 이하.',286:'기본형15% 이하; 향속형·크로스·라운지10% 이하. 출력제한 동반.',
251:'TPMS 초기 약4초, 이상은 약70초 점멸 후 고정. 실제 타이어 압력 확인·보충 후 이상 패턴이면 정비.',
71:'AUTO HOLD 이상 색상 노란색.',195:'AUTO HOLD 이상 색상 주황색.',261:'AUTO HOLD 이상 색상 주황색.',330:'AUTO HOLD 이상 색상 주황색.',366:'AUTO HOLD 이상 색상 주황색.',
205:'키를 센터 콘솔 오픈 트레이의 비상시동 음각 위치에 놓는다. 키 배터리를 교체한다. 키로 버튼 직접 누르기와 다름.',
373:'키를 해당 차량 비상 시동 위치에 둔 뒤 시동 버튼을 누른다.',404:'키를 해당 차량 비상 시동 위치에 둔 뒤 시동 버튼을 누른다.',
155:'최대30초 표시 중 패드에 등록 키를 올린다. 원격 스마트 주차 보조 작동 중/작동 후에는 디지털키로 주행 상태 전환 불가.',
215:'최대30초 표시 중 패드에 등록 키를 올린다. 원격 스마트 주차 보조 작동 중/작동 후에는 디지털키로 주행 상태 전환 불가.',
277:'최대30초 표시 중 패드에 등록 키를 올린다. 원격 스마트 주차 보조 작동 중/작동 후에는 디지털키로 주행 상태 전환 불가.',
218:'인증 성공 안내4초. 키 표시등 켜진 동안30초 안에 브레이크를 밟고 시동. 시간이 지나 표시등이 꺼지면 지문 재인증.',
219:'연속5회 이상 실패 시 안내4초. 화면 제한 시간이 지난 후 재시도. 스마트키 휴대/패드 위 등록 디지털키로 시동 가능.',
220:'프로필 지문시동 설정 및 앱 원격해제 조건. 최대30초 동안 주행 불가; 지문 인증 후 메시지 소멸 시 주행.30초 지나면 시동 꺼짐.',
221:'프로필 지문시동 설정 및 앱 원격해제 조건.30초 안에 패드의 디지털키 또는 지문 인증.30초 지나면 시동 꺼짐.',
222:'지문시동 후 미착용·운전석문 열림: 최대10초 안내. 등록된 사용자/키 없이 시동 끄면 재시동 어려움.',
223:'프로필 지문시동 설정 및 스마트키 미인식. 첫 안내4초+지문 요구6초, 키표시10초. 지문 인증하고 메시지 소멸 확인.',
224:'디지털키·지문 등록 및 프로필 설정 조건. 안내5초, 키표시10초. 등록 키 또는 지문 인증 후 시동.',
225:'디지털키 DRIVE READY 후 미착용·운전석문 열림: 최대10초 안내. 키 휴대 확인.',
313:'일반 배터리 점검과 다르게 안전 정차 후 주차브레이크 작동까지 요구한다.',
166:'12V 과온/과충전, 메시지가 즉시 안전 정차를 요구한다.',
319:'유압 회복 소등 설명 뒤 재시동해야 경고/제한 해제라는 단서가 함께 있다. 복구를 확인하기 전 재시동만으로 문제 해결로 처리하지 않는다.',
352:'유압 회복 소등 설명 뒤 재시동해야 경고/제한 해제라는 단서가 함께 있다.',391:'유압 회복 소등 설명 뒤 재시동해야 경고/제한 해제라는 단서가 함께 있다.',
368:'주황색 의미는 공회전 제한 미진입 상태다. 다른 문서의 노란색 시스템 이상과 같다고 추론하지 않는다.',
338:'제목은 P 또는 N이나 본문 원인·조치는 P만 명시. 모델 절차 확정 전 N 허용을 자동 안내하지 않는다.',
389:'HEV 문서에 서비스 경고 원인을 전기차 시스템으로 표현함. 적용 파워트레인을 BEV로 바꾸지 않는다.',
306:'메시지는 안전 정차이며 시동 끄기라는 문구는 없음; 문제 해결 전 약10초 경고음.',406:'메시지는 안전 정차이며 시동 끄기라는 문구는 없음; 문제 해결 전 약10초 경고음.',
307:'극저 SOC·시동 불가, 경고음1회. 시동을 걸지 말고 정비.',407:'극저 SOC·시동 불가, 경고음1회. 시동을 걸지 말고 정비.',
283:'모든 타이어 점검 후 공기압 저장을 요구하는 메시지. 압력 저장 세부 절차를 읽기 전 임의 리셋 금지.',
196:'아이 페달 사용 중 켜짐.',199:'고속도로 차로변경: 초록 가능/초록점멸 작동/회색 대기/흰색점멸 취소.',203:'지능형 헤드램프 흰색 준비·초록 작동, 대향/선행차 감지 시 상향 LED 부분 소등.',272:'배터리 컨디셔닝 작동 표시.',400:'EV 켜짐/꺼짐은 구동 모드이며 고장 신호 아님.',401:'내비게이션·ECO·환경보호 설정 조건에서 지정 구역 정상 표시.'
}

def main():
    assigned={};rules=[];coverage=[]
    for topic,inds in GROUPS.items():
        for i in inds:
            assert i not in assigned,i
            assigned[i]=topic
    for i,row in enumerate(ROWS):
        if i in NOT_WARNING:
            coverage.append({'rowTextSha256':row['rowTextSha256'],'status':'OUT_OF_SCOPE_NAVIGATION','reason':'설정/탐색 또는 일반 화면 모드이며 경고 대처가 아님','occurrences':row['occurrences']});continue
        if i==424:
            coverage.append({'rowTextSha256':row['rowTextSha256'],'status':'SOURCE_REVIEWED_CONTINUATION','reason':'CE1N PDF149–150 원문 및 CE1 대비 차이를 직접 확인: 방향지시등 점검 항목의 사양 적용 조건 이어짐. 독립 경고가 아님.','occurrences':row['occurrences']});continue
        assert i in assigned,('UNASSIGNED',i)
        topic=assigned[i];cond,act=TOPICS[topic]
        sources=[{'documentId':o['documentId'],'url':o['sourceURL'],'documentSha256':o['sourceSha256'],'locator':{'pdfPages1Based':sorted(set(o['pages']))},'rowTextSha256':row['rowTextSha256']} for o in row['occurrences']]
        rid='HY-TABLE-'+row['rowTextSha256'][:16]
        r={'ruleId':rid,'topic':topic,'documentIds':sorted(set(s['documentId'] for s in sources)),'conditions':[cond],'orderedActions':[act],'driverProhibitions':[],'applicationConstraints':['직접 읽은 표행의 요약이다. 연결된 정비 절차 및 세부 실행 분기 구조화 완료를 뜻하지 않는다.','공통 요약보다 modelSpecificConditions의 원문 차이 조건이 우선한다.'],'modelSpecificConditions':SPECIAL.get(i),'sources':sources,'reviewStatus':'SOURCE_REVIEWED','reviewMethod':'AI direct reading of all columns and continuation rows; exact normalized passage deduplication only','reviewer':'AI','runtimeApproved':False,'expertApproved':False,'structuredEncodingComplete':False}
        if i in [243,244]:r['pairedContinuationRows']=[243,244]
        if i in [402,403]:r['pairedContinuationRows']=[402,403]
        if i==387:
            r['reviewNote']='LX3 PDF135–136 이어짐 직접 확인: 겨울철 동결 시 AAF 고장이 아니어도 메시지가 표시될 수 있으므로 동결·이물질 확인.'
            for source in r['sources']:
                if source['documentId']=='HYUNDAI-LX3-2027':source['locator']['pdfPages1Based']=[135,136]
        if i==338:r['reviewStatus']='SOURCE_AMBIGUITY'
        if topic=='BRAKE_MESSAGE':r['orderedActions']=['제동 성능 저하·페달 이동량 증가 가능성을 고려하고 즉시 정비 점검을 받는다. 이 표행에는 별도의 견인 명령이 없다.']
        if topic=='EBD':r['orderedActions']=['고속 주행을 피하고 안전에 유의하여 정비 점검을 받는다.']
        if topic=='CHARGE12':r['orderedActions']=['12V 배터리 충전 상태와 충전 계통을 점검하고 지속되면 정비한다. 벨트 언급은 내연기관 해당 행에서만 적용한다.']
        if topic=='EPS':r['conditions']=['초기 약3초 정상 점등; 시동 때 표시가 없거나3초 이후 지속하면 이상 문맥']
        if topic=='HEV_CHECK':r['orderedActions']=['일반 점검 메시지는 정비한다. 안전정차 메시지는 정차하고 정비를 요청한다. 시동 금지 메시지는 시동을 시도하지 않고 정비를 요청한다.']
        rules.append(r);coverage.append({'rowTextSha256':row['rowTextSha256'],'status':r['reviewStatus'],'ruleId':rid,'occurrences':row['occurrences']})
    out={'schemaVersion':1,'reviewer':'AI','allCountermeasuresReviewed':False,'runtimeApproved':False,'extractionSha256':hashlib.sha256(RAW.read_bytes()).hexdigest(),'method':'426 unique rows read in full; rows with identical normalized full contents share review, while document/page associations are retained. No keyword-derived semantic approval.','rules':rules,'coverage':coverage}
    p=ROOT/'data/manual-review/2026-10-28/hyundai-pdf-table-review.json';p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print('rules',len(rules),'coverage',len(coverage))
if __name__=='__main__':main()
