# 앱 경고 신호와 차량별 근거 매핑

## 현재 앱은 어떤 경고를 받을 수 있고 무엇을 설명하는가

### Takeaway
SDK 2.3.2에는 경고·표시 유형 95개가 선언되어 있고, 현재 로컬 Pleos 콘솔은 그중 37개를 입력할 수 있다. 앱의 매뉴얼 설명은 2025 대한민국용 아이오닉 5 TPMS 1종·프로필 1개·검토 요약 3개에 한정된다. 이는 95종 실차 지원이나 95종 설명 구현을 뜻하지 않는다.

### Cited Findings
- 설치된 `ai.pleos.playground:Vehicle:2.3.2` AAR의 `classes.jar`를 `javap`로 확인하여 `TelltaleType` enum 상수 95개와 상태 `OFF/ON/BLINK`를 추출했다. 95개 전체 목록, 콘솔 별칭, AAR SHA-256, 카탈로그 SHA-256을 저장했다. — [신호 목록](../../data/manual-research/2026-10-28/warning_mapping.json)
- `PleosWarningSource`는 capability를 확인한 후 목록의 `type.name`과 `state.name`을 `WarningReading`으로 변환한다. SDK `TelltaleData`에 있는 `color`, `priority`, `warningCount`는 이 변환에서 버려진다. — [앱 수신 소스](../../android/app/src/main/java/com/checkmate/pleos/vehicle/PleosWarningSource.kt)
- 이력에는 상태 변화의 시각과 관측 공백이 있지만, 점멸 주기나 점멸 지속시간, 시동 단계, 클러스터 메시지·타이어 실측 압력이 없다. 전체 현재 경고 목록은 앱 메모리에 있지만 설명 서버에는 선택한 경고만 전달한다. — [관측 모델](../../android/app/src/main/java/com/checkmate/pleos/vehicle/WarningMonitor.kt), [서버 설명 연결](../../android/app/src/main/java/com/checkmate/pleos/MainActivity.kt)
- 현재 승인된 근거는 `hyundai-ioniq5-2025-ev-kr-ko-r1.27`의 TPMS 요약 3개이며, 원문 전체 수집 승인은 별도 플래그다. — [기존 카탈로그](../../backend/checkmate/data/manuals.json), [로컬 안내 분기](../../android/app/src/main/java/com/checkmate/pleos/manual/TpmsGuide.kt)

### Inferences
- 신규 수집 자료는 조사 자료로 저장하고 현재 3개 근거에 자동으로 합치거나 덮어쓰지 않는다. PDF 다운로드 성공은 검색 승인·차량 진단 검증과 별개다.
- 매핑의 `supported_signal`은 SDK 선언 여부, `console_testable`은 로컬 콘솔 입력 여부, `app_preserves_context`는 현재 앱 수집 항목, `eligible_for_explanation`은 현재 구현된 안내 범위를 뜻한다. 타입이 존재한다는 사실만으로 실제 차량의 capability를 추정하지 않는다.
- `acquisition_priority` P0/P1/P2는 자료 확보 순서이며 정차 여부·운행 가능 여부·위험도 판정이 아니다. 유형별 한국어 이름과 적용 파워트레인은 후보이고 모델별 승인 상태가 아니다.

### Gaps
- 95개 각각의 실차 신호 제공 여부는 확인하지 않았다. 콘솔에서 제공하지 않는 58개에 대해 시뮬레이터 실기 검증을 주장할 수 없다.
- `PARKING_BRAKE`가 특정 차종의 적색 브레이크 경고 전체를 의미하는지, `RBS`가 정확히 어떤 조합 경고를 보내는지는 enum 이름만으로 확정할 수 없다.
- 색상·시동 단계·클러스터 문구가 필요한 항목은 현재 저장된 type/state만으로 원문 조건을 충족하지 못할 수 있다.

## 어떤 차종별 차이를 근거에 보존해야 하는가

### Takeaway
경고의 의미는 점등/점멸, 시동 직후인지, 동시 경고, 파워트레인과 운전자 관찰 증상에 따라 달라진다. 아래는 출처 본문을 확인한 제한된 예시이며 현대·기아 전 차종 공통 규칙이나 최신 연식 전수 검토 완료가 아니다.

### Cited Findings
- 2025 아이오닉 5 TPMS는 저압 점등과 점멸 후 점등 패턴의 시스템 이상을 구분한다. 저압 때 감속·급조향 회피 및 타이어 점검을 안내하지만, SDK `BLINK` 한 번으로 전체 시간 패턴을 관측한 것은 아니다. — [2025 NE1 TPMS](https://ownersmanual.hyundai.com/full_webhelp/NE1/2025/ko_KR/id23C5E0QD0YK.html)
- 2025 그랜저의 ABS+브레이크 동시 점등 설명은 EBD 기능 문제와 연결하며 고속 주행·급제동 회피 및 점검을 안내한다. ABS 단독 문단과 구분해야 한다. — [GN7 2025 경고등, EBD 절](https://ownersmanual.hyundai.com/full_webhelp/GN7/2025/ko_KR/warning_indicator_lights.html)
- 같은 GN7 설명서에서 MIL 점등·점멸은 점검 대상으로 다루지만, 점멸만으로 특정 실화 원인을 확정하지 않는다. 엔진 오일 압력은 안전 정차·오일 확인 대상으로 별도 기술한다. 충전 경고는 충전 계통과 관련하며 EV 고전압 잔량 경고와 다르다. — [GN7 2025 엔진·오일·충전 절](https://ownersmanual.hyundai.com/full_webhelp/GN7/2025/ko_KR/warning_indicator_lights.html)
- GN7의 EPS 지속 점등/점멸, 에어백 시동 점검 후 지속 점등은 점검 문맥이다. 통합 경고는 여러 기능의 문제를 포괄하므로 단일 고장명을 출력할 근거가 아니다. — [GN7 2025 EPS·에어백·통합 경고 절](https://ownersmanual.hyundai.com/full_webhelp/GN7/2025/ko_KR/warning_indicator_lights.html)
- 2026 아이오닉 5는 파워다운 단독과 서비스 경고 동시 표시를 구분한다. 또한 12V 보조 배터리 충전 경고와 고전압 배터리 충전량 경고를 별도 항목으로 둔다. 원인 후보를 특정 부품 고장으로 확정하거나 두 배터리를 같은 대상으로 다루면 안 된다. — [NE1 2026 경고등 표](https://ownersmanual.hyundai.com/full_webhelp/NE1/2026/ko_KR/id23C4LH00HL7.html)
- 2025 아이오닉 6 ESC는 정상 제어 작동 시 깜빡이며, 지속 점등은 다른 점검 문맥이다. 점멸 중 가속하지 않고 서행하라는 안내가 있고 ESC OFF는 기능 해제 표시로 분리된다. — [CE1 2025 ESC](https://ownersmanual.hyundai.com/full_webhelp/CE1/2025/ko_KR/id0901bae25b0.html)
- 2026 쏘나타 과열 절차는 안전 정차 후 증기·냉각수 누출 여부에 따라 시동 유지/정지 조건이 갈린다. 뜨거운 냉각수 캡을 열지 말라는 주의와 팬 미작동·누수 때 운행 중단 조건도 있다. 따라서 단순 `ENGINE_TEMPERATURE=ON`에 모든 조건을 생략한 일괄 조치를 생성하면 원문과 충돌할 수 있다. — [DN8 2026 엔진 과열](https://ownersmanual.hyundai.com/full_webhelp/DN8/2026/ko_KR/id3ffd8b0b855.html)
- 2026 기아 셀토스 SP3 설명서는 하이브리드 전용 경고 장을 별도로 둔다. HEV 서비스 경고의 지속 점등은 점검 대상으로 설명하지만, EV 모드 표시는 정차 중 엔진 정지 또는 모터 단독 구동 상태를 나타낸다. `HEV_MODE` 같은 표시를 곧바로 `HEV_SYSTEM` 고장으로 취급하면 안 된다. 문서 한 권 안의 파워트레인 적용 조건을 청크 단위로 보존해야 한다. 해당 URL은 웹 검색 도구에서 열리지 않았지만 Python HTTPS 요청으로 HTTP 200과 본문을 확인했다. — [SP3 2026 하이브리드 전용 경고](https://ownersmanual.kia.com/full_webhelp/SP3/2026/ko_KR/topics/t00536.html)

### Inferences
- 내연기관의 오일·벨트 절차를 BEV에 검색시키지 않도록 브랜드/차종 코드/연식/시장/언어/파워트레인 필터를 먼저 적용한다. HEV는 엔진과 전동계가 모두 있으므로 EV·ICE 어느 한쪽으로 단순 합치지 않는다.
- `BLINK`가 언제나 고장이라는 규칙은 ESC 예시와 맞지 않는다. 색상도 단독 위험도 분류 규칙으로 사용하지 않는다.
- 미래 답변은 “SDK 관측 사실”, “해당 차량 매뉴얼의 조건부 설명”, “현재 입력으로 확인 불가”를 구분한다. 기록의 OFF·목록 제외는 정비 완료 판정이 아니다.

### Gaps
- 기아 검색 결과에 나온 문서 UUID `5d14be9b-b783-4d5a-8d96-f65cf9f04e4f/topics/t00507.html`는 직접 열기에서 404였다. 검색 스니펫만으로 차종·연식·최신성을 확정하지 않아 승인 근거로 채택하지 않았다. 기아별 확정 자료는 별도 브랜드 조사 노트를 따른다.
- 이 노트는 기존 앱의 2025 근거와 신호 구분을 분석하기 위해 구판 예시도 명시적으로 사용했다. 최신 연식 카탈로그 확보 결과와 혼동하면 안 된다.
- 예시들은 HTML 본문 검토이며 계기판 이미지/색상 전체를 시각 검토한 결과가 아니다. 신규 예시의 runtime retrieval 승인은 아직 없다. 기아 SP3의 TPMS 부모 페이지는 개요와 하위 절 링크이므로 그 페이지만으로 저압/시스템 이상 조치를 확보했다고 계산하지 않는다. — [SP3 TPMS 부모 절](https://ownersmanual.kia.com/full_webhelp/SP3/2026/ko_KR/topics/t00938.html)

## 원문 확보 뒤 어떤 검수와 평가를 통과시킬 것인가

### Takeaway
원문 파일 확보, 절 후보 추출, 본문/이미지 검토, 앱 검색 승인 단계를 분리한다. 차량별 조건과 출처 위치가 없는 문장을 기존 답변 데이터로 자동 편입하지 않는다.

### Cited Findings
- 초안 스키마는 차종·연식·시장·파워트레인, 판본·원문 해시·조회일, PDF 0기준 페이지와 인쇄 페이지 또는 HTML URL/앵커, 조건·동시 경고·행동·금지 추론·검토 상태를 별도로 둔다. 검색 승인에는 `APPROVED`, 담당자/일시, `APPROVED_FOR_APP`가 필요하다. — [근거 스키마 초안](../../data/manual-research/2026-10-28/warning_evidence.schema.json)
- JSON 파싱과 95개 SDK enum 일치 검사에 더해, 주 에이전트가 `uv run --no-project --with jsonschema python` 환경에서 `Draft202012Validator.check_schema`를 실행해 통과를 확인했다. 이는 JSON Schema 문서 구조 검증이며 개별 근거 레코드의 사실성·조건 해석·의미 품질을 보장하지 않는다. — [검증 대상 스키마](../../data/manual-research/2026-10-28/warning_evidence.schema.json)
- 현재 데이터 모델은 source hash와 profile별 분리 및 retrievalApproved를 이미 사용하므로 확장 시 이 경계를 보존해야 한다. — [현재 백엔드 카탈로그](../../backend/checkmate/data/manuals.json)

### Inferences
- 취득 검수: 공식 목록의 링크와 최종 URL, HTTP 성공 및 MIME/파일 시그니처, SHA-256/파일 크기, 페이지 수를 기록하고 HTML 오류 페이지를 PDF로 오인하지 않는다.
- 정체성 검수: 표지·목차·공식 카탈로그를 대조하여 국내용/한국어/차종 코드/연식/파워트레인/통합 설명서 여부를 확인한다. `latest`는 확인한 공식 카탈로그 안에서만 의미를 가진다.
- 추출 검수: 경고등 이름을 찾은 페이지는 `AUTO_LOCATED`다. 목차·색인·인접 차종·주의 박스·표 셀의 혼합 여부를 본문 및 필요 시 이미지로 확인해야 `TEXT_REVIEWED`/`VISUAL_REVIEWED`로 올린다.
- 의미 검수: 시동 직후 정상 점검, 점멸 지속시간, 동시 경고, 색상·트림·엔진 조건, 금지사항을 같은 근거에 보존한다. 모르는 원인·운행 가능 거리·수리비·고장 횟수를 추가하지 않는다.
- 공개 검색 승인 전 원문 이용 조건과 앱 내 인용 범위를 확인하고 요약/출처 표시 정책을 결정한다. 단순 다운로드는 앱 사용 허가를 의미하지 않는다.
- 평가 후보: 잘못된 연식·시장·파워트레인 차단, TPMS 단일 BLINK에서 시간 패턴 보류, ABS+브레이크 조합과 단독 분리, 12V/HV 분리, ESC 점멸 정상 작동 문맥, MIL 원인 단정 금지, 과열 시 증기 조건 보존, 통합 경고 메시지 부재 처리, 검색 실패 시 근거 없음, OFF/관측 공백에서 정상·수리 완료 단정 금지를 포함한다.

### Gaps
- 초안 JSON Schema는 런타임 코드에 연결하지 않았다. 모델별 근거 항목 작성·전문 검수·검색 품질 평가는 다음 단계이며, 이번 수집만으로 전체 AI 답변 품질이 검증되었다고 주장하지 않는다.
