# 기아 최신 한국어 경고등 매뉴얼

## 어떤 자료를 실제로 확보했는가

### Takeaway
기아 공식 국내 매뉴얼 카탈로그 41항목을 조사하고 현행 기본 차군에 연결되는 최신 27문서의 원문을 확보했다. 26문서는 HTML 경고·응급·점검 관련 절이며 1문서는 하이리무진 전용 보충 PDF다. 완전한 전 차종·전 사양 매뉴얼 미러나 production 검수 완료로 표현하면 안 된다.

### Cited Findings
- 공개 API는 한국 시장 A99, 한국어 ko_KR을 사용하며 차군별 공개 연식·프로젝트 코드·동력계 레이블을 제공한다. 공식 사이트가 배포한 JavaScript에서 endpoint를 확인했다. [카탈로그](https://ownersmanual.kia.com/api/v2/kia/models?countryCode=A99&langCode=ko_KR), [로케일](https://ownersmanual.kia.com/api/v2/kia/current-locale)
- 실제 확보 최신 연식은 K5/K8/모닝/레이/스포티지 ICE/쏘렌토/카니발/타스만/PV5/EV3/EV4/EV6/EV9/K5 HEV/K8 HEV/니로/레이 EV/쏘렌토 HEV/카니발 HEV 2027, K9/셀토스 SP2·SP3/봉고 ICE·EV/EV5/스포티지 HEV 2026, 하이리무진 2025다. 각 선택은 해당 `model` API의 최고 공개 연식이다. [K5 연식](https://ownersmanual.kia.com/api/v3/kia/model?modelName=K5&countryCode=A99&langCode=ko_KR), [EV3 연식](https://ownersmanual.kia.com/api/v3/kia/model?modelName=EV3&countryCode=A99&langCode=ko_KR), 모든 개별 출처는 `kia_catalog.json`에 기록했다.
- 2027 EV3 원문의 공식 최초·최종 게시일은 2026-02-06이다. 모델연식과 게시일을 분리해야 한다. [메타데이터](https://ownersmanual.kia.com/api/v2/kia/model/owners-manuals?countryCode=A99&langCode=ko_KR&projectCode=SV1&year=2027), [목차](https://ownersmanual.kia.com/full_webhelp/SV1/2027/ko_KR/toc.html)
- 매뉴얼 본문은 대처법이 부모 소개 절이 아닌 하위 절에 있는 경우가 있다. 셀토스 TPMS 부모는 개요이고 저압 조치와 시스템 이상은 별도 페이지다. [부모](https://ownersmanual.kia.com/full_webhelp/SP3/2026/ko_KR/topics/t00938.html), [저압 조치](https://ownersmanual.kia.com/full_webhelp/SP3/2026/ko_KR/topics/t00940.html), [시스템 이상](https://ownersmanual.kia.com/full_webhelp/SP3/2026/ko_KR/topics/t00941.html)
- 로컬 검증: HTML 토픽 2,637개 + 최상위 목차 26개 + PDF 1개 = 총 2,664자산, 171,100,205바이트. 해시·크기·파일 시그니처 실패 0개, 미해결 수집 오류 0개. 이는 로컬 실행 증거이며 `kia_validation.json`에 파일별 결과를 남겼다.

### Inferences
- 한국어 경고 근거를 모으는 출발점으로 API 카탈로그와 해당 하위 절을 연결하면 모델/연식이 없는 검색 결과보다 추적성이 높다.
- HTML 원문에 경고등 이미지가 포함돼도 이번에 이미지 자체를 내려받은 것은 아니므로 UI 아이콘 매칭에는 추가 검수가 필요하다.

### Gaps
- 26개 웹매뉴얼은 선택된 경고·응급·점검 절 수집이며 모든 페이지/이미지/CSS를 가진 오프라인 미러가 아니다.
- 하이리무진 53쪽 PDF는 텍스트층이 없어 OCR이 필요하다. 표지/PDF 2쪽을 실제 이미지로 확인했으며, 2쪽은 하이리무진 전용 부품 설명서라 기본 차량 설명서를 함께 보라고 명시한다. 2025 기본 카니발 정확 연식·동력계 문서 연결은 아직 미완료다. 공식 PDF URL과 해시는 `kia_manifest.json`의 `kia_KA4HI_2025`에 있다.
- 카탈로그에 남아 있는 단종 차종 전체 연식은 이번 현재 차군 범위에서 다운로드하지 않았다. 다만 목록·최신연식·제외 사유는 남겼다.

## 현재 판매 제품 범위는 얼마나 대응되는가

### Takeaway
공식 판매 페이지는 42개 제품행을 보여 주며 버스 1행을 제외하면 41행이다. 기본 차군 일치 19행과 추가 적용 확인이 필요한 22행을 구분했다. 제품행, 파워트레인 문서, 모델 연식은 서로 다른 분모다.

### Cited Findings
- EV 페이지에는 기본 EV와 GT, 봉고 EV 특장 제품이 분리돼 있다. [EV 제품](https://www.kia.com/kr/vehicles/ev)
- 승용에는 모닝·레이·K5·K8·K9, RV에는 셀토스·니로·스포티지·쏘렌토·타스만·카니발·하이리무진이 있다. [승용](https://www.kia.com/kr/vehicles/sedan), [RV](https://www.kia.com/kr/vehicles/rv)
- 상용에는 택시·PV5 택시/특수구성·봉고 특장·타스만 오픈베드·그랜버드, PBV에는 패신저·카고 롱/컴팩트·WAV·프라임·오픈베드가 분리돼 있다. [상용](https://www.kia.com/kr/vehicles/commercial), [PBV](https://www.kia.com/kr/vehicles/pbv)
- 셀토스 SP3 카탈로그 fuel 레이블은 ICE지만 실제 목차 제목은 ICE_PHEV_HEV이고 HEV 운전/경고 절이 존재한다. [셀토스 연식](https://ownersmanual.kia.com/api/v3/kia/model?modelName=%EC%85%80%ED%86%A0%EC%8A%A4&countryCode=A99&langCode=ko_KR), [SP3 목차](https://ownersmanual.kia.com/full_webhelp/SP3/2026/ko_KR/toc.html), [HEV 경고](https://ownersmanual.kia.com/full_webhelp/SP3/2026/ko_KR/topics/t00536.html)

### Inferences
- 단일 `fuel` API 문자열을 그대로 적용 필터로 쓰면 셀토스 HEV 근거를 누락할 수 있다. 문서/절 단위 적용 조건을 함께 보유해야 한다.
- GT/택시/특장차를 기본 차종과 자동 동일시하면 장비와 조치의 차이를 놓칠 수 있다. 판매행에 연결한 문서 ID는 검수 후보이지 적용 확정이 아니다.

### Gaps
- 22개 판매행은 `shared_candidate`: GT, PV5 차체/좌석 구성, 봉고 특장, 택시, 하이리무진 등. 필요한 보충 자료와 연식/사양 적용을 확인해야 한다.
- `exact_confirmed` 19행은 공식 모델 차군의 일치 의미이며 모든 트림이나 전체 대처 문구의 서비스 승인 의미가 아니다.
- `PHEV_HEV`라는 문서 그룹 레이블만으로 국내 PHEV 판매를 주장하지 않는다.

## 앱 경고 안내에서 어떤 분기와 근거를 보존해야 하는가

### Takeaway
원문을 읽어 6개 대표 사례를 검수했다. ON/BLINK만으로는 확정할 수 없는 점멸 시간, 시동 직후 여부, 동시 경고, 정확한 표시등 및 파워트레인 조건이 반복적으로 나타난다.

### Cited Findings
- 셀토스 SP3 저압 경고는 감속·급격한 코너링 자제와 타이어 상태/권장 공기압 점검을 요구한다. 시스템 고장 설명은 약 1분 점멸 후 지속 점등이라는 시간 패턴을 구분한다. [저압](https://ownersmanual.kia.com/full_webhelp/SP3/2026/ko_KR/topics/t00940.html), [TPMS 이상](https://ownersmanual.kia.com/full_webhelp/SP3/2026/ko_KR/topics/t00941.html)
- 같은 차의 ESC 점멸은 제어 개입 중 정상 표시일 수 있고, 지속 점등은 점검 안내 대상이다. ESC OFF는 별도 표시다. [표시등](https://ownersmanual.kia.com/full_webhelp/SP3/2026/ko_KR/topics/t00416.html)
- 같은 차의 ABS+브레이크 동시 경고는 EBD 관련 위험 안내와 연결된다. 단일 ABS만 관측했다고 조합을 추정하면 안 된다. [경고등](https://ownersmanual.kia.com/full_webhelp/SP3/2026/ko_KR/topics/t00415.html)
- EV3 2027은 파워다운 단독과 서비스 경고 동시 점등을 구분한다. 전자는 고전력 부품 보호에 따른 제한일 수 있고 후자는 점검 안내가 더해진다. [경고등 및 표시등](https://ownersmanual.kia.com/full_webhelp/SV1/2027/ko_KR/topics/t00163.html)
- 셀토스 HEV의 주행 가능 표시 꺼짐/점멸, HEV 서비스 경고와 정상 EV 모드 점등은 별개다. [HEV 경고·표시](https://ownersmanual.kia.com/full_webhelp/SP3/2026/ko_KR/topics/t00536.html)

### Inferences
- 각 근거에 `required_context`를 저장하고 현재 SDK 관측이 조건을 충족하지 못하면 확정 안내 대신 미확인 조건을 표시해야 한다.
- 서술 근거 6건은 검수 예시이며 나머지 차종/절의 의미상 검수를 대신하지 않는다.

### Gaps
- `kia_reviewed_examples.json`의 상태는 `source_text_reviewed_not_production_approved`다. 아이콘·표 레이아웃을 모두 시각 검수한 상태가 아니다.
- HTML 후보 색인은 15개 경고군의 키워드 일치 결과이며 오탐과 누락이 가능하다. 실제 적용 승인에는 파워트레인·시동 상태·동시 경고 검수가 필요하다.
- 아직 앱 production 데이터에 연결하거나 임베딩하지 않았다. 수집 원본은 `.local/manual-corpus/2026-10-28/kia/`, 재현 방법과 산출물 안내는 `data/manual-research/2026-10-28/kia_README.md`에 있다.
