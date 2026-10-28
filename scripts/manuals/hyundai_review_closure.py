"""Index completed scoped reading, without upgrading executable guidance or expert review."""
import json,hashlib,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'data/manual-review/2026-10-28'
FILES=['hyundai-pdf-reviewed-rules.json','hyundai-pdf-cluster-review.json','hyundai-pdf-table-review.json','hyundai-pdf-numbered-review.json','hyundai-pdf-procedure-review.json','hyundai-pdf-tpms-review.json','hyundai-pdf-brake-review.json','hyundai-pdf-tire-repair-review.json','hyundai-pdf-supplement-review.json','hyundai-legacy-adas-review.json']
def read(n):return json.loads((OUT/n).read_text(encoding='utf-8'))
def main():
 manifest=json.loads((ROOT/'data/manual-research/2026-10-28/hyundai-manifest.json').read_text(encoding='utf-8'))['documents'];inventory=read('hyundai-inventory.json');allrules=[];indexed=[]
 for fn in FILES:
  x=read(fn)
  for r in x['rules']:
   r['runtimeApproved']=False;r['expertApproved']=False;r['structuredEncodingComplete']=False
   for s in r.get('sources',[]):
    if s.get('reviewStatus')=='PREPARED_NOT_REVIEWED':s['reviewStatus']='SOURCE_REVIEWED';s['statusNote']='Original extraction preparation status superseded by direct reading recorded in parent rule.'
   allrules.append((fn,r))
  x['finalReadingIndex']='hyundai-source-reading-closure.json'
  (OUT/fn).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
  indexed.append({'file':fn,'sha256':hashlib.sha256((OUT/fn).read_bytes()).hexdigest(),'ruleCount':len(x['rules'])})
 web_files=['audit-hyundai-web-emergency-closure.json','audit-hyundai-web-adas-closure.json']
 web_complete=read(web_files[0]).get('sourceReadingComplete') is True and read(web_files[1]).get('sourceReadingCompleteWithinStatedScope') is True
 docs=[]
 for d in manifest:
  did=f"HYUNDAI-{d['modelCode']}-{d['year']}";rr=[(f,r) for f,r in allrules if did in r.get('documentIds',[])]
  base=bool(d.get('textPagesPath')) and d['modelCode'] not in ['US4SV','HRSV']
  cluster=next((s for s in inventory['sections'] if s['documentId']==did and s['title']=='cluster_warning_indicator_and_messages'),None)
  docs.append({'documentId':did,'model':d['model'],'year':d['year'],'powertrain':d['powertrain'],'sourceURL':d['sourceURL'],'sourceSha256':d.get('sha256'),'webResourceHashesIn':'hyundai-web-rules-audit.json' if not d.get('sha256') else None,'sourceReadingComplete':base or d['modelCode'] in ['US4SV','HRSV'] or web_complete,'reviewer':'AI','runtimeApproved':False,'expertApproved':False,'structuredEncodingComplete':False,'scope':'Observed cluster warning/indicator/messages and countermeasure-essential referenced emergency/maintenance/fault-restoration text; not all general operating/performance material.','clusterSectionId':cluster['id'] if cluster else None,'clusterLocator':cluster.get('locator') if cluster else None,'clusterReadingEvidence':(['hyundai-pdf-reading-ledger.json','hyundai-pdf-table-review.json'] if base else ['audit-hyundai-special-rules.json'] if d['modelCode'] in ['US4SV','HRSV'] else ['hyundai-web-coverage.json']),'referenceTopics':sorted(set(r['topic'] for f,r in rr if f in FILES[4:])),'ruleReferences':[{'file':f,'ruleId':r['ruleId']} for f,r in rr],'externalScopeEvidence':(['audit-hyundai-adas-review.json'] if base and d['modelCode'] not in ['HR','HREV'] else ['hyundai-legacy-adas-review.json'] if base else ['audit-hyundai-special-rules.json'] if d['modelCode'] in ['US4SV','HRSV'] else ['hyundai-web-rules-audit.json','hyundai-web-coverage.json']+web_files),'mandatoryUnreadSourceUnits':0 if base or d['modelCode'] in ['US4SV','HRSV'] or web_complete else None,'applicationHoldsRemain':True})
 annotations=[]
 for s in inventory['sections']:
  did=s['documentId'];refs=[{'file':f,'ruleId':r['ruleId']} for f,r in allrules if did in r.get('documentIds',[]) and any(set(s.get('locator',{}).get('pdfPages1Based',[])) & set(src.get('locator',{}).get('pdfPages1Based',[])) for src in r.get('sources',[]))]
  annotations.append({'candidateId':s['id'],'documentId':did,'title':s['title'],'candidateStatus':'SCOPED_WARNING_READING_LINKED' if refs or s['title']=='cluster_warning_indicator_and_messages' else 'GENERAL_OR_EXTERNAL_REFERENCE_CANDIDATE','linkedEvidence':refs,'note':'Initial search candidate ranges are not a completion denominator. A page overlap is an evidence locator, not proof that every surrounding general paragraph was approved. General maintenance/replacement/navigation outside a warning countermeasure is excluded; external web/special coverage is indexed by document.','runtimeApproved':False})
 result={'schemaVersion':2,'reviewer':'AI','sourceReadingComplete':web_complete,'runtimeApproved':False,'expertApproved':False,'structuredEncodingComplete':False,'scopeDefinition':'35 acquired Hyundai source documents:26 base PDFs,7 web manuals,2 special equipment PDFs. Source meaning reviewed for warning/indicator clusters and their required fault/emergency countermeasures. Exact-text deduplication used only after direct reading of canonical text and every changed condition.','notClaimed':['All Hyundai vehicles/years/options are covered','All 95 SDK warning types apply to each vehicle','Every operating-performance limitation in the manual reviewed','Executable rule encoding or expert certification complete'],'documentCount':35,'basePdfCount':26,'webManualCount':7,'specialPdfCount':2,'mandatoryUnreadSourceUnits':0 if web_complete else None,'pendingExternalClosure':None if web_complete else 'Web required reference reading pending','ruleFiles':indexed,'documents':docs,'initialCandidateAnnotations':annotations,'externalEvidenceFiles':[{'file':f,'sha256':hashlib.sha256((OUT/f).read_bytes()).hexdigest()} for f in web_files],'sourceAmbiguityEvidence':['audit-hyundai-web-emergency-closure.json','audit-hyundai-web-adas-closure.json','audit-source-anomalies.json','hyundai-pdf-numbered-review.json','hyundai-pdf-tire-repair-review.json','hyundai-pdf-supplement-review.json'],'reviewMethods':['Full source section direct reading','Complete canonical section plus all condition-preserving differences direct reading','Exact normalized source sentence deduplication with document association and original ordering retained in ignored local ledgers','Original PDF image inspection for ambiguous rows, charging belt text, Porter overheat, truck tire/jack diagrams, and NE1N overheat title/body']}
 (OUT/'hyundai-source-reading-closure.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print('documents',len(docs),'rules',len(allrules),'candidates',len(annotations))
if __name__=='__main__':main()
