# CHECKMATE 설명 서버

앱은 SDK 관측 사실을 관리하고 서버는 선택한 매뉴얼의 근거와 설명만 제공합니다.
데이터는 2025 아이오닉 5 국내용 한국어 공식 PDF 기준 직접 작성한 검토 요약 10개입니다.

| SDK 경고 | 근거 | 설명하는 상태 |
|---|---|---|
| `TPMS` | 5개 · PDF 138, 493, 495, 496쪽 | `ON`, `BLINK` |
| `ELECTRONIC_PARKING_BRAKE` | 5개 · PDF 138, 331, 332, 333쪽 | `ON` (매뉴얼은 EPB 경고등을 '켜짐'으로만 설명. 깜빡임은 별도의 브레이크 경고등) |

공식 원문 전체를 복제한 데이터셋이 아닙니다. 경고별 지원 상태와 한계 안내는 `service.WARNING_SCOPE`에 있습니다.
빨간 브레이크 경고(`PARKING_BRAKE`)는 브레이크액 부족·브레이크 이상과 겹쳐 아직 지원하지 않습니다.

## 처리 흐름 (LangGraph)

`checkmate/graph.py`가 요청 하나를 LangGraph `StateGraph`로 처리합니다. API 계약과 응답은 그래프 도입 전과 같습니다.

```
START → check_scope ─(프로필 없음·미지원 프로필/경고/상태)→ END
            ↓
         retrieve ─(근거 없음 / 임베딩 서버 오류)→ END
            ↓
          answer ⇄ (생성 초안이 검증에 실패하면 1회 재시도, 다시 실패하면 TEMPORARILY_UNAVAILABLE)
            ↓
           END
```

- 각 노드는 `ExplanationService`의 `check_scope`·`find_evidence`·`answer`만 호출합니다. 프로필·경고 필터,
  상태 범위, 인용·수치 검증은 기존 코드 그대로입니다. 그래프 상태의 `trace`로 지나간 경로를 확인할 수 있습니다.
- 재시도는 검증 실패(`AnswerRejected`: 가짜 인용·근거 없는 수치·근거 누락)일 때만 합니다.
  모델 시간 초과·통신 오류는 다시 시도해도 대기만 늘어나므로 바로 종료합니다.
- 벡터 DB와 LangChain 검색기 래퍼는 쓰지 않습니다. 근거가 10개라 메모리 비교로 충분하고(질문당 0.1~2.6초,
  그래프 자체 부하 약 2.7ms), 근거가 수천 개로 늘면 `QuestionRanker`를 벡터 DB 구현으로 교체합니다.
  LangGraph가 의존하는 `langchain-core`만 설치됩니다.

## 데이터와 API 계약

- `checkmate/contracts.py`: 요청·응답의 Pydantic 계약. 자유 질문·위치·VIN·이력·메모를 받지 않습니다.
- `checkmate/catalog.py`: 프로필→문서→문단 연결, 원문 출처, 요약 해시, 수집 승인 검증.
- `checkmate/data/manuals.json`: 검토 요약과 공식 문서 메타데이터. `sourceSha256`은 확인 당시
  원문 PDF 파일의 해시이며 `textSha256`은 저장된 요약의 해시입니다.
- 원문은 권리 유보 문서입니다. 원문 수집은 `originalIngestionApproved=false`로 차단합니다.
  외부 원문을 추가하려면 이용 조건 확인과 데이터 검토가 먼저 필요합니다.
- `READY`에는 설명·실제 인용·처리 방식이 필수입니다. 그 외 상태에는 설명을 넣지 않습니다.
- 설명 상태에 `STATE_UNSUPPORTED`를 추가해 알 수 없는 SDK 상태를 구분합니다.
- `mode`로 검토 요약 검색(`REVIEWED_RETRIEVAL`)과 모델 생성(`AI_GENERATED`)을 구분합니다.
- PDF 출처의 `page`는 1부터 세는 PDF 쪽 번호입니다(인쇄 쪽 번호와 다를 수 있음). HTML 출처는 `null`입니다.

## 개발 환경

Python 3.12 이상과 uv를 사용합니다. 의존성 버전은 `uv.lock`에 고정합니다.

```bash
cd backend
uv sync --locked
uv run pytest -q
```

Windows에서도 같은 uv 명령을 사용합니다. 한글 매뉴얼 데이터는 코드에서 UTF-8로 읽으므로
`PYTHONUTF8` 또는 `-X utf8`을 별도로 설정할 필요가 없습니다.
PowerShell에서 Ollama 모드를 실행하려면 다음과 같이 설정합니다.

```powershell
$env:CHECKMATE_GENERATION = 'ollama'
uv run uvicorn checkmate.main:app --host 127.0.0.1 --port 8000
```

이 서버는 로컬 개발용입니다. 공개 배포 전 HTTPS·인증·요청 제한과 운영 설정이 필요합니다.

## 평가 세트

`evals/ioniq5_2025.json`: 아이오닉 5 2025 상황 질문 34개(TPMS 22, EPB 12) + 거절 5개
(다른 차종·다른 경고·OFF·프로필 없음·EPB BLINK).
각 사례에 정답 근거 ID, 반드시 남아야 하는 조건·수치, 공통 금지 표현(고장 단정·정상 단정·주행 허용·압력 수치 등)을 둡니다.

```bash
uv run python -m checkmate.evaluation   # CHECKMATE_GENERATION=ollama 이면 생성 모드로 채점
```

`CHECKMATE_RETRIEVAL=embedding`이면 질문 검색에 bge-m3를 씁니다(`ollama pull bge-m3`).
같은 사례를 개요 요청과 질문 요청(`intent=QUESTION`) 두 방식으로 채점하고,
검색기와 글자 2-gram 기준선의 hit@k를 함께 보고합니다.

결과(`reviewed` 생성, 질문 상위 3개 반환):

| 날짜 · 범위 | 검색기 | 질문 hit@1 | hit@2 | 질문 응답 검사 | 개요 응답 검사 |
|---|---|---|---|---|---|
| 10-28 · TPMS 26사례 | 2-gram 기준선 | 0.500 | 0.682 | 21/26 | 26/26 |
| 10-28 · TPMS 26사례 | bge-m3 | 0.682 | 0.909 | 26/26 | 26/26 |
| 10-29 · TPMS+EPB 39사례 | 2-gram 기준선 | 0.559 | 0.735 | 33/39 | 39/39 |
| 10-29 · TPMS+EPB 39사례 | bge-m3 | **0.735** | **0.941** | **39/39** | 39/39 |

- 근거가 10개로 늘어도 경고 유형으로 먼저 거르므로 다른 경고의 근거가 섞이지 않았습니다.
- bge-m3 hit@3은 TPMS 26사례에서 1.0이라 질문 응답은 상위 3개(`QUESTION_TOP_K`)로 정했습니다.
- 2-gram과 bge-m3 순위 결합(RRF, k=1·10·60, 가중치 0.5·0.7)은 hit@2를 높이지 못해 채택하지 않았습니다.
  22개 질문에 맞춰 가중치를 고르면 과적합이 됩니다.
- **한계:** "타이어 경고등이 그냥 켜졌어요"처럼 모호한 질문에서 저압 대처(감속·급조향 회피) 근거는
  4위로 빠집니다. 질문 응답은 상태별 전체 안내를 **대체하지 않고 보조로** 표시해야 합니다.
- 개요 검사 26/26은 근거 5개를 모두 반환하기 때문에 "내용이 빠짐없이 들어 있다"는 뜻입니다.
- 노트북 CPU 기준 bge-m3 첫 로딩(근거 5개 포함) 약 13초, 이후 질문당 0.1~2.6초. 첫 호출은
  모델 로딩 때문에 임베딩 요청 제한을 90초로 둡니다.
- `ollama` 생성 모드 채점은 GPU 환경에서 실행해야 합니다(노트북 CPU에서는 시간 초과).

## 검색 서버 실행

```bash
uv run uvicorn checkmate.main:app --host 127.0.0.1 --port 8000
```

- `GET /health`: 프로세스·데이터 준비 상태. 모델의 실제 응답 성공을 뜻하지 않습니다.
- `GET /v1/manual-profiles`: 지원 프로필.
- `POST /v1/explanations`: 프로필·경고 태그로 먼저 제한한 뒤 관련 용어로 근거를 정렬합니다.
  - `intent=WARNING_OVERVIEW`(기본): 상태별 근거 전체(현재 5개). 앱이 쓰는 방식입니다.
  - `intent=QUESTION` + `question`(1~300자): 같은 필터 안에서 질문과 가까운 근거 상위 3개.
    차량 데이터·식별 정보는 받지 않습니다. 임베딩 서버 오류 시 추측하지 않고 `TEMPORARILY_UNAVAILABLE`.
- 업무상 미지원·근거 없음은 HTTP 200의 `status`로, 잘못된 JSON은 422로,
  모델/서비스 장애는 503으로 구분합니다. 자동 재요청하지 않습니다.
- 실행 중 `/docs`, `/openapi.json`에서 실제 API 계약을 확인할 수 있습니다.

## Qwen 및 Ollama 연결

```bash
cp .env.example .env
# .env의 CHECKMATE_GENERATION을 ollama로 변경
uv run uvicorn checkmate.main:app --host 127.0.0.1 --port 8000
```

`OLLAMA_BASE_URL`과 `OLLAMA_MODEL`을 실행 환경에 맞게 설정합니다. 현재 개발 환경에는
`qwen2.5:7b`가 설치되어 있어 이 모델로 확인했습니다. OpenAI 키나 SDK는 사용하지 않습니다.
Ollama `/api/chat`의 JSON schema 출력으로 설명을 받고 서버에서 다시 검증합니다.
근거 ID·종류·모든 근거 포함 여부·새 수치 유입을 검사하며, 출처 URL과 한계 안내는
모델이 생성하지 않고 서버가 붙입니다. 이 검사는 문장 전체의 사실성을 증명하지 않으므로
새 문서·모델 추가 시 사례별 내용 평가가 필요합니다.

모델은 동시에 한 요청만 처리하며, 사용 중·60초 초과·응답 오류·검증 실패 시 503을 반환합니다.
이때 검증되지 않은 문장을 반환하지 않습니다. 앱은 같은 프로필의 로컬 요약으로 복귀합니다.

2026-10-26 검증:

- 계약·검색·HTTP·모델 어댑터 테스트 27개 통과.
- 실제 `qwen2.5:7b` 호출: TPMS ON 40.57초(첫 호출), BLINK 3.31초.
- 두 응답 모두 READY, AI_GENERATED, 실제 근거 3개 인용. 설명의 조건과 점검 안내 유지 확인.
- 이 두 사례는 전체 모델 품질이나 지연 보장을 의미하지 않습니다.
- 모델 미완료·잘못된 JSON·가짜 출처·근거 누락·새 수치·타임아웃은 모의 응답으로 차단 검증.

2026-10-28 근거 교체(검토 요약 3개 → 5개, 공식 PDF 기준) 후:

- 계약·검색·HTTP·모델 어댑터 테스트 28개 통과(모의 생성기 포함).
- 실제 `qwen2.5:7b` 생성은 **미검증**. GPU가 없는 노트북(CPU 실행)에서 ON·BLINK 모두 60초 제한을
  넘겨 503(`TEMPORARILY_UNAVAILABLE`)으로 처리됐고, 300초로 늘린 직접 호출도 끝나지 않았습니다.
  기본 `reviewed` 모드는 모델을 사용하지 않습니다. GPU 환경에서 5개 근거 인용·검증 통과를 다시 확인해야 합니다.

API 구현 참고: [Ollama 구조화 출력](https://docs.ollama.com/capabilities/structured-outputs),
[Ollama Chat API](https://docs.ollama.com/api/chat).
