"""Record source-reviewed supplement findings. Raw OCR remains local and unapproved."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/manual-review/2026-10-28'
RAW = ROOT / '.local/manual-review/2026-10-28/audit'
PDF = ROOT / '.local/manual-corpus/2026-10-28/kia/KA4HI_2025/owners-manual.pdf'
URL = 'https://ownersmanual.kia.com/full_pdf/KA4HI/2025/ko_KR'
HASH = hashlib.sha256(PDF.read_bytes()).hexdigest()

def save(name, value):
    (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')

def rule(key, pages, topic, conditions, actions, prohibitions=None, restart=None):
    return dict(ruleId='AUDIT-KA4HI2025-'+key, documentIds=['kia_KA4HI_2025'], topic=topic,
        sources=[dict(URL=URL, hash=HASH, locator={'pdfPages':pages,'printedPages':[p-1 for p in pages]})],
        conditions=conditions, orderedActions=actions, prohibitions=prohibitions or [], restartCriteria=restart or [],
        requiredContext=['전용 장비 장착 여부','2025 하이리무진 및 파워트레인'],
        reviewStatus='SOURCE_REVIEWED', reviewMethod='OCR 전체 열람 및 해당 표/핵심 절 이미지 대조',
        reviewer='AI', runtimeApproved=False, sdkSignal=None, scope='special_equipment_not_instrument_cluster')

rules=[
 rule('FILTER',[39,40,41],'공기청정기 교체 알림', ['적색 잎 LED 3회 점멸과 알림 3회'],
      ['전원 종료 후 전용 필터를 교체한다.','그릴을 정렬하고 표시부를 5초 눌러 교체 타이머를 초기화한다.'],['주행 중 조작 금지']),
 rule('AIR-QUALITY',[39],'공기 상태 색상', ['파랑·초록·주황·빨강의 공기 상태 표시'],
      ['공기 상태 참고 표시로 구분한다.'],['차량 계기판 고장이나 필터 교체 경고와 혼동하지 않는다.']),
 rule('AIR-POWER',[41],'공기청정기 자동 전원', ['차량 전압 저하로 꺼짐'],
      ['기타 이상이면 사용을 중단하고 지정 고객센터에 문의한다.'],['임의 분해·개조 금지'],['전압 회복 시 자동 재작동; 재시동 후 오토 모드']),
 rule('CUP-COLOR',[31,32],'컵홀더 표시', ['파랑 냉장·주황 온장·소등 정지'],
      ['정상 모드 표시로 분류한다.'],['뜨거운 표면 접촉·흡배기구 막음 금지']),
 rule('FRIDGE',[35],'냉온장고 표시와 경보', ['파랑 냉장·빨강 온장; 열린 상태 1분 후 알림'],
      ['문 열림 알림을 고장 경고와 구분한다.','냉온 전환에는 약 5분 간격을 둔다.']),
 rule('SEAT-RESET',[18],'리무진 시트 작동 이상', ['시트 조절 기능이 정상 작동하지 않음'],
      ['안전 정차·키 또는 시동 ON 후 슬라이딩 도어를 연다.','후방 슬라이딩·전방 리클라이닝·상향 레그 서포트를 각각 15초 작동한다.','좌우 릴렉션 버튼을 함께 약 5초 눌러 초기화한다.'],
      ['이동 경로에 신체·물건을 두지 않는다.'],['약 4분 자동 초기화; 중지 버튼·도어 모두 닫힘·OFF·앱 중지 요청 시 중단']),
 rule('EQUIPMENT-FAILURE',[47,48,50],'전용 실내 장치 고장', ['컵홀더·모니터·컨트롤러·조명 이상'],
      ['지정 서비스센터/협력사에서 점검한다.','확인된 이상은 정상 정비 후 운행한다.'],['표의 가능한 원인을 관측된 확정 고장으로 단정하지 않는다.']),
 rule('DMB',[50],'DMB 수신 이상', ['수신 또는 안테나 연결 관련 이상'],
      ['수신 가능한 지상 지역에서 채널을 다시 검색한다.']),
 rule('MAINTENANCE-SAFETY',[47],'점검 작업 안전', ['점검·정비'],
      ['평탄한 장소에서 주차브레이크와 고임목으로 고정한다.','탑승자가 없는 상태에서 작업한다.']),
]

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    save('audit-supplement-rules.json', {'version':1,'scope':'2025 KA4HI 전용 표시/고장 조치; 기본 계기판 아님',
      'runtimeApproved':False,'rules':rules,
      'ocr':{'engine':'Tesseract 5.4 kor+eng tessdata_fast','pages':53,'rawPath':str((RAW/'hilimousine-ocr.json').relative_to(ROOT)),
             'quality':'자동 OCR만으로 승인하지 않음; 표·회전된 글자 인식 오류 존재',
             'visuallyCheckedPdfPages':[2,11,18,20,21,31,35,39,40,41,47,48,49,50]},
      'manualRole':'supplement','baseManualYear':2025,'powertrainEvidence':'PDF 11쪽 HEV 제원 명시; API ICE는 배타적 적용 필터가 아님',
      'scopeExclusions':['스마트 모니터·마사지기 등의 일반 조작 절은 계기판 경고 대처 목록과 구분','전문가 승인 및 런타임 답변 활성화 없음']})
    bases=[]
    for code in ['KA4','KA4KH']:
        d=json.loads((RAW/(code+'-2025-acquired.json')).read_text(encoding='utf8'))
        bases.append(d)
    save('audit-base-manual-acquisition.json', {'documents':bases,'runtimeApproved':False,
       'meaning':'동일 연식 기본 자료 확보. 수집이 의미 검토 완료를 뜻하지 않음.'})
    save('audit-errata.json', {'previousSnapshot':'data/manual-research/2026-10-28', 'corrections':[
      {'documents':['HYUNDAI-US4SV-2026','HYUNDAI-HRSV-2025'],'previousClaim':'현대 PDF 28개 모두 주 취급설명서',
       'correctedClaim':'US4SV와 HRSV는 특장 장비 설명서. 기존 수집 62개 문서 수는 그대로지만 기본차 자료 대체 불가.',
       'sources':[{'URL':'https://ownersmanual.hyundai.com/full_pdf/US4SV/2026/ko_KR','pdfPages':[1,3]},
                  {'URL':'https://ownersmanual.hyundai.com/full_pdf/HRSV/2025/ko_KR','pdfPages':[1,3]}]},
      {'document':'kia_KA4HI_2025','previousClaim':'OCR 필요, 기본차 2025 연결 미확보',
       'correctedClaim':'53쪽 OCR 및 14쪽 시각 대조 완료, KA4/KA4KH 2025 공식 웹 추가 확보. 기본차 대처의 의미 검수는 별도.',
       'source':URL},
      {'issue':'현대 판매명 인코딩 오탐','result':'UTF-8 재검사에서 저장 salesName U+FFFD 0개, 원 API 대체문자 0개. 터미널 출력 문제였으므로 원 데이터 수정 없음.'}
    ]})
    print('supplement rules',len(rules),'base documents',len(bases))

if __name__=='__main__':main()
