# 현대·기아 공식 매뉴얼 조사 데이터

확인일 2026-10-28, 국내 한국어 자료다. 기존 앱 커밋은 `f21c5f9`이며 이번 조사 데이터는 앱의 승인 근거나 임베딩 저장소에 자동 반영하지 않았다. [조사 보고서](../../../reports/현대%20기아%20경고등%20매뉴얼%20조사.md)에서 차종별 대처 예시와 적용 공백을 확인할 수 있다.

| 구분 | 확보 | 범위 해석 |
|---|---|---|
| 현대 | 35문서: PDF 28개·14,792쪽 + 웹 7개 | 웹은 전체 검색본문·목차 및 관련 HTML이며 모든 이미지·CSS의 오프라인 미러는 아님 |
| 기아 | 27문서: 웹 26개 + 보충 PDF 1개·53쪽 | 웹은 경고·비상조치·점검 관련 절만 수집. 하이리무진 PDF는 OCR·기본 설명서 연결 필요 |
| 합계 | 62문서, 원문 검증 자산 990,230,243바이트 | 62개 차량의 서비스 답변 승인 수가 아님 |

현대 국내 판매 대상 44행은 차종군 자료에 모두 연결했지만 특장 등 9행은 적용 확인이 더 필요하다. 기아 국내 대상 41행은 기본 차종군 일치 19행과 공유 자료 후보 22행으로 나눴다. `exact_confirmed`도 차종군 일치만 의미하며 연식·트림·모든 대처법 승인이 아니다. ST1 판매 연식 힌트와 설명서 연식 차이, 셀토스 SP3 통합 파워트레인 조건을 보존한다.

## 파일 안내

| 파일 | 내용 |
|---|---|
| `hyundai-catalog.json` / `kia_catalog.json` | 전체 공식 설명서 카탈로그와 수집·제외 사유 |
| `hyundai-current-lineup-coverage.json` | 현대 현재 판매 60행 중 범위 44행의 문서 연결 및 공백 |
| `kia_sales_lineup.json` / `kia_sales_coverage.json` | 기아 판매 42행 중 범위 41행의 연결·공유 후보·제외 |
| `hyundai-manifest.json` / `kia_manifest.json` | 문서별 차종·연식·출처·공식 게시일·해시·경로·경고 위치 후보 |
| `hyundai-reviewed-examples.json` / `kia_reviewed_examples.json` | 직접 출처를 확인한 예시 각 6건. 전문가 승인·앱 활성화 아님 |
| `hyundai-validation.json` / `kia_validation.json` | 파일 존재·크기·해시·형식 및 해당 문서 구조 검증 |
| `warning_mapping.json` | SDK 95종·콘솔 37종·현재 설명 1종의 구분과 문맥 요구 |
| `warning_evidence.schema.json` | 향후 근거 레코드 초안. Draft 2020-12 스키마 문서 검사 통과 |
| `kia_README.md` | 기아 수집 범위·검증·재현 상세 |

매니페스트의 자동 경고 후보는 목차·중복 언급·관련 절을 포함할 수 있다. 위치 후보가 있다는 사실을 해당 차종의 경고 기능 존재나 조치 검수 완료로 해석하지 않는다. PDF 실제 페이지와 인쇄 페이지, HTML 절 URL을 구분한다. 수집일, 모델 연식, 공식 최초·수정 게시일은 별도 필드다.

## 원문 보관과 재현

원문은 저장소 루트 `.local/manual-corpus/2026-10-28/hyundai/` 및 `kia/`에 있으며 `.local/`은 Git 제외 대상이다. 아래 명령은 저장소 루트에서 실행한다. 앱 의존성과 분리된 도구 환경을 사용한다.

```powershell
# 현대: 수집, 웹 본문·판매 목록 대조, 무결성 검사
uv run --no-project --with pymupdf==2.0 python scripts/manuals/hyundai_acquire.py
uv run --no-project --with pymupdf==2.0 python scripts/manuals/hyundai_web_and_coverage.py
uv run --no-project --with pymupdf==2.0 python scripts/manuals/hyundai_validate.py

# 기아: 별도 조사 환경에서 수집·검증
uv venv .local/manual-tools
uv pip install --python .local/manual-tools/Scripts/python.exe httpx==0.28.1 beautifulsoup4==4.15.0 pymupdf==2.0
& .local/manual-tools/Scripts/python.exe scripts/manuals/kia_acquire.py
& .local/manual-tools/Scripts/python.exe scripts/manuals/kia_audit.py
```

이 도구는 기존 캐시를 재사용하는 **2026-10-28 스냅샷 재현용**이다. 날짜 경로와 카탈로그·문서 메타데이터를 갱신하지 않고 재실행한 결과를 새로운 최신성 검증이라고 부르지 않는다. 현재 원본의 저장·검증은 완료됐지만 의미 검수, 특장 적용 확인, 일부 OCR, 앱 검색 승인, 벡터화는 후속 단계다.

공식 진입점은 [현대 취급설명서](https://ownersmanual.hyundai.com/)와 [기아 취급설명서](https://ownersmanual.kia.com/main)다. 원문 전체 재배포 권한은 이번 조사에서 확정하지 않았으며, Git에는 원문 전문 대신 추적 가능한 메타데이터·검증 결과·조사 코드를 둔다.
