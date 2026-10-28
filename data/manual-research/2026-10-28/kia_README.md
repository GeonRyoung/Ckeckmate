# 기아 공식 매뉴얼 수집 스냅샷

확인일: 2026-10-28. 국내 한국어 `countryCode=A99`, `langCode=ko_KR`.

## 확보 결과와 분모

- 공식 매뉴얼 카탈로그 41개 차군/동력계 항목을 열거했다. 단종 보관자료와 버스를 포함하므로 현재 판매 차종 수가 아니다.
- 현재 판매 기본 차군에 연결한 최신 27개 문서를 확보했다. 셀토스는 같은 2026년형에 SP2와 SP3가 함께 공개돼 두 세대를 구분했다.
- 26개 문서는 HTML 목차와 경고·비상대처·점검 관련 본문을 수집했다. 2,637개 HTML 본문/목차용 토픽과 26개 최상위 목차가 저장됐다. **전체 웹매뉴얼 미러가 아니며 이미지·CSS·스크립트는 수집하지 않았다.**
- 카니발 하이리무진 2025는 53쪽 PDF 한 파일 전체를 확보했다. 표지와 PDF 2쪽을 시각 확인했다. 전용 부품의 **보충 설명서**이며 기본 차량 설명서를 대체하지 않는다. 텍스트층이 없어 OCR 전에는 검색 근거로 쓰지 않는다.
- 공식 판매 페이지의 제품행은 총 42행이다. 그랜버드 버스 1행을 제외한 41행 중 기본 차군 일치 19행, 통합 문서 적용/보충 자료 검토가 필요한 22행이다. **41개 제품에 대한 완전한 대처법 검수가 끝났다는 뜻이 아니다.**
- 검증 대상 파일 2,664개, 171,100,205바이트의 존재·크기·SHA-256·HTML/PDF 시그니처를 대조해 실패 0개. 수집 중 짧은 목차 부모 페이지는 `navigation_only`로 구분해 누락과 혼동하지 않았다.

## 파일

| 파일 | 용도 |
|---|---|
| `kia_catalog.json` | 전체 카탈로그, 공개 연식, 최신 선택 변형, 범위 제외 사유 |
| `kia_manifest.json` | 27문서별 출처, 공식 최초/최종 게시일, 원문 경로·해시, 경고 주제별 후보 URL |
| `kia_sales_lineup.json` | EV/승용/RV/상용/PBV 공식 판매 페이지의 제품행 |
| `kia_sales_coverage.json` | 판매 제품행과 문서 ID 연결, `exact_confirmed/shared_candidate/excluded_bus` |
| `kia_reviewed_examples.json` | 본문을 읽어 검수한 대처 분기 6건과 필수 문맥 |
| `kia_validation.json` | 파일별 해시·크기·형식 검사 결과와 집계 |

원문은 저장소 루트 `.local/manual-corpus/2026-10-28/kia/`에 있으며 Git에서 제외된다.
원문 전체 텍스트는 배포용 JSON에 넣지 않았다. 문서 URL/로컬 파일은 수집 증거이며 앱의 production 근거 승인은 별도다.

## 의미상 주의점

`source_label_year`는 공식 카탈로그의 모델 연식이고, 실제 게시일은 `latest_evidence.web_publication/pdf_publication`이다. 예컨대 2027 EV3 매뉴얼은 최초·최종 게시일이 2026-02-06으로 표시된다. 연식 2027을 미래 추정으로 생성하지 않았다.

셀토스 SP3의 API fuel 값은 ICE지만 실제 문서 제목에는 ICE/PHEV/HEV가 들어가고 HEV 장이 존재한다. 이 문자열만으로 국내 PHEV 판매 여부를 주장하지 않는다. 세부 파워트레인 및 사양 적용은 따로 검수해야 한다.

GT, 택시, PV5 차체/좌석 구성, 봉고 특장차는 기본 차군 설명서를 후보로 연결했으며 적용 확정이 아니다. 하이리무진 2025 보충 설명서에 대해 이번 기본 카니발 문서는 2027이므로 정확한 연식 일치도 미완료다.

경고 후보 URL은 키워드 검색 결과다. 항목이 없다고 해당 경고가 없는 차라고 판단하면 안 되며, 키워드가 있다고 그 차량에 해당 고장 기능이 있다는 확정도 아니다. HTML은 PDF 쪽번호 대신 URL과 절 제목을 인용한다.

## 재현

조사 전용 환경을 사용한다. 앱/백엔드 의존성은 변경하지 않는다.

```powershell
uv venv .local/manual-tools
uv pip install --python .local/manual-tools/Scripts/python.exe httpx beautifulsoup4 pymupdf
& .local/manual-tools/Scripts/python.exe scripts/manuals/kia_acquire.py
& .local/manual-tools/Scripts/python.exe scripts/manuals/kia_audit.py
```

이 스크립트는 기존 다운로드를 재사용하는 **2026-10-28 스냅샷 재현 도구**다. 향후 최신성 갱신에는 새로운 날짜 폴더에서 카탈로그·모델·문서 메타데이터를 새로 받아야 한다. 판매 목록 대조는 `kia_sales_lineup.json`의 공식 링크를 새로 확인해야 한다.

사용 패키지: httpx 0.28.1, beautifulsoup4 4.15.0, pymupdf 2.0. 동시 요청은 최대 3개 작업자이며 재시도와 로컬 캐시를 사용한다.

공식 진입점: [기아 사용자 설명서](https://ownersmanual.kia.com/main), [국내 매뉴얼 카탈로그 API](https://ownersmanual.kia.com/api/v2/kia/models?countryCode=A99&langCode=ko_KR), [EV](https://www.kia.com/kr/vehicles/ev), [승용](https://www.kia.com/kr/vehicles/sedan), [RV](https://www.kia.com/kr/vehicles/rv), [상용](https://www.kia.com/kr/vehicles/commercial), [PBV](https://www.kia.com/kr/vehicles/pbv).
