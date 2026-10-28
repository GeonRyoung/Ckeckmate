import copy
"""Persist only explicitly read procedure units and source-specific exceptions."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'.local/manual-review/2026-10-28/hyundai/procedures'
UNITS=json.loads((RAW/'units.json').read_text(encoding='utf-8'))
MAN=json.loads((ROOT/'data/manual-research/2026-10-28/hyundai-manifest.json').read_text(encoding='utf-8'))['documents']
READ={
'OVERHEAT':['DN8-2026','DN8HEV-2026','DN8c-2025','US4-2026','US4HEV-2026','MX5-2026','MX5HEV-2026','AX-2027','SX2-2027','SX2HEV-2027','LX3-2027','LX3HEV-2027','CN7N-2026'],
'OIL':['DN8-2026','DN8HEV-2026','DN8c-2025','US4-2026','US4HEV-2026','MX5-2026','MX5HEV-2026','AX-2027','SX2-2027','SX2HEV-2027','LX3-2027','LX3HEV-2027'],
'COOLANT':['NE1-2025','A01-2026','NE1-2027','CE1-2025','ME-2027','AXEV-2027','SX2EV-2025','DN8-2026','DN8HEV-2026','DN8c-2025','US4-2026','US4HEV-2026','MX5-2026','MX5HEV-2026','AX-2027','SX2-2027','SX2HEV-2027','LX3-2027','LX3HEV-2027','CN7N-2026','NE1N-2026','CE1N-2025'],
'BRAKE_FLUID':['DN8-2026','A01-2026','US4EV-2027','NE1-2027','NE1-2025','CE1-2025','ME-2027','AXEV-2027','SX2EV-2025','DN8HEV-2026','DN8c-2025','US4-2026','US4HEV-2026','MX5-2026','MX5HEV-2026','AX-2027','SX2-2027','SX2HEV-2027','LX3-2027','LX3HEV-2027','NE1N-2026','CE1N-2025'],
}
SUMMARY={
'OVERHEAT':{
'conditions':['엔진 수온 과열·출력 저하·노킹 문맥. 증기/냉각수 분출 및 냉각팬 상태를 먼저 구분한다.'],
'orderedActions':['비상등을 켜고 안전하게 정차하여 P·주차브레이크를 적용하고 에어컨을 끈다.','증기 또는 냉각수 분출이면 엔진을 끄고 정비 연락. 분출이 없을 때만 시동 상태에서 후드를 열어 냉각한다. 수온이 내려가지 않거나 팬이 돌지 않으면 시동을 끄고 충분히 식힌다.','충분히 식은 뒤 수량·누수·호스·펌프를 확인한다. 누수/팬 미회전/벨트 손상이 있으면 운전을 중단하고 점검한다. 누수 없이 부족한 경우 적정 냉각수를 천천히 소량씩 보충한다.'],
'driverProhibitions':['뜨거운 냉각수/라디에이터/히터 호스 캡을 열지 않는다.','팬·벨트에 손이나 옷을 가까이하지 않는다.','뜨거운 엔진에 차가운 냉각수를 급하게 붓지 않는다.'],
'applicationConstraints':['냉각팬이 멈출 때까지 OFF 금지라는 주의문을 분출·팬 미회전 분기에 무조건 적용하지 않는다.','정차/시동 조치는 차량별 원문 예외가 우선한다.','오일압력·화재·고전압 배터리 과열에 이 엔진 냉각 절차를 전이하지 않는다.'],
'restartCriteria':'충분한 냉각과 원인 확인이 선행된다. 본문은 경고 소멸만으로 무조건 주행 허가하지 않는다.'},
'OIL':{'conditions':['정기 오일량 점검 및 보충 절차. 엔진 유압 경고의 긴급 조치와 구분.'],'orderedActions':['평지에서 규정 온도까지 예열한 정기 점검 차량은 시동을 끄고 주입캡/게이지를 분리한 뒤 약15분 기다린다.','깨끗이 닦은 게이지를 다시 넣어 F–L 범위를 확인하고 L 이하이면 F까지 보충 후 재확인·밀봉한다.'],'driverProhibitions':['엔진 오일 첨가제 사용 금지.','주입구에 이물질 유입 금지.'],'applicationConstraints':['유압 경고가 이미 켜진 차량에 정기 점검의 예열 단계를 그대로 지시하지 않는다.','엔진별 규격·용량은 별도 원문 표와 대조해야 한다.'],'restartCriteria':'DN8은 유압 회복 후 재시동해야 경고/출력 제한 해제라는 단서가 정비 절에도 있다.'},
'COOLANT':{'conditions':['EV 전기 동력 장치 냉각수 점검; 충분히 냉각된 상태.'],'orderedActions':['시동을 끄고 장치가 식은 뒤 탱크 수량을 확인한다. MIN 부근이면 해당 규격 혼합액을 MAX까지 보충하고 캡을 완전히 잠근다.','누수와 며칠 뒤 수량을 재확인한다. 현저히 감소하면 정비한다.'],'driverProhibitions':['뜨거울 때 캡 개방 금지.','냉각수 없는 상태로 주행 금지.','소금물·지하수·알코올·메탄올 및 다른 계열 혼합 금지.'],'applicationConstraints':['이온수/저전도 냉각수 등 차종별 냉각 회로 차이를 확인하기 전 다른 EV로 전파 금지.','본문 35%/60% 경계 금지 표현과 혼합표의 경계 수치가 함께 있어 극한 경계값을 실행형 규칙으로 확정하지 않는다.'],'restartCriteria':None},
'BRAKE_FLUID':{'conditions':['브레이크액 MIN/MAX 점검·보충.'],'orderedActions':['MIN 아래이면 정비 점검을 받는다. 보충 시 평지 주차 후 탱크 주위를 닦고 청결한 깔때기로 넘치지 않게 넣어 캡을 잠근다.','도장/플라스틱에 묻으면 즉시 닦고 눈에 들어가면 깨끗한 흐르는 물로 씻은 후 진료받는다.'],'driverProhibitions':['장시간 공기 노출액·성분 다른 오일 사용 금지.'],'applicationConstraints':['보충만으로 브레이크 고장이 해결됐다고 판단하지 않는다. 경고 지속과 제동 저하는 별도 고장 절차 적용.','규격 SAE J1704 DOT-4 LV/ISO4925 CLASS-6/FMVSS116 DOT-4를 다른 모델에 자동 전파하지 않는다.'],'restartCriteria':None}}

def make_unit(code,year,topic,nums):
 d=next(d for d in MAN if d['modelCode']==code and d['year']==str(year));p=json.loads((ROOT/d['textPagesPath']).read_text(encoding='utf-8'));text='\n'.join(p[n-1] for n in nums)
 return {'id':f'{code}-{year}-{topic}','documentId':f'HYUNDAI-{code}-{year}','topic':topic,'sourceURL':d['sourceURL'],'documentSha256':d['sha256'],'locator':{'pdfPages1Based':nums},'sourceTextSha256':hashlib.sha256(text.encode()).hexdigest()}

def main():
 rules=[]
 for topic,codes in READ.items():
  for code in codes:
   u=next(u for u in UNITS if u['id']==f'{code}-{topic}');r={'ruleId':'HY-PROCEDURE-'+u['id'],'documentIds':[u['documentId']],'topic':topic,**copy.deepcopy(SUMMARY[topic]),'sources':[u],'reviewStatus':'SOURCE_REVIEWED','reviewer':'AI','reviewMethod':'Direct canonical full passage reading and every source difference with context; explicitly enumerated completed units only','runtimeApproved':False,'expertApproved':False,'structuredEncodingComplete':False};rules.append(r)
 for r in rules:
  if r['topic']=='BRAKE_FLUID':
   modern=['US4EV','NE1','CE1','ME','AXEV','US4','US4HEV','AX','LX3','LX3HEV','CE1N']
   code=r['documentIds'][0].split('-')[1]
   r['modelSpecificConditions']=['MIN 아래이면 점검; MAX까지 청결하게 보충.' if code in modern else 'MIN 이하이면 점검; 보충 시 넘침 방지.']
   if code=='ME':r['modelSpecificConditions']+=['후드 뒤 냉각수 보조 탱크 커버 제거 후 브레이크액 탱크 확인.']
  if r['topic']=='COOLANT':
   r['conditions']=['해당 차량의 엔진/전기 동력 장치 냉각수 점검. 충분히 냉각된 상태이며 HEV는 지정 냉각 회로를 구분한다.']
   r['modelSpecificConditions']=['혼합표: -15°C 35%, -25°C 40%, -35°C 50%, -45°C 60% 부동액. 경계값 금지 문장과 함께 보존하며 자동 배합 지시로 승인하지 않음.']
   if r['documentIds'][0]=='HYUNDAI-DN8HEV-2026':r['modelSpecificConditions']+=['희석수는 증류수로 명시. 엔진 및 인버터/HSG/LDC 냉각 회로 구분. 팬 정비 시 엔진룸12V 전원 분리 커넥터 조건.']
   if r['documentIds'][0]=='HYUNDAI-SX2HEV-2027':r['modelSpecificConditions']+=['엔진 및 인버터/HSG/LDC 냉각 회로 구분. 팬 정비 시 엔진룸12V 전원 분리 커넥터 조건.']
   if r['documentIds'][0]=='HYUNDAI-ME-2027':r['modelSpecificConditions']+=['냉각수 보조 탱크 커버 제거 후 수량 확인.']
  if r['topic']=='OIL':
   r['restartCriteria']='이 문서 정비 절은 유압 회복 후 재시동해야 경고/출력 제한이 해제된다고 명시한다.'
   if r['documentIds'][0] in ['HYUNDAI-DN8HEV-2026','HYUNDAI-SX2HEV-2027']:r['crossSectionReconciliation']='클러스터 단락에는 재시동 문장이 생략되어 있으나 연결된 엔진 오일 정비 절에 명시되어 있다. 클러스터만으로 재시동 불필요 결론을 내리지 않는다.'
 for code,year,nums in [('QX',2027,[330]),('HR',2026,[260,261])]:
  u=make_unit(code,year,'OVERHEAT',nums);r={'ruleId':'HY-PROCEDURE-'+u['id'],'documentIds':[u['documentId']],'topic':'OVERHEAT',**copy.deepcopy(SUMMARY['OVERHEAT']),'sources':[u],'reviewStatus':'SOURCE_REVIEWED','reviewer':'AI','reviewMethod':'Direct full source page reading','runtimeApproved':False,'expertApproved':False,'structuredEncodingComplete':False}
  if code=='HR':
   r['visualVerification']={'pdfPages1Based':[260,261],'printedPageLabels':['5-8','5-9'],'method':'AI viewed original rendered pages; three-column sequence and condition labels confirmed'}
   r['orderedActions']=['안전한 곳에 주차하고 중립·주차브레이크를 적용하며 에어컨을 끈다.','냉각수 분출/수증기 시 원문은 공회전 유지와 멎을 때까지 후드 개방 금지를 요구한다. 분출이 없으면 시동 상태에서 동승석을 들어 통풍시키고 팬 작동을 확인한다. 팬이 돌지 않으면 시동을 끈다.','수온이 내려간 후 시동을 끄고 충분히 식힌 다음 탱크 F–L 수량·워터펌프 벨트·누수를 확인한다. 벨트 파손/누수/재발 우려/수량 감소/팬 미작동이면 신속히 정비한다.'];r['driverProhibitions']=r['driverProhibitions']+['분출이나 증기가 멎기 전 후드를 열지 않는다.'];r['applicationConstraints']=['DN8 등 다른 차종의 분출 시 즉시 OFF 규칙과 다르다. HR 원문을 독립 적용한다.','혼동 위험이 높은 긴급 절차이므로 전문가 확인 전 런타임 승인하지 않는다.']
  rules.append(r)
 for code,year,nums in [('QX',2027,[358,359]),('HR',2026,[305,306]),('CN7N',2026,[392,393])]:
  u=make_unit(code,year,'OIL',nums);r={'ruleId':'HY-PROCEDURE-'+u['id'],'documentIds':[u['documentId']],'topic':'OIL',**copy.deepcopy(SUMMARY['OIL']),'sources':[u],'reviewStatus':'SOURCE_REVIEWED','reviewer':'AI','reviewMethod':'Direct complete source page reading','runtimeApproved':False,'expertApproved':False,'structuredEncodingComplete':False}
  r['restartCriteria']='HR 2.5 T-LPDI는 유압 회복 후 재시동 필요.' if code=='HR' else '이 정비 단락에는 유압 경고 해제를 위한 재시동 요구가 명시되어 있지 않음.'
  if code=='QX':r['orderedActions']=['정기 점검 차량을 평지에 두고 정상 온도 예열 후 시동을 끈다. 약5분 기다린 뒤 게이지를 닦고 다시 넣어 F–L 범위를 확인한다.','L 부근이면 F까지 보충하고 수량 재확인 후 캡과 게이지를 확실히 체결한다.'];r['modelSpecificConditions']=['대기시간 약5분. 다른 최신 문서의15분을 대입하지 않는다.']
  rules.append(r)
 for code,year,nums in [('QX',2027,[360,361]),('HR',2026,[307,308]),('HREV',2026,[260]),('US4EV',2027,[535,536])]:
  u=make_unit(code,year,'COOLANT',nums);r={'ruleId':'HY-PROCEDURE-'+u['id'],'documentIds':[u['documentId']],'topic':'COOLANT',**copy.deepcopy(SUMMARY['COOLANT']),'sources':[u],'reviewStatus':'SOURCE_REVIEWED','reviewer':'AI','reviewMethod':'Direct complete source page reading','runtimeApproved':False,'expertApproved':False,'structuredEncodingComplete':False}
  r['conditions']=['해당 모델의 냉각수 점검. 충분히 냉각된 상태.'];r['modelSpecificConditions']=['QX/HR은 탱크 F–L, HREV/US4EV는 MAX–MIN 표기.']
  if code=='HREV':
   r['orderedActions']=['냉각수 수량을 MAX–MIN 사이인지 확인한다. 부족하면 지정 정비소에서 점검받는다.'];r['driverProhibitions']=['EV 전용 냉각수 적용으로 다른 부동액이나 물을 보충하지 않는다.'];r['applicationConstraints']=['같은 페이지의 일반 혼합비율 표를 자가 물 보충 허가로 해석하지 않는다.'];r['modelSpecificConditions']=['전용 냉각수 경고가 일반 냉각수 보충 템플릿보다 우선한다.']
  if code=='HR':r['modelSpecificConditions']+=['추천 혼합은 부동액40~50:물60~50. 별도 온도표는35/40/50/60%. 냉각수 교환 배출·순환 절차는 전문 정비 작업으로 분리한다.']
  if code=='US4EV':r['applicationConstraints']+=['BEV 문서의 연료 전지 스택룸 언급은 부품 명칭 혼입 의심. 이 문구로 FCEV로 분류하지 않는다.']
  rules.append(r)
 for code,year,nums in [('QX',2027,[361,362]),('HR',2026,[313]),('HREV',2026,[260,261]),('CN7N',2026,[395,396])]:
  u=make_unit(code,year,'BRAKE_FLUID',nums);r={'ruleId':'HY-PROCEDURE-'+u['id'],'documentIds':[u['documentId']],'topic':'BRAKE_FLUID',**copy.deepcopy(SUMMARY['BRAKE_FLUID']),'sources':[u],'reviewStatus':'SOURCE_REVIEWED','reviewer':'AI','reviewMethod':'Direct complete source page reading','runtimeApproved':False,'expertApproved':False,'structuredEncodingComplete':False}
  r['modelSpecificConditions']=['MIN 이하 기준. 클러치액은 HR/CN7N 해당 사양에서만 포함.']
  if code in ['HR','HREV']:r['modelSpecificConditions']+=['해당 저장 용기의 커버를 당겨 분리한 뒤 보충하고 커버를 다시 장착한다.']
  if code=='HR':r['orderedActions']=['점검창에서 MIN–MAX를 확인하고 MIN 이하이면 지정 규격액을 평지에서 보충한다. 현저한 감소는 제동계통 이상을 점검하고 정비한다.','용기 커버 분리·주위 청소·천천히 주입·캡 및 커버 체결 순서. 도장에 묻으면 즉시 닦는다.'];r['driverProhibitions']=['다른 제품과 혼용 금지.','먼지·습기 유입과 눈 접촉 금지.']
  rules.append(r)
 (ROOT/'data/manual-review/2026-10-28/hyundai-pdf-procedure-review.json').write_text(json.dumps({'schemaVersion':1,'reviewer':'AI','runtimeApproved':False,'allCountermeasuresReviewed':False,'rules':rules},ensure_ascii=False,indent=2),encoding='utf-8');print('procedure rules',len(rules))
if __name__=='__main__':main()
