"""Persist source-read tire emergency procedures; never an executable repair guide."""
import json, hashlib, re
from hyundai_review_tpms_legacy_adas import ROOT, OUT, RAW, MAN, rule

def main():
 units=json.loads((RAW/'tire-repair-units.json').read_text(encoding='utf-8'))
 sentences=json.loads((RAW/'tire-repair-sentences.json').read_text(encoding='utf-8'))
 units += [{'id':f'{c}-{y}-TIRE_REPAIR','pages':list(range(a,b+1))} for c,y,a,b in [('QX',2027,334,339),('HR',2026,265,282),('HREV',2026,233,245)]]
 rules=[]
 for u in units:
  code,year=u['id'].split('-')[:2]
  threshold=42 if code in ['HR','HREV'] else 29
  damage=6 if code=='QX' else 4
  cold=-40 if any(u['id'] in s['units'] and '-40°C' in s['text'] for s in sentences) else -30
  r=rule(code,year,'TIRE_REPAIR',u['pages'],['장착된 해당 차량용 TMK로 트레드의 작은 펑크만 임시 수리한다. 측면·심한 손상은 수리 대상이 아니다.'],[
   '안전하고 단단한 평지에 세우고 주차브레이크를 체결한다. 키트 설명서·유효기간을 확인하고 속도 제한 라벨을 잘 보이는 곳에 붙인다.',
   '컴프레서를 끈 상태에서 봉합제와 호스를 정확히 고정하고, 해당 키트의 전원 연결 그림과 순서에 따라 연결한다. 시동 상태에서 규정 공기압까지 약 5–7분 주입한다.',
   f'압력이 {threshold}psi 이하이면 출발하지 않는다. 충족되면 컴프레서를 끄고 호스·전원을 분리하여 보관한다.',
   '봉합제 분배는 해당 문서의 20km/h 이상, 7–10km 또는 약 10분 조건을 확인한다. 최대 80km/h를 지키고 이상 진동·소음·거친 주행이면 감속하여 안전 정차 후 견인 점검한다.',
   '안전 정차 후 봉합제를 연결하지 않고 직접 호스로 공기압을 재측정·조정한다. 측정 시 컴프레서를 끈다. 규정 공기압이 유지되지 않으면 운행을 중단하고 서비스/견인을 요청한다.',
   '임시 수리 후 200km 이내 정비소에서 타이어를 점검/교체한다. 센서와 휠의 잔여 봉합제를 제거하고 사용한 용기·주입 호스는 교환한다.'
  ],[f'{damage}mm 이상 손상·측면 손상에 TMK 사용 금지.',f'주변 기온 {cold}°C 이하 사용 금지 문구를 보존한다.','컴프레서를 10분 이상 계속 작동하지 않는다. 박힌 못을 임의로 뽑지 않으며 사용 중 키트를 방치하지 않는다.','실런트를 먹거나 눈·피부에 닿게 하지 않고 어린이에게 노출하지 않는다.','압력만 조절할 때 봉합제를 사용하지 않는다.'],[
   '요약은 실제 연결 그림/타이어 규격을 대체하지 않는다. 차종·연식·키트 A/B 사양·타이어 크기·전원 방식 확인이 필요하다.',
   '재분배 주행 문구가 있어도 저압 주행 금지 및 규정 압력 미유지 운행 중단 조건을 지우지 않는다.',
   '치료 처방은 이 정비 자료에서 자동 생성하지 않는다. 봉합제 노출 응급 지침은 제품 안내와 전문 의료 조언 대상으로 분리한다.'
  ])
  r['reviewMethod']='All 826 unique exact-normalized source sentences and document associations directly read; QX/HR/HREV complete page sequences additionally read; high-risk Porter/ST1/Staria EV diagrams visually checked.'
  r['numericConditions']={'noDriveAtOrBelowPsi':threshold,'damageNotRepairableAtOrAboveMm':damage,'temperatureNoUseAtOrBelowC':cold}
  if code in ['HR','HREV']:
   r['orderedActions'] += ['1톤 2WD 후륜은 손상 타이어를 임시 탈거해야 한다. 전원 OFF, 평지·주차브레이크·대각선 고임목·전원 OFF를 유지하고 지정 잭 지점에만 설치한다. 승객을 내리고 최소 높이만 든다. 접촉면 청소 후 휠을 맞추고 대각선 순서로 2–3회에 나누어 15–20kgf·m로 체결한다. 약 1,000km 후 풀림을 재점검한다.']
   r['driverProhibitions'] += ['잭으로 든 상태에서 시동·하부 진입·흔들기 금지. 잭 최대 하중 초과 금지. 잭 녹색 정지 마크가 보이면 더 올리지 않는다. 내릴 때 밸브를 2회 이상 풀지 않는다.','휠 볼트/너트에 오일 도포, 렌치 밟기·파이프 연장 금지.']
   r['applicationConstraints'] += ['TMK 연결은 배터리 +/− 클램프인데 재압력 조정 절에 다용도 소켓 연결 문구가 공존한다. 실제 키트 확인 전 연결 자동 안내 보류.','기온 -30°C 이상 허용 문구와 -30°C 이하 금지가 함께 있어 경계값 자동 판단 보류.']
   r['sourceAmbiguities']=['TMK 전원 연결 방식의 문맥 불일치','영하 30도 경계 포함 여부']
  if code=='HREV':r['applicationConstraints']+=['EV 타이어 교환 절의 엔진/수동 1단 문구는 실제 차량 적용성이 의심되어 전이 금지.']
  if code in ['NE1N','CE1N']:r['modelSpecificConditions']=['휠 너트 18–20kgf·m. 다른 차종의 11–13 값을 전이하지 않는다.']
  if code in ['NE1']:r['applicationConstraints']+=['7–10km 거리를 10분 정도 주행하는 원문 표현을 다른 문서의 OR 논리로 일괄 치환하지 않는다.']
  if code=='US4EV':r['applicationConstraints']+=['최초 연결 그림은 12V 배터리 −단자, 재조정 문구는 −충전단자(차체 접지). 두 위치를 추정 통합하지 않는다.']
  r['requiredContext']=['modelCode','modelYear','powertrain','TMKType','tireSize','vehiclePressureLabel','damageLocation','damageSize','actualPressure','ambientTemperature']
  rules.append(r)
 b=(RAW/'tire-repair-sentences.json').read_bytes()
 (OUT/'hyundai-pdf-tire-repair-review.json').write_text(json.dumps({'schemaVersion':1,'rules':rules,'readingLedger':{'uniqueSourceSentencesRead':826,'allUnitIndicesRead':list(range(826)),'sha256':hashlib.sha256(b).hexdigest(),'localPath':str((RAW/'tire-repair-sentences.json').relative_to(ROOT))},'runtimeApproved':False,'scope':'TMK and explicitly referenced Porter jack/tire removal, not universal roadside towing approval'},ensure_ascii=False,indent=2),encoding='utf-8')
 print(len(rules))
if __name__=='__main__':main()
