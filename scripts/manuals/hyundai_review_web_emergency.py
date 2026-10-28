"""Persist completed direct reading, preserving exact source associations."""
import json, hashlib
from pathlib import Path
from collections import Counter
B=Path(__file__).resolve().parents[2]
R=B/'.local/manual-review/2026-10-28/audit/hyundai-web-closure'
inv=json.loads((R/'inventory.json').read_text('utf-8'))
units=json.loads((R/'units.json').read_text('utf-8'))
assignment=json.loads((R/'assignment.json').read_text('utf-8'))
ids=set(assignment['emergencyUnitIds'])
assert len(ids)==836
notes=[
 ('비상 제동','일반 제동 고장의 비상시에만 EPB를 계속 당겨 제동하고 놓으면 중단. 정차 후 체결, 제동거리 증가·경고음, 재조작/재시동 후 경고 지속·탄 냄새/소음은 점검 조건 확인.'),
 ('주차 브레이크','체결 확인·시동 및 페달 조건의 해제, 자동 해제의 벨트/문/후드/트렁크 또는 테일게이트/변속 조건, 반복 조작 후 일시 경고와 지속 고장·ESC 동반 경고를 구분. 체결 중 운행 금지, 저전압 지원 및 해제 불가 시 정비/견인 조건 확인.'),
 ('Auto Hold','흰색 대기/초록 작동/주황 고장과 해제 경고를 구분. 해제 경고 시 직접 브레이크를 밟아 유지. 자동 EPB 전환·문/벨트 인식·급경사/장시간 조건 및 세차/주차 해제 주의 확인.'),
 ('ESC','시동 자기점검·정상 개입 점멸·지속 고장을 구분. 작동 점멸 시 감속·가속 금지, 기능 해제 금지. 차종별 정차 후 화면 설정/버튼 조작 및 OFF/SPORT 제한 상태와 고장을 혼동하지 않음.'),
 ('비상 시동','12V 전원·극성 및 지정 충전 단자/차체 접지 순서, 역순 분리·화염/동결/전해액 부족 위험 확인. FCEV/HEV 리셋 시간과 충전 유지·타차 지원 금지는 차종별로 분리.'),
 ('12 V 배터리 비상','제목형 부모 절. 해당 문서의 비상 시동 본문을 연결해 읽었으며 제목만으로 절차를 생성하지 않음.'),
 ('시동 켜기','스마트 키/디지털 키 방식별 인증 위치, 브레이크·시동 버튼 순서와 인증 실패 재시도 조건, 무인 어린이 방치 금지 확인.'),
 ('시동이 켜지지','P 및 배터리 상태 확인 후 비상 시동 절 연결, 지속 실패 시 긴급 지원. 일반 비상 재시동을 침수·과열·유압 경고 재시동 허가로 전이하지 않음.'),
 ('모터','P 또는 P/N·연료/배터리 확인을 원문별 구분하고 지속 실패 시 긴급 지원. 부모 절과 실제 하위 절을 구분.'),
 ('견인','상차/구동륜 들기/돌리 및 구동방식 조건, 짧은 상차 준비 이동과 후크 견인을 구분. N 유지·EPB 해제·시동 상태, 후크 체결/로프/탑승자·누유·속도/거리·급출발 금지 등 해당 절 조건을 확인.'),
 ('건널목','시동 정지 시 차량 이동 가능 여부에 따른 안전 이동/대피·신고·열차 연락 분기를 읽음. N 유지 절을 연결했으며 모든 차종에 단일 이동 방법으로 병합하지 않음.'),
 ('타이어가','비상등·핸들 유지·엔진 또는 회생 제동으로 감속, 평지 정차·EPB·대각 바퀴 고임목 후 TMK 연결 조건을 확인.'),
 ('시동이 꺼진','안전한 곳 이동과 제동/조향 보조 감소에 따른 힘 증가를 확인. 주행 중 P 변속 금지와 비상 시동 조건은 별도 연결 절에 귀속.'),
 ('제동력이','제동 저하 상태 지속 운행 금지, 페달·차종별 엔진/EPB 비상 제동으로 안전 정차 후 서비스 연락.'),
 ('표지판','후방 통행 차량에 주의하며 식별 가능한 곳에 안전삼각대 설치. 위험한 차도에 머무르도록 안내하지 않음. 보관/조립은 문맥으로 읽음.'),
 ('수소 가스','안전밸브 근처 온도110도 초과 시 긴급 배출·소음, 차량 앞 또는 옆 방향으로 멀리 대피하고 서비스 연락. 뒤쪽 배출 방향으로 접근 금지 문맥 확인.'),
 ('침수','즉시 시동을 끄고 다시 켜지 않으며 안전 대피 후 전문 견인/정비 요청.'),
 ('LPI','승객 대피·LPG 연료 취출 밸브 차단과 적합 소화기의 원문 분기를 읽음. 대응 불가 시 접근 통제·신고이며 연료/사양 미확인 상태 자동 안내 보류.'),
 ('화재','안전 정차·시동 정지·대피·신고 및 접근 통제. FCEV는 수소/고전압·감전/재발화 조건을 별도 보존. 안전한 초기 진화 가능 여부와 불가능 시 대피를 구분.'),
 ('사고','비상등·안전 정차·대피와 지원 요청. 연료 누유/수소·고전압 위험은 해당 동력계에만 적용.'),
 ('주행 중 고장','도로변 안전 정차·비상등·후방 경고·탑승자 대피와 서비스 요청. 터널 정차 위험 및 직접 작업 시 통행 차량 주의 확인.'),
 ('비상 상황 경고','비상 경고등 사용·방전 주의와 작동 중 방향지시등 제한을 확인.'),
 ('폭설','응급장에 포함된 일반 폭설/기상 방송 표를 문맥으로 읽음. 경고등 고장 복구의 실행형 규칙으로 채택하지 않음.'),
]
def note(title):
 for token,txt in notes:
  if token in title:return txt
 return '제목/상위 문맥 절을 읽고 같은 문서의 구체 하위 대응 절과 연결. 제목만으로 운전자 행동을 생성하지 않음.'
entries=[]
for idx,e in enumerate(inv):
 if e['scope'] not in ('emergency-required-reference','brake-or-key-required-reference'):continue
 row={k:v for k,v in e.items() if k not in ('lines','reviewStatus')}
 row.update(reviewStatus='SOURCE_REVIEWED',reviewer='AI',runtimeApproved=False,expertApproved=False,structuredEncodingComplete=False,reviewNoteKo=note(e['title']),uniqueUnitIds=[u['id'] for u in units if u['id'] in ids and idx in u['entries']],sourceReadingMethod='Read all 836 newly distinct source text units; exact identical prior-reviewed units inherited from hyundai-web-coverage.json; original order rechecked for jump/towing/high-risk branching. Official searchData text, not a claim of HTML visual reading.',textSha256=hashlib.sha256('\n'.join(e['lines']).encode()).hexdigest())
 entries.append(row)
assert len(entries)==200
extra=json.loads((R/'emergency-extra.json').read_text('utf-8'))
read_indices=[0,1,3,4,8,9,11,12,15,16,19,20,23,24,27,28,29,30,31,32,33,34,35,37]
extra_rows=[]
for i in read_indices:
 e=extra[i];row={k:v for k,v in e.items() if k!='lines'};row['sectionId']=e['documentId']+'-'+e['topicId'];row.update(reviewStatus='SOURCE_REVIEWED',runtimeApproved=False,expertApproved=False,structuredEncodingComplete=False,scope='mandatory-emergency-start-or-N-retention-reference',textSha256=hashlib.sha256('\n'.join(e['lines']).encode()).hexdigest())
 if '비상 키' in e['title']:row['reviewNoteKo']='방전 시 운전석 비상키·커버/핸들 사용과 회전 방향, 무리한 힘 금지를 확인. NH2/GN7/NX5는 우회전 해제, CN8/CN8KH는 좌회전 해제로 모델별 방향을 구분. 잠금 장치 회전 방향도 차종별 상이.'
 elif '시동이 걸리지' in e['title']:row['reviewNoteKo']='P 확인·스마트키 방전/전파간섭 인증·제동스위치 퓨즈 단선 시 비상 시동을 구분. NH2는 트레이 인증 및 OFF+브레이크10초, GN7 계열 OFF 퓨즈 분기, CN8/NX5 계열 ACC10초+안전상 브레이크 조건 보존. 움직이는 중 P 변속·가속하며 시동 금지.'
 elif i==35:row['reviewNoteKo']='NH2 시동 OFF/POWER ON/READY와 N 시 12V 방전 위험, 비상 시동 끄기2초 또는3회, 움직이는 상태 N 재시동 조건을 읽음. 일반 정차·견인과 비상 주행 분기를 혼합하지 않음.'
 else:row['reviewNoteKo']='N 주차·ACC 유지·방전 시 N 전환 및 자동 P 복귀를 읽음. EPB/Auto Hold 해제·평지·OFF 후3분·운전석 도어 개방 조건과 SBW/SBC 사양 차이 보존. NH2 READY+OFF후다이얼1초, CN8 레버형 기계 해제와 전자식 점프 방식, NX5KP 리셋 대체를 구분. 일부 전자식 P 버튼 비상제동은 명시된 사양에만 귀속.'
 extra_rows.append(row)
diffs=[
 dict(documents=['HYUNDAI-NH2-2027'],finding='리셋 후15초 이내 시동·READY 약30분. 후크 견인은10m/5km/h와 감속기 누유 없음 조건, POWER ON 유지.',sectionIds=[inv[60]['sectionId'],inv[66]['sectionId']]),
 dict(documents=['HYUNDAI-GN7HEV-2027','HYUNDAI-CN8KH-2027','HYUNDAI-NX5KP-2027'],finding='리셋 후30초 이내 시동·READY30분. GN7HEV/CN8KH는 실외 트렁크, NX5KP는 테일게이트 버튼으로 보호 해제. 점프 접지 지점은 개별 그림/본문 확인.',sectionIds=[inv[i]['sectionId'] for i in [198,324,457]]),
 dict(documents=['HYUNDAI-CN8-2027','HYUNDAI-CN8KH-2027'],finding='SBC/SBW 분기에 따라 N 전환·Auto Hold의 R단 미작동·문 열림 자동 P 조건이 다름. 현대 전체 공통 버튼 절차로 병합 금지.',sectionIds=[extra[i]['documentId']+'-'+extra[i]['topicId'] for i in [29,30,31,32]]),
]
holds=[dict(documentId='HYUNDAI-CN8KH-2027',sectionId=inv[331]['sectionId'],type='SOURCE_APPLICABILITY_AMBIGUITY',finding='차량 변속기 본문은 더블 클러치인데 후크 견인 절에 IVT1.5km/15km/h가 인쇄됨. 원문을 읽었으나 이 수치를 DCT 허가로 전이하지 않음.',runtimeApproved=False),dict(documentId='HYUNDAI-NH2-2027',sectionId=inv[60]['sectionId'],type='SOURCE_WORDING_ANOMALY',finding='FCEV 비상 시동 절 후반에 하이브리드 차량 표현이 있음. FCEV 리셋/충전 조건은 앞의 명시 본문으로 귀속하고 HEV 전이 금지.',runtimeApproved=False)]
visual=json.loads((R/'visual/sources.json').read_text('utf-8'))
for v in visual:v.update(reviewStatus='VISUALLY_REVIEWED',finding='양극 충전 단자와 차량 측 음극의 지정 금속 접지 위치를 그림에서 확인. 배터리 음극 직결로 치환하지 않음.')
out=dict(schemaVersion=1,reviewer='AI',runtimeApproved=False,expertApproved=False,structuredEncodingComplete=False,sourceReadingComplete=True,scope='200 assigned emergency/brake/key sections plus 24 mandatory N-retention/emergency-key/start reference sections; general recursive operations excluded.',sectionCount=200,additionalRequiredSectionCount=24,newDistinctUnitsRead=836,unreadRequiredSections=[],entries=entries,additionalReferences=extra_rows,modelDifferences=diffs,sourceAmbiguities=holds,visualEvidence=visual,documentCounts=dict(Counter(e['documentId'] for e in entries)),baselineReview='data/manual-review/2026-10-28/hyundai-web-coverage.json')
(B/'data/manual-review/2026-10-28/audit-hyundai-web-emergency-closure.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf-8')
print('Saved 200 sections +24 mandatory references, 836 read units; 5 jump diagrams visually checked.')
