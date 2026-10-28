"""Supplement Hyundai PDF acquisition with official web text/TOC and sales-list coverage.
Run after hyundai_acquire.py. Does not enable any app answer source.
"""
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import re
import urllib.parse
from hyundai_acquire import RAW, OUT, ROOT, BASE, TOPICS, fetch

LINEUP = "https://www.hyundai.com/kr/ko/e/api/common/gnb/menus/M?siteType=H&imageSectionCode=01&includeModelYn=Y"
# Explicit mapping of official sales identifiers to owners-manual catalog identifiers.
# Family linkage is NOT proof that special equipment or current sales year is covered.
MAP = {
    "TS12":["A01"],"HE02":["NH2"],"SX17":["SX2EV"],"NE09":["NE1"],
    "US39":["US4EV"],"US40":["US4EV"],"US41":["US4EV","US4SV"],
    "ME02":["ME"],"CE03":["CE1"],"M579":["HREV"],"M5A0":["HREV","HRSV"],
    "AX07":["AXEV"],"CE05":["CE1N"],"NE08":["NE1N"],"CN26":["CN7N"],
    "DN26":["DN8"],"DN27":["DN8HEV"],"FN01":["CN8"],"FN02":["CN8KH"],
    "GN11":["GN7"],"GN12":["GN7HEV"],"GX01":["NX5"],"GX02":["NX5KP"],
    "FX03":["LX3"],"FX04":["LX3HEV"],"QX07":["QX"],"SX19":["SX2"],"SX20":["SX2HEV"],
    "MX07":["MX5"],"MX08":["MX5HEV"],"AX08":["AX"],
    "US46":["US4HEV","US4SV"],"US36":["US4","US4SV"],"US45":["US4HEV","US4SV"],
    "US31":["US4"],"US34":["US4HEV"],"US30":["US4"],"US33":["US4HEV"],
    "GN13":["GN7"],"US32":["US4"],"US35":["US4HEV"],"TX02":["DN8c"],
    "M578":["HR"],"M5A4":["HRSV","HR"],
}
SPECIAL = {"US41","M5A0","US46","US36","US45","GN13","US32","US35","M5A4"}

def js_json(data):
    s=data.decode("utf-8-sig"); return json.loads(s[s.index("{"):s.rindex("}")+1])

def flatten_toc(tree):
    result={}
    def visit(node):
        if isinstance(node,dict):
            for key,value in node.items():
                if isinstance(value,list) and len(value)>=2:
                    result[key]={"title":value[0],"path":value[1]}
                    if len(value)>2: visit(value[2])
    visit(tree);return result

def acquire_web(record):
    if record["status"] not in {"no_pdf_available","web_acquired"}: return record
    docs=record["webSources"]; doc=docs.get("omManual",{})
    if not doc.get("webhelpManual"): return record
    base=doc["webhelpManual"].rsplit("/",1)[0]+"/"
    stem=f'{record["modelCode"]}-{record["year"]}-web'
    directory=RAW/stem;directory.mkdir(exist_ok=True)
    resources=[]
    try:
        # TOC explicitly references these two official data resources.
        for part in ["index.html","toc.html","data/tocData.json","data/searchData.json"]:
            url=urllib.parse.urljoin(base,part); target=directory/part;target.parent.mkdir(exist_ok=True)
            if not target.exists(): target.write_bytes(fetch(url))
            data=target.read_bytes();resources.append({"url":url,"localPath":target.relative_to(ROOT).as_posix(),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
        toc=flatten_toc(js_json((directory/"data/tocData.json").read_bytes()))
        search=js_json((directory/"data/searchData.json").read_bytes())
        candidates=[]
        for key,node in toc.items():
            content="\n".join(search.get(key,[]))
            topics=[topic for topic,pattern in TOPICS.items() if re.search(pattern,node["title"]+"\n"+content,re.I|re.S)]
            if topics:
                candidates.append({"topicId":key,"title":node["title"],"sourceURL":urllib.parse.urljoin(base,node["path"]),"topics":topics,"reviewStatus":"automated_keyword_candidates_not_semantically_reviewed"})
        # Preserve exact HTML for relevant warning/cluster/TPMS headings in addition to complete text index.
        pages=[n for n in candidates if re.search(r"경고|공기압|고장|과열",n["title"])]
        def html_save(node):
            part=urllib.parse.urlparse(node["sourceURL"]).path.rsplit("/",1)[1]
            target=directory/part
            if not target.exists():target.write_bytes(fetch(node["sourceURL"]))
            data=target.read_bytes()
            return {"url":node["sourceURL"],"localPath":target.relative_to(ROOT).as_posix(),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}
        with cf.ThreadPoolExecutor(max_workers=3) as pool: resources.extend(pool.map(html_save,pages))
        record.update(status="web_acquired",sourceURL=doc["webhelpManual"],webURL=doc["webhelpManual"],publication=doc.get("webhelpPubdate"),documentId=doc.get("webhelpDocId"),localPath=directory.relative_to(ROOT).as_posix(),format="webhelp_text_index_and_warning_html",resources=resources,bytes=sum(r["bytes"] for r in resources),tocTopics=len(toc),searchTextTopics=len(search),missingSearchTopicIds=sorted(set(toc)-set(search)),warningTopicLocators=candidates,checkedUTC=dt.datetime.now(dt.timezone.utc).isoformat(),reviewStatus="acquired_not_approved_for_answers",acquisitionLimit="Complete official search-text/TOC data, index and selected warning HTML; images/styles and every HTML page are not mirrored. Original URLs remain canonical.")
        print("WEB",stem,"topics",len(toc),"text",len(search),"warning candidates",len(candidates),flush=True)
    except Exception as exc:record.update(status="web_error",error=str(exc))
    return record

def main():
    manifest=json.loads((OUT/"hyundai-manifest.json").read_text(encoding="utf-8"))
    # Only one manual at a time, at most 3 HTTP downloads at once.
    manifest["documents"]=[acquire_web(d) for d in manifest["documents"]]
    (OUT/"hyundai-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    data=fetch(LINEUP);(RAW/"current-lineup.json").write_bytes(data)
    lineup=json.loads(data)
    groups=[group for section in lineup["data"] for item in section.get("list") or [] for group in item.get("carTypeList") or []]
    records=[]
    for group in groups:
        for car in group["repnCarInfos"]:
            code=car["carCode"]; projects=MAP.get(code,[])
            row={"salesCode":code,"salesName":car["carName"],"category":group["carTypeCode"],"modelURL":car.get("menuLink2") or "https://www.hyundai.com"+car["menuLink"],"sourceURL":LINEUP,"catalogModelCodes":projects,"currentOfficialListingVerified":True,"customerPurchaseConsultationPossible":car.get("customerPurCnsPossibleYn"),"equipmentApplicabilityReviewed":False}
            matches=[d for d in manifest["documents"] if d["modelCode"] in projects and d.get("latestEvidence",{}).get("isLatest",True)]
            row["manualReferences"]=[{"modelCode":d["modelCode"],"year":d["year"],"status":d["status"],"sourceURL":d.get("sourceURL")} for d in matches]
            imageyear=re.search(r"-(\d{2})my",car.get("carImgPath",""))
            row["salesImageYearHint"]="20"+imageyear[1] if imageyear else None
            row["status"]="excluded_bus_heavy_truck" if group["carTypeCode"] in {"T","B"} else "family_manual_acquired_equipment_review_required" if matches else "unmapped_current_listing"
            if code in SPECIAL:row["variantGap"]="Special/taxi/mobility equipment cannot be assumed covered by family or older special manual; dedicated applicability review required."
            if code=="TS12":row["yearGap"]="Official sales image indicates 2027; latest published manual catalog exposes 2026. Do not apply 2026 manual to 2027 automatically."
            records.append(row)
    catalog=json.loads((OUT/"hyundai-catalog.json").read_text(encoding="utf-8"))
    currentcodes={c for r in records for c in r["catalogModelCodes"]}
    for row in catalog["models"]:
        row["currentSalesVerified"]=row["modelCode"] in currentcodes
        if row["currentSalesVerified"]:row["currentSalesEvidenceURL"]=LINEUP
    (OUT/"hyundai-catalog.json").write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding="utf-8")
    (OUT/"hyundai-current-lineup-coverage.json").write_text(json.dumps({"checkedUTC":dt.datetime.now(dt.timezone.utc).isoformat(),"sourceURL":LINEUP,"landingURL":"https://www.hyundai.com/kr/ko/e/all-vehicles","currentListedVariants":len(records),"inScopeVariants":sum(r["status"]!="excluded_bus_heavy_truck" for r in records),"rows":records},ensure_ascii=False,indent=2),encoding="utf-8")
    print("Coverage",len(records),"in scope",sum(r["status"]!="excluded_bus_heavy_truck" for r in records),"unmapped",sum(r["status"]=="unmapped_current_listing" for r in records),flush=True)

if __name__=="__main__":main()
