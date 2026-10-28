"""Persist AI reading notes, not executable vehicle advice or automatic approval.

The 7 cluster texts, notification texts, TPMS and maintenance texts were read
directly. Repeated editions were compared to the GN7 baseline, including all
changed prose; the script only serializes those reading decisions.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/manual-review/2026-10-28'
INV = json.loads((OUT/'hyundai-inventory.json').read_text(encoding='utf8'))
CODES = ['NH2','GN7','GN7HEV','CN8','CN8KH','NX5','NX5KP']
ROWS = [r for r in INV['sections'] if r['documentId'].split('-')[1] in CODES]

def source(r, item=None):
    code = r['documentId'].split('-')[1]
    raw = ROOT/'.local/manual-corpus/2026-10-28/hyundai'/f'{code}-2027-web'
    path = raw/r['locator']['path']
    if not path.exists():
        path = raw/'data/searchData.json'
    if not path.exists():
        paths = list(raw.rglob('*search*json'))
        if not paths: raise FileNotFoundError(raw)
        path = paths[0]
    return {'URL':r['sourceURL'],'hash':hashlib.sha256(path.read_bytes()).hexdigest(),
            'sourceKind':'official_html' if path.suffix=='.html' else 'official_searchData_text',
            'sourceLocalPath':str(path.relative_to(ROOT)).replace('\\','/'),
            'locator':dict(r['locator'], item=item), 'passageHash':r['passageSha256']}

def make(r, key, topic, conditions, actions, prohibitions=None, restart=None, note=None):
    return {'ruleId':f'AUDIT-{r["id"]}-{key}', 'documentIds':[r['documentId']],
        'sources':[source(r,key)], 'topic':topic,'conditions':conditions,'orderedActions':actions,
        'prohibitions':prohibitions or [], 'restartCriteria':restart or [],
        'requiredContext':['정확한 모델·연식·파워트레인·장착 사양','시동/주행 상태','표시 색상·점멸 시간·동반 문구'],
        'reviewStatus':'SOURCE_REVIEWED','reviewMethod':'AI 원문 독해 및 동등 절 차이 대조',
        'reviewer':'AI','runtimeApproved':False,'executableRule':False,
        'structuredEncodingComplete':False, 'reviewNote':note or '원문 의미 검토 기록이며 모든 문장을 실행 규칙으로 변환한 결과가 아님.'}

# Brief paraphrases authored after reading the indicator paragraphs.
NOTES = {
 '안전벨트':('미착용·해제와 시동/속도 조건','바른 자세로 안전벨트를 착용한다. 좌석 물건·전자기기 영향도 확인한다.','경고음 시간은 좌석과 차종에 따라 달라 단일 상수로 통합하지 않는다.'),
 '에어백':('초기 약 3–6초 점등은 정상; 미점등 또는 지속은 이상','지정 정비소에서 점검한다.',''),
 '전동 파워':('초기 약 3초 이후 지속 또는 미점등','안전에 유의해 지정 정비소에서 점검한다.',''),
 '충전 경고':('12 V 충전 계통 이상 또는 부족; 고전압 SOC 경고와 별개','12 V 충전 상태와 해당 차량 충전 계통을 확인하고 지속하면 점검한다.','EV·HEV에 구동 벨트 점검을 임의 추가하지 않는다.'),
 'LPG 과충전':('LPI 차량의 빨간 LPG 과충전 표시','지정 정비소에서 점검한다.','수소 과충전과 혼동하지 않는다.'),
 '엔진 오일 압력':('주행 중 저유압 표시; 저유량과 연계될 수 있음','안전 정차 후 시동을 끈 상태의 오일 점검 절과 함께 확인한다. 부족량 보충 후에도 지속하면 점검한다.','경고 상태 계속 주행 금지. 정기 오일 점검의 예열 절차를 저유압 비상 상황에 기계적으로 적용하지 않는다.'),
 '냉각수 수온':('정상 범위 초과 시 빨강','과열 대처 절의 증기/누수/팬 상태에 따른 정지 조건을 따른다.','뜨거운 캡 개방 금지; 일괄 즉시 시동 끄기 또는 일괄 계속 공회전으로 단순화하지 않는다.'),
 'EBD':('ABS와 브레이크 경고가 동시에 표시','고속 주행을 피하고 제동 불안정에 유의해 점검한다.','ABS 단독 경고의 조건과 합치지 않는다.'),
 'ABS 경고':('초기 약 3초 이후 지속 또는 미점등','안전 정차 후 재시동하고 지속 또는 미점등이면 점검한다.',''),
 '회생 제동 경고':('회생 제동 이상; 브레이크 동반 또는 주황/노랑 경고','페달 깊이와 제동 거리 변화에 유의해 점검한다.','일반 회생 단계 표시를 고장으로 분류하지 않는다.'),
 '브레이크 경고':('주차브레이크 체결·액 부족·제동 이상을 구분','급제동을 피해 감속·정차한다. 제동이 약하면 페달을 더 강하게 밟고 부족 시 주차브레이크를 서서히 사용한다. 액량/제동계통을 점검한다.','주차브레이크 급조작 금지. 단순 해제 안내만으로 액 부족/제동 이상을 덮지 않는다.'),
 '4륜구동 경고':('경고가 지속되거나 빈번함','지정 정비소에서 점검한다.',''),
 '4륜구동 고정':('센서와 주행 모드에 따른 4륜 고정 모드 표시','정상 작동 표시와 별도의 4륜 고장 경고를 구분한다. 주행 중 고장 경고이면 즉시 점검한다.',''),
 'DBC':('녹색 대기·녹색 점멸 작동·주황 이상','주황 이상 상태는 지정 정비소에서 점검한다.',''),
 '연료 부족':('연료 잔량 부족; NH2는 수소','차량 연료 종류에 맞춰 즉시 보충한다.','연료 소진 상태의 계속 주행 금지.'),
 '저압 타이어':('저압 지속 점등과 약 1분 점멸 후 점등하는 TPMS 이상을 구분','공기압을 확인하고 차량 권장값으로 조절한다. 초기 미점등 또는 시스템 이상 패턴이면 점검한다.','TMK/실런트 허용은 차종별 TPMS 절을 함께 확인한다.'),
 '주차 브레이크':('EPB 초기 약 3초 이후 지속 또는 주행 중 발생','지정 정비소에서 점검한다.','주차브레이크 체결을 나타내는 기본 브레이크 표시와 혼동하지 않는다.'),
 '통합 경고':('운전자 보조 등 상세 이상 알림이 있음','알림 센터 또는 클러스터 유틸리티에서 원인을 확인한다. 해당 센서 이물질 조치 후 지속하면 점검한다.','통합 경고만으로 특정 부품 고장을 확정하지 않는다.'),
 'AUTO HOLD':('흰색 대기·녹색 유지·주황 이상','주황일 때 지정 정비소에서 점검한다.','정상 유지 표시를 고장으로 취급하지 않는다.'),
 '엔진 경고':('엔진 제어 이상; 저유압 보호 반복 또는 연료 캡 미잠금도 가능','신속히 점검하고 시동 불가이면 견인한다. 캡 미잠금이면 딸깍 잠근 뒤 지속 여부를 확인한다.','캡 문제로 단정하거나 지속/점멸 상태의 계속 주행을 권하지 않는다.'),
 '키 확인':('차내 키 존재 시 일시 점등; 인식 불가 시 점멸','키 존재·인식과 해당 메시지의 비상 시동 방법을 확인한다.',''),
 'LED 전조등':('램프 이상 점등 또는 관련 부품 이상 점멸','지정 정비소에서 점검한다.','계속 주행 시 램프 수명 저하 가능.'),
 '지능형 헤드램프 경고':('초기 3초 이후 지속; 일시 통신/진동 이상 가능','재시동 후에도 지속하면 점검한다.','일반 지능형 헤드램프 작동 표시와 구분한다.'),
 'ESC) 작동 정지':('운전자가 ESC를 끈 표시와 초기 자가 점검을 구분','설정 상태와 실제 고장 지속 여부를 확인한다.','원문에 꺼짐 상태와 지속 시 정비 문구가 병존하므로 모든 ESC OFF를 고장으로 자동 처리하지 않는다.'),
 'ESC) 작동 표시':('초기 3초·작동 중 점멸·고장 지속 점등','계속 켜진 이상은 점검한다.','정상 제어 점멸을 고장으로 처리하지 않는다.'),
 '전방 안전':('주황 미설정/이상; 빨간 점멸 안전 기능 작동','기능 설정과 관련 센서 가림을 확인하고 이물질 제거 후 지속하면 점검한다.','빨간 작동 점멸과 고장 지속 표시를 구분한다.'),
 '조향 안전':('전방/측방 안전 미설정·이상 또는 작동 표시','설정·관련 센서를 확인하고 가림 제거 후 지속하면 점검한다.',''),
 '차로 안전':('대기·가능·개입·꺼짐·이상 표시를 색/아이콘별 구분','차로 이탈방지 설정과 전방 카메라 가림을 확인한 뒤 지속 이상을 점검한다.','차종별 꺼짐 아이콘/주황 의미를 하나로 고정하지 않는다.'),
 '속도 제한':('주황은 꺼짐/카메라 가림/고장; 제한속도 빨강은 초과','전방 카메라 가림을 확인하고 지속 이상은 점검한다.','속도 초과 빨강을 시스템 고장으로 취급하지 않는다.'),
 '전방 주시':('실내 카메라 가림/시스템 이상; 일부 차종 점멸은 전방 주시 요구','도로를 주시하고 실내 카메라 가림을 제거한다. 지속 이상은 점검한다.','NH2 원문에는 같은 점멸 조건이 없으므로 GN7의 점멸 조건을 전이하지 않는다.'),
 '부주의 운전':('주황 점멸 경고·지속은 카메라 가림 또는 이상','전방 카메라를 확인하고 이물질 제거 후 지속하면 점검한다.',''),
 '도어 열림':('도어·트렁크/테일게이트 열림','주행 전과 차량을 떠나기 전 완전히 닫힌 상태를 확인한다.',''),
 '차로 유지':('녹색 작동·회색 대기·중단 점멸','상태 표시로 읽고 운전 책임을 유지한다.','중단 점멸 색은 GN7/NX5 회색, CN8/NH2 흰색 등 원문별 구분.'),
 '고속도로 차로':('대기·가능·작동·취소 상태','색상과 점멸 방향을 해당 차종 표시 체계로 읽는다.','일반 기능 상태를 고장으로 분류하지 않는다.'),
 '하이빔 보조':('흰색/회색 대기와 녹색 작동; NH2 지능형 헤드램프 포함','자동 상향 제어 작동 표시로 구분한다.','대기 색은 차종별로 다르다.'),
 '전조등 상향':('상향등 켜짐','맞은편 차량 시야를 방해하지 않게 조작한다.',''),
 '전조등 하향':('하향등 작동','정상 조명 작동 표시로 분류한다.',''),
 '미등 표시':('미등 작동','정상 조명 작동 표시로 분류한다.',''),
 '비상 경고등/방향':('방향 한쪽·비상 양쪽 점멸; 비정상 점멸 속도','비정상 속도이면 전구/접지/LED 관련 점검을 받는다.','정상 비상등을 고장 경고로 분류하지 않는다.'),
 '도로 결빙':('저온 시 결빙 가능성; CN8/CN8KH는 약 4℃ 이하 명시','노면 결빙 가능성을 알리는 환경 경고로 구분한다.','명시되지 않은 차종에 4℃ 임계값을 전이하지 않는다.'),
 '시동 대기':('LPI 시동 대기','표시가 꺼질 때까지 브레이크를 유지하면 자동 시동된다.',''),
 '주행 가능':('준비 완료 점등; 이상 시 소등/점멸','이상 소등/점멸이면 점검한다.',''),
 'EV 모드':('모터 주행·회생·엔진 정지 상태','정상 동력 모드 표시로 분류한다.',''),
 '대기 환경':('해당 구역·내비·ECO·기능 설정 조건','정상 환경 보호 모드 표시로 분류한다.',''),
 '서비스 경고':('HEV 또는 FCEV 제어계통 이상; 초기 약 3초 정상','주행 중 발생 또는 초기 지속이면 점검한다.','EV/HEV/FCEV 시스템을 같은 부품으로 단정하지 않는다.'),
 '수소 누출':('빨강 누출과 주황 감지 센서 이상','빨강 지속이면 안전 정차 후 견인 점검한다. 주황 지속이면 지정 정비소에서 점검한다.','주황 센서 이상을 누출 확정으로 말하지 않는다.'),
 '파워다운':('연료전지 스택 이상 등 출력 제한','속도·등판 제한에 유의하고 서비스 경고 동반 시 점검한다.','배터리 부족이라고 단정하지 않는다.'),
 '아이 페달':('아이 페달 작동','정상 기능 작동 표시로 분류한다.',''),
}

def cluster_rules(r):
    text = (ROOT/r['localPassagePath']).read_text(encoding='utf8')
    chunks = re.split(r'(?m)^\((\d+)\)\s*$',text)
    result=[]
    for i in range(1,len(chunks),2):
        num,body=chunks[i:i+2]
        lines=[x.strip() for x in body.splitlines() if re.search('[가-힣]',x)]
        if not lines: continue # icon legend, not prose paragraph
        title=lines[0]
        matched=next((v for k,v in NOTES.items() if k in title),None)
        if not matched: raise ValueError((r['id'],title))
        condition,action,prohibition=matched
        result.append(make(r,'indicator-'+num,title,[condition],[action],[prohibition] if prohibition else [],
             note='해당 번호 본문을 직접 읽고 기준 GN7 절과 차이 대조. 요약의 공통 문구가 차종별 원문 적용 조건을 대신하지 않음.'))
        result[-1]['itemPassageHash']=hashlib.sha256(body.encode()).hexdigest()
    return result

def main():
    rules=[]; coverage=[]
    for r in ROWS:
        t=r['title']; code=r['documentId'].split('-')[1]
        if r['characters']>5000 and t=='경고등 및 표시등 확인하기':
            rules.extend(cluster_rules(r)); status='SOURCE_REVIEWED'
        elif 'SAE 점도' in t:
            status='SOURCE_REVIEWED' # downloaded all 12 assets; 3 exact-byte images visually read
        elif t in ['엔진 과열','엔진 오일 점검하기','냉각수 점검하기','브레이크액 점검하기','구동 모터 냉각수 점검하기','연료 전지 냉각수 점검하기']:
            status='SOURCE_REVIEWED'
        elif r['characters']<300 and t in ['주행 정보와 경고등','경고등 및 표시등 확인하기','경고등 및 표시등','변속 위치 표시등','회생 제동 단계 표시등']:
            status='REVIEWED_CONTEXT_NO_COUNTERMEASURE'
        else: status='SOURCE_REVIEWED'
        coverage.append({'sectionId':r['id'],'documentId':r['documentId'],'title':t,'status':status,
            'source':source(r),'runtimeApproved':False,
            'scope':'인벤토리의 본문 텍스트 독해; 모든 연결 기능 제한 절의 재귀적 검토는 별도',
            'visualImageVerification':'SAE 점도' in t})
        if 'SAE 점도' in t:
            imgs=json.loads((ROOT/'.local/manual-review/2026-10-28/audit/sae/manifest.json').read_text(encoding='utf8'))
            coverage[-1]['imageSources']=[x for x in imgs if x['id']==r['id']]
            coverage[-1]['imageReading']='-30~50℃ 눈금 전폭의 점도 띠: CN8KH 0W-16, 나머지 0W-20. 점도만으로 전체 오일 품질 규격을 확정하지 않음.'

        if 'TPMS' in t:
            tmk=code in ['GN7','GN7HEV','NH2']
            rules.append(make(r,'tpms-procedure','저압·TPMS 이상·타이어 손상',
                ['저압 점등 또는 시스템 이상 점멸 후 점등','차체 불안정은 센서 경고가 없어도 조치'],
                ['감속하고 급조향을 피한다. 상태를 점검하고 차종의 권장 공기압으로 조절한다.',
                 '냉간 조건: 주행 종료 3시간 후 또는 주행 1.6 km 이내에서 조절한다.',
                 '시스템 이상은 즉시 점검한다. 센서 휠 교체 후에도 지속하면 정비한다.',
                 '주변 정비소가 없으면 해당 TMK 절차를 확인한다.' if tmk else '주변 정비소가 없으면 보험사 또는 가까운 정비 사업소에 연락한다.'],
                ['급격한 파손을 TPMS가 반드시 즉시 감지한다고 가정하지 않는다.','센서 임의 개조·변형 금지.',
                 '일반 방수제·부적합 실런트 사용 금지.' if tmk else '이 차종 TPMS 절은 타이어 실런트 사용을 금지한다. 타 차종 TMK 절차 전이 금지.']))
            if tmk:
                rules.append(make(r,'tmk','TMK 임시 수리와 중단 조건',
                    ['트레드의 작은 손상만 해당; 측면·심한 손상은 제외','차량에 맞는 유효기간 내 실런트·키트'],
                    ['안전한 평지에서 주차브레이크로 고정하고 원문 연결 순서에 따라 준비한다.',
                     '시동 상태에서 약 5–7분 주입 후 압력을 확인한다.',
                     '허용 압력 확보 후 20 km/h 이상으로 7–10 km 또는 약 10분 분포 주행하고 재점검한다.',
                     '80 km/h 이하로 200 km 이내 정비소를 방문한다.',
                     '진동·소음·거친 주행감 또는 적정 압력 유지 불가이면 정차 후 견인한다.'],
                    ['29 psi(200 kPa) 이하 주행 금지.','컴프레서 10분 이상 작동 금지.','-30℃ 이하 사용 금지.',
                     '4 mm 이상 손상·측면 손상에 사용 금지.','타이어의 못 등 이물질 임의 제거 금지.'],
                    note='절차와 후반 제한사항을 같은 검색 단위로 결합해야 한다. 숫자는 이 3개 문서에서 읽은 값이며 타 모델 전이 금지.'))
        elif t=='엔진 과열':
            rules.append(make(r,'overheat','과열 분기', ['과열 표시·노킹·출력 저하; 증기/누수와 팬 동작을 구분'],
                ['비상등, 안전 정차, P 및 주차 고정 후 에어컨을 끈다.',
                 '증기/냉각수 유출이면 시동을 끄고 서비스에 연락한다.',
                 '유출이 없으면 원문은 시동 상태 통풍 냉각을 안내한다. 수온이 내려가지 않으면 시동을 끄고 기다린다.',
                 '팬 미회전이면 시동을 끈다. 누수·팬·벨트 이상이면 운행을 중단한다.',
                 '충분히 식은 뒤 누수와 양을 확인하고 이상 없을 때 규격 냉각수를 조금씩 보충한다.'],
                ['뜨거운 라디에이터/히터 호스 캡 개방 금지.','회전 팬·벨트 접촉 금지.','뜨거운 엔진에 찬 냉각수 급주입 금지.'],
                note='마지막 팬 정지 전 시동 유지 주의문은 앞의 누수·증기·팬 고장 정지 조건과 함께 읽어야 한다. 재주행 허가는 이 요약에서 판정하지 않는다.'))
        elif t=='엔진 오일 점검하기':
            rules.append(make(r,'oil-level','오일 점검과 저유압 연결', ['정기 점검 및 오일 부족 확인'],
                ['평지에서 시동을 끈 후 약 15분 안정화하고 게이지를 닦아 재측정한다.','L 이하이면 F까지 보충한 뒤 재확인하고 캡/게이지를 닫는다.'],
                ['뜨거운 오일 화상·이물질·첨가제 유입을 피한다.','정기 점검 예열 지시를 이미 저유압인 비상 상황의 엔진 재가동 지시로 사용하지 않는다.'],
                ['유압 회복 뒤 재시동해야 보호 제한이 해제된다는 원문 조건; 오일 보충만으로 안전 재주행을 확정하지 않는다.']))
        elif t=='연료 전지 냉각수 점검하기':
            rules.append(make(r,'stack-coolant','연료전지 전용 냉각수', ['차가운 스택에서 MIN 근접 또는 감소'],
                ['지정 하이테크센터/블루핸즈에서 전용 사양 냉각수를 보충한다.'],
                ['비정비 인력의 압력 캡 개방 금지.','일반 냉각수·부동액 혼입 금지.','MIN 이하 지속 주행 금지.'],
                note='일반 냉각수 보충 RAG 답변을 적용하면 안 됨. 클러스터 과열 문구의 캡 주의와 이 전용 금지 절을 반드시 함께 검색한다.'))
        elif t=='구동 모터 냉각수 점검하기':
            rules.append(make(r,'motor-coolant','구동모터 냉각수', ['스택이 식은 상태의 F–L 수위'],
                ['필요한 보충은 지정 정비소에 의뢰한다.','충분히 식힌 뒤 상태와 누수를 확인한다.'],
                ['뜨거운 계통 캡 개방·부적합 냉각수 혼입·냉각수 없는 주행 금지.'],
                note='원문의 혼합비/수위 설명은 전문점 보충 지시를 취소하지 않는다.'))
        elif t=='냉각수 점검하기':
            rules.append(make(r,'coolant','냉각수 점검', ['엔진 충분히 냉각된 상태'],
                ['시동을 끄고 충분히 식힌다.','CN8은 F–L, 나머지는 MAX–MIN 표시를 확인하고 규격에 맞게 보충한다.','캡을 확실히 닫고 누수·현저한 감소 시 점검한다.'],
                ['뜨거운 캡 개방 금지.','경수·알코올/메탄올·부적합 혼합 사용 금지.','냉각수 없는 주행 금지.'],
                note='일부 문서의 35/60% 경계 문구가 표와 불일치하므로 경계값 자동 판정은 보류. 차종·엔진/전기장치 탱크 구분 필요.'))
        elif t=='브레이크액 점검하기':
            rules.append(make(r,'brake-fluid','브레이크액 보충 제한', ['MAX–MIN 범위; MIN 아래면 점검 대상'],
                ['MIN 아래이면 지정 정비소에서 점검한다.','보충 시 주위를 청결히 하고 규격액을 MAX까지만 넣은 뒤 캡을 잠근다.'],
                ['다른 오일 혼입·오래 노출된 액 사용·넘침 금지.','피부/눈·도장 접촉 주의.'],
                note='브레이크 경고를 액 보충만으로 해결되었다고 선언하지 않는다. NH2 용량표와 이 절의 DOT 규격 표기는 별도 확인 필요.'))

    # Message tables were read as complete source sections. Preserve nuanced
    # high-stakes branches without pretending all rows are executable mappings.
    for r in ROWS:
        if r['title'] not in ['알림 메시지 확인하기','클러스터 메시지 확인하기'] and not (r['title']=='경고등 및 표시등 확인하기' and 1500<r['characters']<2000): continue
        code=r['documentId'].split('-')[1]
        rules.append(make(r,'messages','메시지별 대응 검토', ['정확한 표시 문구와 동반 경고를 먼저 확인'],
            ['키·P단·브레이크·디지털 키·문 열림 메시지는 해당 조건 해소를 안내한다.',
             '시스템 점검 문구가 지속하면 지정 정비소에서 점검한다. 정차/견인/시동 금지 문구는 각각 별개 분기로 보존한다.'],
            ['모든 배터리 메시지를 충전 권고로 통합하지 않는다.','고전압·12 V·냉각수·제동 경고의 동일 단어만으로 차종 간 대응을 공유하지 않는다.'],
            note='전체 메시지 본문을 독해했으며 행별 실행형 추출은 아직 완료하지 않음. NH2 지문/원격시동 문구에 MY GENESIS가 혼입되어 해당 옵션 적용은 확인 보류.'))
        if code in ['GN7HEV','CN8KH','NX5KP']:
            rules.append(make(r,'hev-branches','하이브리드 고전압·전원·냉각수 분기',
                ['SOC 매우 낮음','시동 불가 및 시동 금지','전원 공급 장치 정차 요구','인버터/배터리 냉각수 부족'],
                ['단순 낮은 SOC 충전 요구는 안전 정차 후 P로 변속한다.','시동 금지 문구는 재시동을 권하지 않고 점검한다.',
                 '전원 공급 장치 정차 요구는 안전 정차 후 견인한다.','냉각수 부족은 주행을 중단하고 양을 확인하며 냉각수 안전 절과 연결한다.'],
                ['고전압 직접 수리·12 V 점프 시동으로 임의 전환 금지.','냉각수 부족 상태 장시간 주행 금지.']))
        if code=='NH2':
            rules.append(make(r,'hydrogen-branches','수소 관련 메시지 분기',
                ['빨간 누출·과충전·중대 연료전지/고전압 고장','미세 누출 가능성 또는 주황 센서 이상','수소 탱크 온도 이상'],
                ['빨간 누출·과충전·중대 고장은 안전 정차 후 견인 점검한다.','미세 누출 가능성과 주황 센서 이상은 점검하고 빨강 동반 시 정차·견인으로 강화한다.',
                 '탱크 온도 이상은 시동을 끄고 안정화하며 지속 시 견인한다.','과열 출력 제한은 운행 중단·시동 종료·냉각 및 즉시 점검; 전용 냉각수 캡은 정비 인력만 취급한다.',
                 '충전 중에는 완료까지 기다리고 시동하지 않는다.','충전 3,995회 이상 메시지는 수소 저장 시스템 교체 점검 대상이다.'],
                ['빨간 누출 상태 계속 주행 금지.','연료전지 냉각수 직접 캡 개방 금지.'],
                note='원문상 연료 완전 소진 시동 불가도 견인 점검 안내. 보조 배터리 저전압 정차 문구는 잠시 뒤 POWER ON 재확인 후 동일 시 견인으로 구별.'))

    payload={'version':1,'scope':'2027 Hyundai web 7 acquired inventory source-text review','reviewer':'AI',
        'runtimeApproved':False,'rules':rules,'limits':['전문가/제조사 승인 아님','전체 소유자 설명서의 모든 연결 절·이미지·옵션까지 완료한 것은 아님','메시지 행별 구조화·SDK 매핑 별도 필요']}
    (OUT/'hyundai-web-rules-audit.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf8')
    (OUT/'hyundai-web-coverage.json').write_text(json.dumps({'version':1,'runtimeApproved':False,'sections':coverage,
        'counts':{s:sum(r['status']==s for r in coverage) for s in sorted({r['status'] for r in coverage})},
        'denominator':'92 inventoried sections; indicator paragraphs counted separately; not 95 SDK types per vehicle'},ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'rules':len(rules),'sections':len(coverage)},ensure_ascii=False))

if __name__=='__main__': main()
