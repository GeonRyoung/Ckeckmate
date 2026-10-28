"""Structural audit only: it cannot turn candidates into source-reviewed facts."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/manual-review/2026-10-28'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def main():
 findings=[];total=0
 for n in ['audit-supplement-rules.json','audit-variant-rules.json','hyundai-web-rules-audit.json','audit-hyundai-special-rules.json']:
  d=read(OUT/n)
  for r in d['rules']:
   total+=1
   assert r['runtimeApproved'] is False,(n,r['ruleId'])
   assert r['sources'] and all(len(s['hash'])==64 and s['URL'].startswith('https://ownersmanual.') for s in r['sources'])
   assert r['reviewer']=='AI'
 findings.append({'check':'own_review_records_have_sources_and_no_runtime_approval','passed':True,'records':total})
 w=read(ROOT/'data/manual-research/2026-10-28/warning_mapping.json')
 assert len(w['warnings'])==95
 matrix=[]
 for r in w['warnings']:
  matrix.append({'sdkSymbol':r['sdk_symbol'],'sdkStateDomain':['OFF','ON','BLINK'],
   'reviewMappingStatus':'SEMANTIC_MAPPING_PENDING','vehicleApplicability':'UNKNOWN_UNTIL_EXACT_DOCUMENT_OPTION_MATCH',
   'runtimeApproved':False,'note':'SDK 타입 존재는 각 차량 장착 또는 문서 검토 완료 증거가 아님. 원문 항목과 다대다 의미 매핑 필요.'})
 (OUT/'audit-sdk-coverage.json').write_text(json.dumps({'sdkTypes':95,'rows':matrix,'runtimeApproved':False,
  'denominator':'95 SDK types are an integration taxonomy, not 95 warnings on every vehicle',
  'source':w['sdk'],'automaticCandidatePromotion':False},ensure_ascii=False,indent=2),encoding='utf8')
 findings.append({'check':'sdk_taxonomy_denominator','passed':True,'types':95,'vehicleMappingsApproved':0})
 counts=read(OUT/'hyundai-web-coverage.json')['counts']
 findings.append({'check':'hyundai_web_sections','counts':counts,'fullyExecutable':False})
 kp=OUT/'kia-rules.json'
 if kp.exists():
  k=read(kp);rs=k['records'];assert all(r['runtime_approved'] is False and r['expert_approved'] is False for r in rs)
  findings.append({'check':'kia_no_runtime_or_expert_approval','passed':True,'snapshotRecords':len(rs),
    'sourceMeaningReviewIsNotCrossReferenceCompletion':True,'snapshotHash':hashlib.sha256(kp.read_bytes()).hexdigest()})
 (OUT/'audit-validation.json').write_text(json.dumps({'version':1,'scope':'structure/denominator audit; not automotive expert approval',
  'runtimeApproved':False,'findings':findings},ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(findings,ensure_ascii=False))
if __name__=='__main__':main()
