"""Acquire official Korean Hyundai manuals. Raw copyrighted files stay in ignored .local.

Run: backend/.venv/Scripts/python.exe scripts/manuals/hyundai_acquire.py
Requires PyMuPDF (research tooling only; not an app dependency).
Endpoints are discovered from the official ownersmanual site's public frontend.
Catalog membership is not proof of current domestic sales or exact trim applicability.
"""
from __future__ import annotations
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request
import pymupdf

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/manual-research/2026-10-28"
RAW = ROOT / ".local/manual-corpus/2026-10-28/hyundai"
BASE = "https://ownersmanual.hyundai.com"
COUNTRY, LANG = "A99", "ko_KR"
CATALOG_URL = BASE + f"/api/v2/hmc/models?countryCode={COUNTRY}&langCode={LANG}"
LANDING = "https://www.hyundai.com/kr/ko/digital-customer-support/helpdesk/download-center"
TOPICS = {
    "TPMS": r"공기압|TPMS",
    "ABS": r"ABS|안티록",
    "BRAKE_EBD": r"브레이크\s*경고|제동력\s*분배|EBD|회생\s*제동\s*경고",
    "OIL_PRESSURE": r"오일\s*압력|오일\s*경고",
    "CHARGING_12V": r"충전\s*경고|보조\s*배터리",
    "COOLANT": r"냉각수\s*수온|엔진\s*과열|냉각수\s*경고",
    "ENGINE_MIL": r"엔진\s*경고|엔진\s*정비\s*지시|MIL",
    "ESC": r"차체\s*자세\s*제어|ESC\s*작동|ESC\s*경고",
    "EPS": r"전동식\s*파워\s*스티어링|EPS|MDPS",
    "AIRBAG": r"에어백\s*경고",
    "MASTER_WARNING": r"통합\s*경고",
    "EV_SERVICE": r"서비스\s*경고|전기차\s*시스템|전기\s*자동차\s*시스템",
    "POWER_DOWN": r"파워\s*다운|출력\s*제한|출력\s*저하",
    "HV_BATTERY": r"고전압\s*배터리\s*충전량|구동용\s*배터리\s*충전량|배터리\s*잔량\s*경고",
    "HEV_SYSTEM": r"하이브리드\s*시스템.*경고|하이브리드\s*시스템.*점검",
    "FCEV_HYDROGEN": r"수소\s*누출|연료전지.*경고|수소\s*부족",
    "DPF_GPF_SCR": r"매연\s*필터|요소수|배출가스\s*경고|DPF|GPF",
    "EPB": r"EPB|전자식\s*파킹\s*브레이크\s*경고",
}

def fetch(url: str) -> bytes:
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "CHECKMATE-manual-research/1.0"}), timeout=90) as response:
                return response.read()
        except Exception:
            if attempt == 2: raise
            time.sleep(1 + attempt)

def get_json(url: str, save: str):
    data = fetch(url)
    (RAW / save).write_bytes(data)
    return json.loads(data)

def detail(model):
    code = model["projCode"]
    url = BASE + "/api/v3/hmc/model?" + urllib.parse.urlencode({"modelName":model["langModelName"],"countryCode":COUNTRY,"langCode":LANG})
    entry = {"model":model["langModelName"], "modelCode":code, "category":model["modelType"], "catalogURL":CATALOG_URL,"detailURL":url,"countryCode":COUNTRY,"language":LANG,"currentSalesVerified":False}
    if model["modelType"] in {"BUS","TRUCK"} or code == "BH":
        entry.update(status="excluded_scope", reason="bus/heavy truck/Genesis")
        return entry, []
    try:
        data = get_json(url, f"{code}-years.json")
        years = sorted(data.get("years") or [], reverse=True)
        entry["availableYears"] = years
        if not years:
            entry["status"] = "no_years_in_official_catalog"
            return entry, []
        latest = years[0]
        entry["latestCatalogYear"] = latest
        # Keep historical entries visible, while acquiring contemporary models first.
        if int(latest) < 2025:
            entry.update(status="historical_catalog_not_acquired", reason="latest catalog model year before 2025; not asserted current sales")
            return entry, []
        selected = [latest] + (["2025"] if code == "NE1" and latest != "2025" else [])
        entries = []
        for year in selected:
            for version in data.get("yearModels",{}).get(year,[]):
                actual = version["projCode"]
                api = BASE + "/api/v2/hmc/model/owners-manuals?" + urllib.parse.urlencode({"projectCode":actual,"year":year,"langCode":LANG,"countryCode":COUNTRY})
                docs = get_json(api, f"{actual}-{year}-manuals.json")
                found = 0
                for kind, doc in docs.items():
                    if not doc or not doc.get("pdfManual"): continue
                    if kind == "quickGuide": continue
                    found += 1
                    entries.append({"brand":"Hyundai","model":version["modelName"],"modelCode":actual,"year":year,"sourceLabelYear":year,"powertrain":version.get("fuel"),"market":"KR","language":LANG,"countryCode":COUNTRY,"manualKind":kind,"sourceURL":doc["pdfManual"],"landingURL":LANDING,"catalogURL":CATALOG_URL,"metadataURL":api,"webURL":doc.get("webhelpManual"),"tocURL":doc.get("webhelpToc"),"publication":doc.get("pdfPubdate"),"documentId":doc.get("pdfDocId"),"latestEvidence":{"availableYears":years,"latestCatalogYear":latest,"isLatest":year==latest},"reviewStatus":"acquired_not_approved_for_answers","variantUncertainty":"Official model/year/fuel metadata; trim and equipment applicability requires content review","status":"pending"})
                if not found:
                    entries.append({"brand":"Hyundai","model":version["modelName"],"modelCode":actual,"year":year,"sourceLabelYear":year,"powertrain":version.get("fuel"),"market":"KR","language":LANG,"metadataURL":api,"status":"no_pdf_available","webSources":docs})
        entry["status"] = "catalog_enumerated"
        return entry, entries
    except Exception as exc:
        entry.update(status="catalog_error",error=str(exc))
        return entry, []

def acquire(record):
    if record["status"] != "pending": return record
    stem = f'{record["modelCode"]}-{record["year"]}-{record["manualKind"]}'
    path = RAW / f"{stem}.pdf"
    try:
        if not path.exists(): path.write_bytes(fetch(record["sourceURL"]))
        data = path.read_bytes()
        if not data.startswith(b"%PDF-"): raise ValueError("Not a PDF signature")
        with pymupdf.open(path) as pdf:
            pages = [page.get_text() for page in pdf]
            if not pages: raise ValueError("Empty PDF")
            (RAW / f"{stem}-pages.json").write_text(json.dumps(pages,ensure_ascii=False),encoding="utf-8")
            warnings = []
            for topic, pattern in TOPICS.items():
                hits = [i+1 for i,text in enumerate(pages) if re.search(pattern,text,re.I|re.S)]
                warnings.append({"topic":topic,"pdfPages1Based":hits,"matchCountPages":len(hits),"reviewStatus":"automated_keyword_candidates_not_semantically_reviewed"})
            cover = "\n".join(pages[:5])
            record.update(pages=len(pdf),pdfMetadata=pdf.metadata,hasKoreanText=bool(re.search("[가-힣]",cover)),coverModelMention=record["model"].replace(" ","") in cover.replace(" ",""),topicLocators=warnings)
        record.update(status="downloaded",localPath=path.relative_to(ROOT).as_posix(),textPagesPath=(RAW/f"{stem}-pages.json").relative_to(ROOT).as_posix(),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),checkedUTC=dt.datetime.now(dt.timezone.utc).isoformat())
        print(f"DOWNLOADED {stem}: {record['pages']} pages, {len(data)} bytes",flush=True)
    except Exception as exc:
        record.update(status="download_error",error=str(exc))
        print(f"FAILED {stem}: {exc}",flush=True)
    return record

def main():
    RAW.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
    catalog=get_json(CATALOG_URL,"models.json")
    models=[m for group in catalog.values() for m in group]
    entries,documents=[],[]
    with cf.ThreadPoolExecutor(max_workers=3) as pool:
        for entry,docs in pool.map(detail,models): entries.append(entry);documents.extend(docs)
    (OUT/"hyundai-catalog.json").write_text(json.dumps({"checkedUTC":dt.datetime.now(dt.timezone.utc).isoformat(),"sourceURL":CATALOG_URL,"selectionRule":"Latest official Korean catalog year >=2025 plus exact 2025 Ioniq5; all other catalog entries accounted as historical or excluded. This does not certify current sales.","models":entries},ensure_ascii=False,indent=2),encoding="utf-8")
    with cf.ThreadPoolExecutor(max_workers=3) as pool: documents=list(pool.map(acquire,documents))
    report={"checkedUTC":dt.datetime.now(dt.timezone.utc).isoformat(),"documents":documents}
    (OUT/"hyundai-manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"catalogModels":len(entries),"documents":len(documents),"downloaded":sum(d['status']=='downloaded' for d in documents),"bytes":sum(d.get('bytes',0) for d in documents)},ensure_ascii=False),flush=True)

if __name__=="__main__": main()
