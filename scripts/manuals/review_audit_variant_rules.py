"""Serialize directly read GT and PV5 special-equipment source findings."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'.local/manual-review/2026-10-28/audit/variants'
OUT=ROOT/'data/manual-review/2026-10-28'
def read(n): return json.loads((RAW/n).read_text(encoding='utf8'))
sources=read('manifest.json')+read('supplementary-manifest.json')
byurl={s['URL']:s for s in sources}
rules=[]
def add(key, topics, condition, actions, forbidden, note=''):
 selected=[s for s in byurl.values() if any(s['URL'].endswith('/'+x+'.html') and s['code']==c for c,x in topics)]
 assert len(selected)==len(topics),(key,topics)
 rules.append({'ruleId':'AUDIT-VARIANT-'+key,'documentIds':sorted({'kia_'+s['code'] for s in selected}),
  'sources':[{'URL':s['URL'],'hash':s['hash'],'locator':{'title':s['title']}} for s in selected],
  'topic':key,'conditions':condition,'orderedActions':actions,'prohibitions':forbidden,'restartCriteria':[],
  'requiredContext':['차종·연식','GT/PV5 전용 장비 장착 여부','정확한 경고 메시지'],
  'reviewStatus':'SOURCE_REVIEWED','reviewMethod':'AI 해당 본문 직접 독해','reviewer':'AI','runtimeApproved':False,
  'structuredEncodingComplete':False,'reviewNote':note})

add('GT-ECS',[('SV1_2027','t00510'),('CT1_2027','t00708_4'),('OV1K_2026','gt8'),('CV1_2027','t00731')],
 ['전자제어 서스펜션 점검 경고; 12 V 과/저전압 보호 중 일시 경고 가능'],
 ['지정 서비스센터/협력사에서 점검한다.'],['일시 전압 원인 가능성만으로 실제 고장을 배제하지 않는다.'])
add('GT-PREVIEW-LIMIT',[('CT1_2027','t00708_4'),('OV1K_2026','gt8')],
 ['전방 카메라 가림·내비 재탐색·터널 GPS 수신 제한'],
 ['전방 카메라 영역을 청결히 유지한다. 카메라/유리 교환·재조립은 보정 점검을 의뢰한다.'],
 ['카메라 영역에 필름·스티커 부착 및 대시보드 반사물 배치 금지.'],
 '센서 한계를 넘으면 프리뷰가 제한되고 일반 ECS 제어가 남는다는 의미를 고장 표시와 구분.')
add('GT-ELSD',[('CV1_2027','t00735'),('MV1_2027','t00887')],
 ['고온 일시중지','타이어 동일 여부 메시지','시스템 점검 메시지'],
 ['과열이면 차량을 정지시켜 장치를 식힌다.','타이어 메시지이면 동일 크기·타입을 장착한다.','시스템 이상이면 지정 서비스센터에서 점검한다.'],
 ['고온·타이어 불일치·장치 고장을 한 가지 조치로 합치지 않는다.'])
add('GT-ELSD-JACK',[('CV1_2027','t00732'),('MV1_2027','t00887')],['e-LSD 차량 정비'],[],
 ['한 바퀴만 잭으로 들어 올린 상태에서 바퀴를 구동하지 않는다.'])
add('PV5-OPENBED-DOOR',[('SW1K_2027','c_t0004'),('SW1K_2027','c_t0015'),('SW1K_2027','c_t0016')],
 ['적재함 도어 개방 시 후미 램프 가려짐','작업 후 도어 잠금 필요'],
 ['개방 시 삼각대 등으로 뒤 차량에 경고한다.','주행 전 보조 잠금까지 확실히 확인하고 화물을 분산·고정한다.'],
 ['적재함 사람 탑승·펼친 도어 위 적재·경사면 하역·임의 특장 개조 금지.','기본형 700 kg/항속형 600 kg 초과 적재 금지.'],
 'c_t0004 작업 정차 문구는 N+주차브레이크를 명시한다. 다른 장의 P 지시와 상황을 구분하고 실행형 적용 전 확인 필요.')
add('PV5-OPENBED-LAMPS',[('SW1K_2027','c_t0035'),('SW1K_2027','c_t0036'),('SW1K_2027','c_t0037')],
 ['LED 후퇴·방향·후미·제동등 불점등','별도 벌브 번호등'],
 ['일체형 LED는 숙련 기술자에게 점검/교체를 의뢰한다.','번호등 벌브 작업은 주차브레이크 체결 및 시동 종료 후 해당 분리 절차를 따른다.'],
 ['LED 일체형과 교체 가능한 번호등 벌브를 혼동하지 않는다.'])
add('PV5-PRIME-SEAT',[('SW1K_2027','c_t0047'),('SW1K_2027','c_t0048'),('SW1K_2027','c_t0049')],
 ['릴렉션 시트 자동 이동 또는 복귀'],
 ['끼임을 살피고 가급적 주정차 휴식 때 사용한다.','자동 이동 중 시트 조절 스위치를 조작하면 자동 이동을 중지할 수 있다.'],
 ['두 종류 스위치 동시 조작 금지.'], '기본 차량 계기판 고장과 별개 특장 장비 조작 안전.')
add('PV5-PRIME-VENT',[('SW1K_2027','c_t0057'),('SW1K_2027','c_t0058')],
 ['열선/통풍 시트 표시','시트에 액체 유입'],
 ['액체를 쏟으면 통풍을 끄고 닦은 후 완전히 말려 사용한다.','열선 자동 중단/재개는 온도 제어임을 구분하고 저온 화상 위험에 주의한다.'],
 ['유기용제 세척·무겁거나 날카로운 물건 올림 금지.'], '정상 강약 표시를 고장 경고로 분류하지 않는다.')
add('PV5-WAV-PREPARATION',[('SW1K_2027','t00259'),('SW1K_2027','t00263'),('SW1K_2027','t00264'),('SW1K_2027','t00266')],
 ['휠체어 승하차 전 공간/노면/슬로프 확인'],
 ['평지에서 P와 주차브레이크를 유지하고 공간과 좌석 고정을 확인한다.','슬로프 끝단 밀착과 이탈방지판을 확인한다.','120 mm 미만은 2단, 120–180 mm는 1단 사용 조건을 확인한다.'],
 ['젖음·눈·얼음으로 미끄러운 슬로프 사용 금지.','슬로프 약 300 kg 최대 하중 초과 금지.','주행 중 또는 사람이 앉은 상태 좌석 조정 금지.'],
 '이 기록은 준비/슬로프 절만 검토했다. 휠체어 전후 고정·안전벨트 전체 절차까지 검증한 것으로 표시하지 않는다.')

(OUT/'audit-variant-rules.json').write_text(json.dumps({'version':1,'runtimeApproved':False,'rules':rules,
 'scopeLimit':'PV5 전체 특장 조작 설명서 검토가 아님; 지정 sources의 고장/주의 분기 검토. 미검토 일반 조작·WAV 고정 절차는 별도.'},ensure_ascii=False,indent=2),encoding='utf8')
print(len(rules))
