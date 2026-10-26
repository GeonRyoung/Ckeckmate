# CHECKMATE 설명 서버

앱은 SDK 관측 사실을 관리하고 서버는 선택한 매뉴얼의 근거와 설명만 제공합니다.
첫 데이터는 2025 아이오닉 5 국내용 한국어 TPMS의 직접 작성한 검토 요약 3개입니다.
공식 원문 전체를 복제한 데이터셋이 아니며 임베딩 검색은 아직 포함하지 않습니다.

## 데이터와 API 계약

- `checkmate/contracts.py`: 요청·응답의 Pydantic 계약. 자유 질문·위치·VIN·이력·메모를 받지 않습니다.
- `checkmate/catalog.py`: 프로필→문서→문단 연결, 원문 출처, 요약 해시, 수집 승인 검증.
- `checkmate/data/manuals.json`: 검토 요약과 공식 문서 메타데이터. `sourceSha256`은 확인 당시
  원문 HTML 해시이며 `textSha256`은 저장된 요약의 해시입니다.
- 원문은 권리 유보 문서입니다. 원문 수집은 `originalIngestionApproved=false`로 차단합니다.
  외부 원문을 추가하려면 이용 조건 확인과 데이터 검토가 먼저 필요합니다.
- `READY`에는 설명·실제 인용·처리 방식이 필수입니다. 그 외 상태에는 설명을 넣지 않습니다.
- 설명 상태에 `STATE_UNSUPPORTED`를 추가해 알 수 없는 SDK 상태를 구분합니다.
- `mode`로 검토 요약 검색(`REVIEWED_RETRIEVAL`)과 모델 생성(`AI_GENERATED`)을 구분합니다.
- HTML 출처의 `page`는 `null`이며 절 제목과 공식 URL을 사용합니다.

## 개발 환경

Python 3.12 이상과 uv를 사용합니다. 의존성 버전은 `uv.lock`에 고정합니다.

```bash
cd backend
uv sync --locked
uv run pytest -q
```

이 서버는 로컬 개발용입니다. 공개 배포 전 HTTPS·인증·요청 제한과 운영 설정이 필요합니다.

## 검색 서버 실행

```bash
uv run uvicorn checkmate.main:app --host 127.0.0.1 --port 8000
```

- `GET /health`: 프로세스·데이터 준비 상태. 모델의 실제 응답 성공을 뜻하지 않습니다.
- `GET /v1/manual-profiles`: 지원 프로필.
- `POST /v1/explanations`: 프로필·경고 태그로 먼저 제한한 뒤 관련 용어로 근거를 정렬합니다.
  현재는 고정 의도 `WARNING_OVERVIEW`에 대한 작은 어휘·태그 검색입니다.
- 업무상 미지원·근거 없음은 HTTP 200의 `status`로, 잘못된 JSON은 422로,
  모델/서비스 장애는 503으로 구분합니다. 자동 재요청하지 않습니다.
- 실행 중 `/docs`, `/openapi.json`에서 실제 API 계약을 확인할 수 있습니다.
