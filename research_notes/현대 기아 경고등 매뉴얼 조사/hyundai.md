# 현대 공식 한국어 차량 매뉴얼 조사

## 어떤 차종과 최신 설명서를 확보했는가

### Takeaway
2026-10-28 확인 기준 현대 공식 취급설명서 카탈로그 69항목을 열거하고, 국내 현재 판매 페이지의 60개 판매 변형과 교차했다. 버스·중대형 트럭 16개를 제외한 44개 판매 변형 모두에 해당 차종군 설명서 후보를 연결했으며, 28개 PDF와 7개 웹 설명서의 본문 자료를 실제로 내려받았다. **차종군 연결 44/44는 세부장비·모든 판매연식에 대한 답변 적용 승인 44/44를 뜻하지 않는다.**

### Cited Findings
- 현대 공식 다운로드센터가 전 차종 취급설명서 출처로 ownersmanual.hyundai.com을 연결한다. 한국 locale은 공식 locale 목록에서 `A99 / ko_KR`다. [다운로드센터](https://www.hyundai.com/kr/ko/digital-customer-support/helpdesk/download-center), [locale API](https://ownersmanual.hyundai.com/api/v2/hmc/country-lang-mappings)
- 취급설명서 카탈로그 69항목에는 단종 차량과 버스·트럭도 섞여 있다. 카탈로그에 존재한다는 사실을 현재 판매 증거로 사용하지 않았다. [한국 취급설명서 카탈로그](https://ownersmanual.hyundai.com/api/v2/hmc/models?countryCode=A99&langCode=ko_KR)
- 국내 전체차량 페이지가 사용하는 공개 GNB 모델 API에는 현재 60개 판매 행이 있다. 이 중 승용·SUV·N·전기/수소·MPV·소형상용 44행을 범위에 포함했다. 캐스퍼도 동일 API에 포함된다. [공식 전체차량 페이지](https://www.hyundai.com/kr/ko/e/all-vehicles), [공식 현재 모델 API](https://www.hyundai.com/kr/ko/e/api/common/gnb/menus/M?siteType=H&imageSectionCode=01&includeModelYn=Y)
- 최신 PDF 27개와 앱의 정확한 기존 프로필인 아이오닉 5 2025 PDF 1개를 확보했다. 총 28 PDF, 14,792쪽이다. 최신 PDF 미제공 7종은 **아반떼 CN8/아반떼 HEV CN8KH/그랜저 GN7/그랜저 HEV GN7HEV/넥쏘 NH2/투싼 NX5/투싼 HEV NX5KP의 2027** 웹 설명서로 확보했다. 각 원본 경로는 `hyundai-manifest.json`의 sourceURL 및 metadataURL에 있으며 [공식 카탈로그](https://ownersmanual.hyundai.com/api/v2/hmc/models?countryCode=A99&langCode=ko_KR)에서 시작해 연식 API를 거쳐 얻었다.
- 아이오닉 5 공식 2027 설명서는 최초 2026-06-29, 최종 2026-10-19 게시로 API에 표시된다. 2027이라는 모델연도를 미래 자료로 임의 배제하지 않았다. 별도 2025 설명서는 최초 2024-06-10/최종 2025-04-16이다. [NE1 2027 metadata](https://ownersmanual.hyundai.com/api/v2/hmc/model/owners-manuals?projectCode=NE1&year=2027&langCode=ko_KR&countryCode=A99), [NE1 2025 metadata](https://ownersmanual.hyundai.com/api/v2/hmc/model/owners-manuals?projectCode=NE1&year=2025&langCode=ko_KR&countryCode=A99)
- 확보된 차종군은 ST1, 넥쏘, 스타리아 EV, 아이오닉 5/6/9, 캐스퍼 EV, 코나 EV, 포터 EV, 그랜저/HEV, 쏘나타/HEV/택시, 아반떼/HEV, 스타리아/HEV/특장, 베뉴, 싼타페/HEV, 캐스퍼, 코나/HEV, 투싼/HEV, 팰리세이드/HEV, 포터/특장, 아반떼 N, 아이오닉 5 N/6 N이다. 현재 판매 행에서는 라운지·리무진·킨더·모빌리티·택시·특장을 별도로 유지했다. [현재 모델 목록](https://www.hyundai.com/kr/ko/e/api/common/gnb/menus/M?siteType=H&imageSectionCode=01&includeModelYn=Y)

### Inferences
- 공식 모델명/프로젝트 코드/연식/연료/한국 locale 조합으로 자료 신원을 식별할 수 있다. PDF 첫 페이지가 표지가 아니라 목차인 문서도 있으므로 coverModelMention=false는 곧 오자료라는 뜻이 아니다. 반대로 이미지 파일명이나 검색 스니펫만으로 연식을 확정해서도 안 된다.
- 원문 파일 자체는 변경될 수 있어 체크 시각, SHA256, 공식 최초·수정일과 당시 카탈로그 응답을 함께 보관해야 한다.

### Gaps
- **ST1**: 현재 판매 API 이미지에 2027 표기가 있으나 설명서 카탈로그의 최신 자료는 2026이다. 2027 차량에 2026 자료를 자동 적용할 수 없다. 판매 이미지 연도는 보조 힌트이며 별도 공식 본문 적용범위 확인이 필요하다. [ST1 판매](https://www.hyundai.com/kr/ko/e/vehicles/st1/intro), [ST1 공식 2026 매뉴얼 메타데이터](https://ownersmanual.hyundai.com/api/v2/hmc/model/owners-manuals?projectCode=A01&year=2026&langCode=ko_KR&countryCode=A99)
- 그랜저 택시·스타리아 리무진/킨더/모빌리티·포터 EV 특장 등 9개 판매 변형은 차종군 자료만 연결했다. 전용 장비 또는 다른 파워트레인의 특장 설명서를 그대로 적용할 수 없다. `variantGap`에 기록했다. 스타리아 라운지도 사양 적용은 실제 본문과 VIN/트림 확인 단계가 남는다. [현재 목록](https://www.hyundai.com/kr/ko/e/api/common/gnb/menus/M?siteType=H&imageSectionCode=01&includeModelYn=Y)
- 7개 웹 설명서는 전체 TOC 및 공식 전체 검색본문 데이터와 관련 경고 원문 HTML을 보관했다. 모든 이미지·CSS·모든 HTML 페이지를 오프라인 복제한 완전한 웹사이트는 아니다. 원본 URL이 정본이다. [예: 그랜저 2027 웹 설명서](https://ownersmanual.hyundai.com/full_webhelp/GN7/2027/ko_KR/index.html)
- 제외: Genesis, 버스, 중대형 트럭, 해외시장, 모든 과거 연식. 과거 카탈로그 항목도 삭제하지 않고 제외/미수집 이유를 명시했다. 현재 판매 변형과의 교차 후 2024 이하 자료가 필요한 현행 모델은 이번 44행에서 발견되지 않았다.

## 경고등별 대처 근거는 어떻게 구분했는가

### Takeaway
모든 PDF에 18개 경고 주제의 페이지 후보를 만들고, 웹 7종에는 관련 본문 항목 URL 후보를 만들었다. 이것은 검색용 위치 색인이며 자동 의미 검토나 정비 지침 승인 결과가 아니다. 별도의 6개 예시만 출처를 직접 읽고 구분 조건을 정리했다.

### Cited Findings
- **아이오닉 5 2025 TPMS**: 공기압 확인/필요 시 보충과 약 1분 점멸 뒤 점등 시 점검을 구분한다. PDF 실제 138쪽, 인쇄 134쪽을 렌더링해 표를 시각 확인했다. 2027판은 같은 인쇄 134쪽이 PDF 실제 142쪽이므로 두 페이지 체계를 혼용하면 안 된다. [2025 원문](https://ownersmanual.hyundai.com/full_pdf/NE1/2025/ko_KR#page=138), [2027 원문](https://ownersmanual.hyundai.com/full_pdf/NE1/2027/ko_KR#page=142)
- **아이오닉 5 2025 파워다운**: 배터리 상태·온도·구동계 보호 조건과 서비스 경고 동시 점등을 구분해야 한다. PDF 실제 136쪽/인쇄 132쪽의 표를 시각 확인했다. [원문](https://ownersmanual.hyundai.com/full_pdf/NE1/2025/ko_KR#page=136)
- **아이오닉 5 2027 12V 충전 경고**는 충전 계통 점검 대상이다. 고전압 배터리 잔량 부족과 같은 의미로 처리하면 안 된다. PDF 실제 142쪽/인쇄 134쪽을 시각 확인했다. [원문](https://ownersmanual.hyundai.com/full_pdf/NE1/2027/ko_KR#page=142)
- **그랜저 2027 오일 압력**은 주행 중 점등 시 안전 정차와 오일량 확인을 안내한다. **ABS+브레이크 동시 점등**은 EBD 조건으로 별도 취급한다. 해당 웹 원문과 공식 검색본문을 직접 읽었다. [그랜저 경고등 (6), (9), (10)](https://ownersmanual.hyundai.com/full_webhelp/GN7/2027/ko_KR/cluster-check_warn_indic_lights-check_warn_and_ind_lights.html)
- **넥쏘 2027 수소 누출**은 빨간색 지속 시 안전 정차·견인 점검, 주황색 지속 시 누출 감지 센서 점검으로 구분한다. 동일 ON 상태라도 색상에 따라 조치가 달라진다. [넥쏘 경고등 (2)](https://ownersmanual.hyundai.com/full_webhelp/NH2/2027/ko_KR/id23C4LH00HL7.html)

### Inferences
- BLINK 한 번 수신은 약 1분 점멸 후 점등이라는 시간 패턴을 증명하지 않는다. 과거 서로 다른 시각의 ABS/BRAKE를 동시 경고라고 판단해서도 안 된다.
- 현재 앱의 ON/BLINK만으로 넥쏘 색상별 조치를 선택할 수 없으므로 필요한 컨텍스트가 없는 질문은 확인 질문 또는 제한된 근거 안내로 처리해야 한다.
- RAG에는 차종·프로젝트 코드·연식·한국시장·파워트레인·사양과 관측 색상/지속시간/동시경고/메시지를 필터와 조건으로 보존해야 한다.

### Gaps
- 자동 페이지 후보는 목차·중복 언급·주행보조 설명도 포함한다. 후보 페이지 수를 서로 다른 경고등 수나 검토된 규칙 수로 제시하면 안 된다.
- 6개 source-reviewed 예시는 자동차 전문가 검토가 없고 앱에 활성화하지 않았다. 전체 35문서의 모든 경고 조치 규칙에 대한 의미 검수는 후속 작업이다.
- 일부 PDF 텍스트에서는 경고/주의 아이콘 전용 글꼴이 다른 문자로 추출된다. 검토 시 PNG와 원문을 함께 확인해야 한다. 이미지 아이콘 자체 임베딩이나 OCR은 이번 수집에 포함되지 않는다.

## 파일과 재현·검증 결과는 무엇인가

### Takeaway
로컬 원본은 `.local/manual-corpus/2026-10-28/hyundai/`에 보관하고 Git에는 목록·출처·위치 색인·조사 스크립트만 둔다. 독립 무결성 검사 35/35가 통과했으며 현재 판매 목록 범위 44행 중 미연결 0행이다. 해당 수치는 현재 실행으로 생성한 `hyundai-validation.json`에 기록했다.

### Cited Findings
- 원본 합계 819,130,038 bytes: PDF 28개/14,792쪽, 웹 7개/3,696 TOC 항목. 모든 웹 TOC 항목에 검색본문이 대응한다. SHA256·크기·PDF signature·페이지 수·한국어 추출·페이지 범위·웹 항목 해시 검증 35건 전부 통과했다. 이는 연구 산출물의 직접 검증이며 외부 통계가 아니다. [검증 결과](../../data/manual-research/2026-10-28/hyundai-validation.json)
- tracked 자료: `hyundai-catalog.json`(69항목), `hyundai-current-lineup-coverage.json`(현재60/범위44행), `hyundai-manifest.json`(35문서 및 주제 위치 후보), `hyundai-reviewed-examples.json`(6개 직접 확인 예시), `hyundai-validation.json`.
- 공식 다운로드 및 웹 메타데이터의 publication은 `firstdate/lastdate` 원문 값을 유지한다. 수집일과 출판일을 구분한다. [공식 ownersmanual](https://ownersmanual.hyundai.com/)

### Inferences
- 재현 시 앱 환경과 분리해 아래 명령을 순서대로 실행하는 것이 좋다. 추가 도구는 PyMuPDF 2.0이며 앱 pyproject/uv.lock은 변경하지 않았다. 최초 조사에서는 backend venv에 pypdf/PyMuPDF를 설치했지만, 아래 uv 격리 실행은 앱 의존성을 수정하지 않는다.

```powershell
uv run --no-project --with pymupdf==2.0 python scripts/manuals/hyundai_acquire.py
uv run --no-project --with pymupdf==2.0 python scripts/manuals/hyundai_web_and_coverage.py
uv run --no-project --with pymupdf==2.0 python scripts/manuals/hyundai_validate.py
```

### Gaps
- 재실행 시 다운로드 파일은 캐시 재사용한다. 새 수정판 확보를 위한 날짜별 스냅샷 경로와 HTTP 재검증 정책은 다음 수집 버전에서 추가해야 한다. 현재 스크립트의 날짜별 저장 경로는 2026-10-28로 고정되어 있다.
- 원문 재배포 권한을 확인한 것은 아니다. 원본·추출 전문은 Git에서 제외하고, 앱에 공개 제공할 인용 길이·출처 표시·원문 사용 권한은 배포 전에 별도로 확정해야 한다. [현대 웹 설명서의 법적 고지](https://ownersmanual.hyundai.com/full_webhelp/GN7/2027/ko_KR/owner-legal_notices.html)
