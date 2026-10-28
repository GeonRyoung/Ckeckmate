"""Serialize semantic reviews of manually read numbered warning sections."""
import json,re,hashlib
from pathlib import Path
from hyundai_review_cluster_notes import ROOT,MAN
from hyundai_review_table_notes import TOPICS
ASSIGNMENTS={
 'US4EV':(2027,168,173,'READY SERVICE CHARGE_INDICATOR BELT SRS REGEN REGEN BRAKE ABS EBD CHARGE12 EPS TPMS EPB HV_LOW FCA LKA DAW MASTER LED ICE POWER AUTO_HOLD NORMAL_OTHER LFA ISLA DOOR ESC ESC_OFF KEY TURN LIGHTS LIGHTS LIGHTS LIGHTS'.split()),
 'US4':(2026,109,115,'BELT SRS BRAKE ABS EBD FUEL LPG_OVERFILL OIL MIL CHARGE12 COOLANT_RED EPS TPMS EPB FCA LKA DAW MASTER LED ICE AUTO_HOLD LFA ISLA LPI_WAIT DOOR ESC ESC_OFF KEY TURN LIGHTS LIGHTS LIGHTS LIGHTS'.split()),
 'US4HEV':(2026,141,147,'READY HEV_EV_MODE SERVICE BELT SRS REGEN REGEN BRAKE ABS EBD FUEL OIL MIL CHARGE12 COOLANT_RED EPS TPMS EPB HV_LOW FCA LKA DAW MASTER LED ICE GREEN_ZONE AUTO_HOLD LFA ISLA DOOR ESC ESC_OFF KEY TURN LIGHTS LIGHTS LIGHTS LIGHTS'.split()),
 'CE1':(2025,144,150,'READY SERVICE CHARGE_INDICATOR BELT SRS REGEN REGEN BRAKE ABS EBD CHARGE12 EPS TPMS EPB HV_LOW FCA STEERING_SAFETY LKA DAW DMS MASTER LED IFS_FAULT AWD ICE POWER AUTO_HOLD NORMAL_OTHER LFA ISLA NORMAL_OTHER DOOR ESC ESC_OFF KEY TURN LIGHTS LIGHTS LIGHTS NORMAL_OTHER'.split()),
 'CE1N':(2025,139,145,'READY SERVICE CHARGE_INDICATOR BELT SRS REGEN REGEN BRAKE ABS EBD CHARGE12 EPS TPMS EPB HV_LOW FCA STEERING_SAFETY LKA DAW DMS MASTER LED IFS_FAULT AWD ICE POWER AUTO_HOLD NORMAL_OTHER LFA ISLA NORMAL_OTHER DOOR ESC ESC_OFF KEY TURN LIGHTS LIGHTS LIGHTS NORMAL_OTHER NORMAL_OTHER NORMAL_OTHER NORMAL_OTHER NORMAL_OTHER'.split())
}
def main():
 rules=[];coverage=[]
 for code,(year,start,end,topics) in ASSIGNMENTS.items():
  d=next(x for x in MAN if x['modelCode']==code and x['year']==str(year))
  pages=json.loads((ROOT/d['textPagesPath']).read_text(encoding='utf-8'))
  text='';positions=[]
  for n in range(start,end+1):
   positions.append((len(text),n));text+=pages[n-1]+'\n'
  # Require Korean heading on the same line, skipping the preceding icon-only index.
  matches=list(re.finditer(r'(?m)^\((\d+)\)\s+[^\n]*[가-힣][^\n]*$',text))
  assert len(matches)==len(topics),(code,len(matches),len(topics))
  for idx,(m,topic) in enumerate(zip(matches,topics)):
   finish=matches[idx+1].start() if idx+1<len(matches) else text.find('클러스터 메시지 확인하기',m.end())
   if finish<0:finish=len(text)
   nums=[n for off,n in positions if off<finish and (n==end or positions[n-start+1][0]>m.start())]
   body=text[m.start():finish];cond,act=TOPICS[topic]
   r={'ruleId':f'HY-NUMBER-{code}-{year}-{idx+1:02}','documentIds':[f'HYUNDAI-{code}-{year}'],'topic':topic,'sourceHeading':m.group(0),'conditions':[cond],'orderedActions':[act],'driverProhibitions':[],'applicationConstraints':['다른 연식·구동계로 자동 전파하지 않는다.','연결된 비상·정비 절차와 실행형 조건 구조화 완료를 뜻하지 않는다.'],'requiredContext':['정확한 경고 종류·색상·패턴·전원 단계·추가 메시지','장착 사양'],'sources':[{'url':d['sourceURL']+f'#page={nums[0]}','documentSha256':d['sha256'],'passageSha256':hashlib.sha256(body.encode()).hexdigest(),'locator':{'pdfPages1Based':nums,'printedPageLabels':[str(n-8) for n in nums]}}],'reviewStatus':'SOURCE_REVIEWED','reviewMethod':'AI direct complete numbered-section reading; CE1N compared with fully read CE1 and every difference inspected; US4HEV compared with fully read US4 and every difference inspected','runtimeApproved':False,'expertApproved':False,'structuredEncodingComplete':False}
   if code in ['CE1','CE1N','US4EV']:
    r['powerStateTerminology']=['POWER ON','DRIVE READY']
   if topic=='EBD':r['orderedActions']=['고속 주행을 피하고 안전에 유의하여 정비한다.']
   if topic=='EPS':r['conditions']=['초기 약3초 정상 점등; 처음부터 표시가 없거나3초 이후 지속하면 이상 문맥']
   if topic=='AUTO_HOLD':r['modelSpecificConditions']='이상 색상은 주황색.'
   if topic=='ESC_OFF':
    r['reviewStatus']='SOURCE_AMBIGUITY';r['reviewNote']='원문은 사용자 OFF 정상 점등 설명 다음에 지속점등이면 점검을 받으라고 적는다. 사용자 해제와 고장 구분 없이 실행형 분기로 확정하지 않는다.'
   if topic=='CHARGE12':r['orderedActions']=['12V 배터리 충전 상태와 충전 계통을 점검하고 지속되면 정비한다.']+(['해당 내연기관/HEV 원문은 구동 벨트 점검도 안내한다.'] if code in ['US4','US4HEV'] else [])
   if topic=='OIL':r['restartCriteria']='유압 회복 후 재시동해야 경고/출력 제한이 해제된다고 명시.'
   if code=='US4HEV' and topic=='HV_LOW':
    r['reviewStatus']='SOURCE_AMBIGUITY';r['reviewNote']='비플러그인 HEV 원문에 EV와 같은 잔여30~40km·즉시충전 안내가 들어 있다. 외부 충전 지시로 전파하지 않는다. 별도 SOC 정차/P 충전 메시지 절을 따른다.';r['orderedActions']=[]
   if topic=='NORMAL_OTHER':
    r['modelSpecificConditions']={('US4EV',24):'아이 페달 작동 표시',('CE1',28):'아이 페달 작동 표시',('CE1',31):'차로변경: 초록 가능·초록점멸 작동·회색 대기·흰색점멸 취소',('CE1',40):'지능형 헤드램프 흰색 준비·초록 작동, 상향LED 부분 소등',('CE1N',28):'아이 페달 작동 표시',('CE1N',31):'차로변경: 초록 가능·초록점멸 작동·회색 대기·흰색점멸 취소',('CE1N',40):'지능형 헤드램프 흰색 준비·초록 작동',('CE1N',41):'배터리 컨디셔닝 작동',('CE1N',42):'드리프트 주행 모드 작동',('CE1N',43):'N 모드 작동 중 켜짐·해제 시 소등',('CE1N',44):'런치컨트롤 준비 상태'}.get((code,idx+1))
   rules.append(r)
  coverage.append({'documentId':f'HYUNDAI-{code}-{year}','numberedItemsRead':len(topics),'pdfPages1Based':list(range(start,end+1)),'linkedProceduresReviewed':False,'allCountermeasuresReviewed':False})
 out={'schemaVersion':1,'reviewer':'AI','runtimeApproved':False,'allCountermeasuresReviewed':False,'rules':rules,'coverage':coverage}
 (ROOT/'data/manual-review/2026-10-28/hyundai-pdf-numbered-review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print('numbered review rules',len(rules))
if __name__=='__main__':main()
