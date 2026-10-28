"""Applicability evidence is narrower than full trim approval."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/manual-research/2026-10-28'
OUT=ROOT/'data/manual-review/2026-10-28'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 rows=[]
 h=read(DATA/'hyundai-current-lineup-coverage.json')
 for r in h['rows']:
  if r['salesCode'] not in ['US41','M5A0','US46','US36','US45','GN13','US32','US35','M5A4']:continue
  note='기본 계열 문서 확보는 현재 판매 특수 사양의 장비 적용 확인과 다름.'
  state='EXACT_EQUIPMENT_APPLICABILITY_PENDING'
  if r['salesCode'] in ['US36','US45']:
   note='US4SV 2026 특장 문서에 킨더 장이 명시되지만 판매 이미지의 2027 표기와 정확한 장비/연식 매칭은 미확정.'
   state='DEDICATED_CONTENT_FOUND_YEAR_MATCH_PENDING'
  if r['salesCode'] in ['US41','US46']:
   note='US4SV 2026 특장 목차는 킨더·휠체어 리프트·구급차·캠퍼이며 리무진 전용 문서라고 단정할 수 없음.'
  if r['salesCode'] in ['M5A0','M5A4']:
   note='HRSV 2025 상부 특장 설명서는 탑차·냉동·윙바디·파워게이트·덤프 등을 포함한다. 기본 2026 HR/HREV와 연식·동력 장비 일치 확인은 미해결.'
   state='DEDICATED_CONTENT_FOUND_YEAR_MATCH_PENDING'
  rows.append({'brand':'hyundai','salesCode':r['salesCode'],'salesName':r['salesName'],'salesURL':r['modelURL'],
   'officialListingURL':r['sourceURL'],'manualReferences':r['manualReferences'],'status':state,'finding':note,
   'fullVariantApproved':False,'runtimeApproved':False})
 k=read(DATA/'kia_sales_coverage.json')
 for r in k['products']:
  if r['coverage_status']!='shared_candidate':continue
  code=r['manifest_document_ids'][0].replace('kia_','')
  p=ROOT/'.local/manual-corpus/2026-10-28/kia'/code/'toc-links.json'
  toc=read(p) if p.exists() else {}
  suffix=r['url'].rsplit('/',1)[1]
  term=None
  if suffix.startswith('ev') and suffix.endswith('-gt'):term='GT 전용'
  elif suffix=='pv5-openbed':term='오픈베드'
  elif suffix=='pv5-prime':term='프라임'
  elif suffix in ['pv5-wav','pv5-wav-taxi']:term='WAV'
  elif suffix in ['pv5-passenger','pv5-taxi','pv5-taxi-122']:term='패신저'
  elif suffix in ['pv5-cargo','pv5-cargo-compact']:term='카고'
  hits=[{'URL':u,'title':t} for u,t in toc.items() if term and term in t]
  state='DEDICATED_EQUIPMENT_SOURCE_NOT_IDENTIFIED'
  note='검토한 공식 메타데이터/목차에서 전용 장을 특정하지 못함. 미발행 또는 적용 불가로 단정하지 않음.'
  if hits:
   state='EXPLICIT_VARIANT_CONTENT_FOUND'
   note='공식 목차에 해당 사양 전용 내용이 명시됨. 모든 연식/옵션/경고 대처 승인과는 별개.'
   if suffix in ['pv5-taxi','pv5-taxi-122','pv5-wav-taxi','pv5-cargo-compact']:
    state='FAMILY_CONTENT_FOUND_EXACT_CONFIGURATION_PENDING'
    note='패신저/WAV/카고 내용은 명시되지만 택시 좌석 배열 또는 카고 컴팩트 전용 적용성은 아직 입증하지 못함.'
  if suffix=='carnival-hi-limousine':
   state='EXACT_2025_BASE_AND_SUPPLEMENT_ACQUIRED'
   note='KA4HI 2025 53쪽 특장 설명서 OCR·핵심 14쪽 시각 대조 완료. 정확한 KA4/KA4KH 2025 기본 설명서 추가 확보. 현재 판매분 전체 연식 승인은 아님.'
   hits=[{'URL':'https://ownersmanual.kia.com/full_pdf/KA4HI/2025/ko_KR','title':'하이리무진 2025 전용 설명서'}]
  rows.append({'brand':'kia','salesName':r['label'].strip(),'salesURL':r['url'],'manualDocumentIds':r['manifest_document_ids'],
   'status':state,'finding':note,'explicitContents':hits,'tocSourceHash':sha(p) if p.exists() else None,
   'fullVariantApproved':False,'runtimeApproved':False})
 catalog=read(DATA/'hyundai-catalog.json')
 st=next(x for x in catalog['models'] if x['modelCode']=='A01')
 year={'model':'ST1','sourceURL':st['detailURL'],'catalogYears':st['availableYears'],'latestPublishedCatalogYear':st['latestCatalogYear'],
  'salesImageYearHint':'2027','salesModelYearConfirmed':False,
  'status':'2027_NOT_IN_CHECKED_OFFICIAL_CATALOG; SALES_YEAR_UNCONFIRMED',
  'note':'판매 이미지 파일명 2027은 실제 차량 연식 확인을 대신하지 않음. 공식 ST1 소개 HTML은 SPA로 연식을 본문에서 확인하지 못함. 2026 안내를 2027 자동 적용 금지.',
  'productURL':'https://www.hyundai.com/kr/ko/e/vehicles/st1/intro','productHtmlHash':sha(ROOT/'.local/manual-review/2026-10-28/audit/st1-product.html'),
  'runtimeApproved':False}
 out={'version':1,'runtimeApproved':False,'denominator':{'hyundaiSpecialSalesRows':9,'kiaSpecialSalesRows':22,'totalSpecialSalesRows':31,'separateYearGap':1},
  'rows':rows,'yearGaps':[year],'counts':{s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})},
  'interpretation':'확인/미확인 사양은 기본 설명서 수와 별개. 전용 내용 존재, 정확한 연식 적용, 의미 검토, 런타임 승인 네 단계를 분리.'}
 assert len(rows)==31
 (OUT/'audit-variant-applicability.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(out['counts']))
if __name__=='__main__':main()
