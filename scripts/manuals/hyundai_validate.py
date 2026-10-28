"""Read-only integrity audit of the Hyundai research manifest and local originals."""
import hashlib,json
from pathlib import Path
import pymupdf
from hyundai_acquire import OUT,ROOT

def main():
    manifest=json.loads((OUT/'hyundai-manifest.json').read_text(encoding='utf-8'))
    results=[]
    for doc in manifest['documents']:
        errors=[]
        if doc['status']=='downloaded':
            path=ROOT/doc['localPath'];data=path.read_bytes()
            if not data.startswith(b'%PDF-'):errors.append('signature')
            if hashlib.sha256(data).hexdigest()!=doc['sha256']:errors.append('sha256')
            if len(data)!=doc['bytes']:errors.append('bytes')
            with pymupdf.open(path) as pdf:
                if len(pdf)!=doc['pages']:errors.append('page_count')
                if not any('\uac00'<=c<='\ud7a3' for page in [pdf[0],pdf[min(10,len(pdf)-1)]] for c in page.get_text()):errors.append('Korean_text')
            for topic in doc['topicLocators']:
                if any(n<1 or n>doc['pages'] for n in topic['pdfPages1Based']):errors.append('page_out_of_bounds')
        elif doc['status']=='web_acquired':
            for item in doc['resources']:
                data=(ROOT/item['localPath']).read_bytes()
                if hashlib.sha256(data).hexdigest()!=item['sha256']:errors.append('web_sha256')
                if len(data)!=item['bytes']:errors.append('web_bytes')
            if doc['missingSearchTopicIds']:errors.append('missing_search_topics')
        else:errors.append('not_acquired:'+doc['status'])
        results.append({'modelCode':doc['modelCode'],'year':doc['year'],'status':'pass' if not errors else 'fail','errors':errors})
    coverage=json.loads((OUT/'hyundai-current-lineup-coverage.json').read_text(encoding='utf-8'))
    result={'documentsChecked':len(results),'passed':sum(r['status']=='pass' for r in results),'failed':sum(r['status']=='fail' for r in results),'pdfCount':sum(d['status']=='downloaded' for d in manifest['documents']),'pdfPages':sum(d.get('pages',0) for d in manifest['documents']),'webCount':sum(d['status']=='web_acquired' for d in manifest['documents']),'webTOCTopics':sum(d.get('tocTopics',0) for d in manifest['documents']),'bytes':sum(d.get('bytes',0) for d in manifest['documents']),'currentSalesVariantsInScope':coverage['inScopeVariants'],'unmappedSalesVariants':sum(r['status']=='unmapped_current_listing' for r in coverage['rows']),'semanticApproval':False,'results':results}
    (OUT/'hyundai-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='results'},ensure_ascii=False))
    if result['failed']:raise SystemExit(1)

if __name__=='__main__':main()
