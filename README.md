# CHECKMATE

Pleos 차량 경고를 매뉴얼 기반 설명, 관측 이력, 정비 전달용 요약으로 연결하는 Android 앱입니다.

## 현재 상태

- Kotlin + XML / View Binding 기반 현재 경고·상세·이력·매뉴얼 설정 화면
- Pleos Vehicle SDK 2.3.2: capability 확인, 초기 조회, 실시간 리스너, 화면 종료 시 해제
- 경고 종류·원시 상태·관측 시각·마지막 수신 시각 표시
- 오류/null과 유효한 빈 목록 구분, 반복 상태 중복 제거, 관측 공백 표시
- `CarUxRestrictions` 확인 전 또는 제한 중에는 상세 영역과 재연결 조작 차단
- Room 2.8.4 + SQLite로 관측 구간과 구조화된 경고 이벤트를 영구 저장
- 경고 이력 화면: 최신순 50개씩 조회, 이전/최근 페이지 및 새로고침
- 강제 종료 후 종료 시각 미확인 공백을 기록하고 기존 경고를 관측 재개로 구분
- 현재 화면의 최근 변화는 50개 메모리 목록이며, 전체 저장 이력은 별도 조회
- 2025 아이오닉 5 한국어 매뉴얼 프로필 선택·보존 및 TPMS 오프라인 설명·출처 표시
- FastAPI 설명 API, 프로필 범위 검색, Ollama/Qwen 생성 및 앱의 명시적 서버 요청
- 정비 전달용 관측 요약: 오늘·최근 7일·최근 30일 전체 집계, 공백 구분, 최근 50개 상세
- 대규모 원문 데이터·임베딩 검색, 사용자 메모는 후속 구현
- 근처 현대·기아 정비점 검색 및 전화 연결은 지원 여부 검증 후 추가할 옵션

## 프로젝트 구조

```text
android/                 Android Studio에서 열 프로젝트
  app/src/main/          Kotlin 코드, 화면 리소스, Manifest
  app/schemas/           Room DB 버전별 스키마 (Git 관리)
  gradle/                버전 카탈로그 및 Gradle Wrapper
backend/                 FastAPI, 근거 데이터, Ollama 어댑터와 테스트
docs/                    기존 기획 문서 (기존 정책에 따라 Git 제외)
```

## 개발 환경

기존 `PleosVehicleTest` 프로젝트에서 사용한 AGP 9.4.1, Gradle 9.6.0,
Pleos Vehicle SDK 2.3.2를 기준으로 설정했습니다. 최신 버전이라는 의미는 아닙니다.
AGP의 내장 Kotlin 지원을 사용하므로 별도 Kotlin Android 플러그인을 추가하지 않습니다.

- Android Studio와 호환되는 Gradle JDK (현재 로컬 환경: Android Studio 내장 JDK 25)
- Android SDK Platform 35 (`compileSdk` / `targetSdk` 35, `minSdk` 28)
- Pleos Connect Emulator 및 Virtual Console
- Google Maven, Maven Central, Pleos Maven 저장소 접근

## 실행

### Windows 통합 실행

저장소 루트의 `START.cmd`를 더블클릭하거나 PowerShell에서 실행합니다.

```powershell
.\scripts\Start-Checkmate.ps1
```

Pleos AVD와 Android SDK/JDK, uv, Ollama 및 `qwen2.5:7b`가 설치된 환경에서 사용합니다.
스크립트는 다음 순서로 실행하며, 실패하면 이유를 출력하고 종료 코드 1로 끝납니다.

1. 지정한 AVD를 재사용하거나 실행하고 부팅 완료를 기다립니다.
2. `uv sync --locked`로 백엔드 의존성을 준비하고 Ollama 모델 설치 여부를 확인합니다.
3. 정상 CHECKMATE 서버가 있으면 재사용하고, 없으면 localhost:8000에 실행합니다.
4. 웹 콘솔의 `adb forward`와 앱 서버 연결의 `adb reverse`를 설정합니다.
5. debug APK를 빌드하고 `install -r`로 기존 앱 데이터를 보존해 설치한 뒤 실행합니다.
6. 웹 콘솔·API 응답과 앱 프로세스를 확인한 후에만 `READY`와 주소를 출력합니다.

```powershell
# 이미 빌드한 APK로 빠르게 실행 (코드 변경을 반영하려면 이 옵션을 빼세요)
.\scripts\Start-Checkmate.ps1 -SkipBuild

# 서비스를 시작하거나 포트를 수정하지 않고 실행 상태만 점검
.\scripts\Start-Checkmate.ps1 -CheckOnly

# 다른 Pleos AVD 이름이나 SDK 위치를 사용하는 경우
.\scripts\Start-Checkmate.ps1 -AvdName MyPleos -SdkPath 'D:\Android\Sdk'

# Ollama 없이 검토된 근거 요약으로 새 백엔드 시작
.\scripts\Start-Checkmate.ps1 -GenerationMode reviewed
```

기본 AVD는 `Checkmate_Pleos_API_34`, SDK는 `%LOCALAPPDATA%\Android\Sdk`,
JDK는 Android Studio의 `jbr`입니다. JDK 경로는 `-JavaHome`으로 변경합니다.
AVD나 모델을 자동 다운로드하지 않으며, 없으면 설치할 항목을 안내합니다.
새 백엔드는 `-GenerationMode`와 `-OllamaModel`로 설정합니다. 기존 서버는 실행 중인 설정을
유지하며, 생성 모드가 다르면 재시작 안내 후 중단합니다. 기존 서버의 모델을 변경하려면
그 서버를 명시적으로 종료한 후 다시 실행해야 합니다.

다른 서비스나 장치가 쓰는 포트 연결을 덮어쓰거나 프로세스를 강제 종료하지 않습니다.
직접 시작한 백엔드·Ollama는 숨김 실행하고 Pleos 창은 표시합니다.
로그는 Git에서 제외되는 `.local/logs/`에 저장합니다. `READY`는 실행 환경 점검 결과이며,
AI 답변 생성 성공이나 화면의 시각 검증을 뜻하지 않습니다.

2026-10-27 실행 스크립트 검증:

- 실행 중인 Pleos·서버 재사용, Gradle debug 빌드, APK 재설치·MainActivity 실행 성공.
- 개발용 Pleos·백엔드를 종료한 상태에서 `-SkipBuild`로 부팅·서버 시작·연결·앱 실행 성공.
- 8088 forward와 8000 reverse를 제거하면 `-CheckOnly`가 실패하고, 실행 명령으로 복구됨.
- 생성 모드 불일치 시 기존 서버 PID를 유지한 채 종료 코드 1 반환. 없는 AVD 점검도 실패로 처리.
- 최종 점검에서 웹 콘솔·API 문서 HTTP 200, 앱 프로세스 실행 확인. 창 클릭·시각 검증은 미완료.

### Android Studio 실행

1. Android Studio에서 이 저장소의 **`android` 폴더**를 엽니다.
2. Gradle JDK를 Android Studio 내장 JDK로 지정하고 Gradle Sync를 실행합니다.
3. SDK 경로는 Android Studio가 생성하는 `local.properties`에서 관리합니다. Git에 올리지 않습니다.
4. Pleos 에뮬레이터가 완전히 부팅된 후 `app`을 실행합니다.
5. 주차 상태에서 `상세 화면 사용 가능`, 수신 결과, 마지막 유효 수신 시각을 확인합니다.
   권한·서비스 오류가 나면 오류 메시지를 확인하고 `다시 연결`로 재시도합니다.

Windows PowerShell에서는:

```powershell
cd android
.\gradlew.bat :app:assembleDebug :app:testDebugUnitTest :app:lintDebug
```

Linux/macOS에서는 해당 OS용 JDK와 Android SDK를 설치한 후:

```bash
cd android
./gradlew :app:assembleDebug :app:testDebugUnitTest :app:lintDebug
```

디버그 APK: `android/app/build/outputs/apk/debug/app-debug.apk`

## 차량 상태 모니터

`feature/vehicle-status-monitor`에서 구현합니다.

- `vehicle/PleosWarningSource`: SDK 연결, capability 조회, 초기/실시간 응답, 연결 세대별 늦은 콜백 무시
- `vehicle/WarningMonitor`: 일반 Kotlin 상태 처리, 중복 제거, 관측 공백 및 제한된 메모리 로그
- `vehicle/UxRestrictionSource`: AAOS 서비스와 UX 제한 상태 구독
- `history/HistoryDatabase`: 관측 구간·경고 이벤트 Entity, DAO, Room Database
- `history/HistoryRepository`: 프로세스 단일 DB 작업 큐, 세션 복구, 저장 및 페이지 조회
- `summary/ServiceSummary`: 기간 계산, 전체 집계 모델 및 관측 사실의 정형 요약
- `summary/SummaryPresenter`, `ServiceSummaryPanel`: 기간 선택, 비동기 조회, 주행 제한 및 화면 전환 처리
- `MainActivity`: 화면 생명주기 및 UI 연결

Telltales SDK 2.3.2 소스에서 capability/리스너는 `PRIVATE_CAR_SAFETY`를 요구합니다.
초기 조회의 annotation은 `CAR_SAFETY`, 설명은 PRIVATE 권한으로 서로 달라 두 권한을 선언했습니다.
이는 에뮬레이터 연동용 선언이며 실제 차량의 privileged 권한 부여나 App Market 승인을 의미하지 않습니다.
권한을 우회하거나 시스템 앱으로 설치하지 않습니다. 권한 오류는 확인 불가 상태로 표시합니다.

앱은 주차 상태를 기본으로 하며 `distractionOptimized`를 선언하지 않습니다.
앱이 화면에 보이는 동안 수신하고, 중단 구간은 관측 공백으로 남깁니다.
리스너 등록만으로 연결 성공이라고 표시하지 않으며 데이터가 없다는 시간만으로 연결 실패를 추정하지 않습니다.
초기 조회보다 실시간 콜백이 먼저 도착하면 늦은 초기 조회 결과/오류는 무시합니다.

목록에서 사라진 항목은 `목록 제외 관측 (해제 의미 미검증)`으로 기록합니다.
전체 스냅샷 계약 및 다중 경고 테스트 전까지 표시 해제·수리 완료로 단정하지 않습니다.
현재 시각 표시는 에뮬레이터에 설정된 시간대 기준입니다.

## 검증 기록 및 수동 시연

2026-10-23 검증:

- debug APK 빌드, 서명 전 release APK 빌드, Android Lint 통과
- 상태 처리 단위 테스트 8개 통과 (저장된 경고 종류 복원 포함): 중복, 목록 제외/재관측, null/공백, 다중 경고,
  상태 변경, 잘못된 중복 종류 입력, 로그 크기 제한
- 실행 중인 API 34 Pleos 에뮬레이터에 debug APK 설치·실행 성공
- 초기 조회와 리스너의 유효한 빈 목록 수신, 사용 제한 없음 상태 및 UI 표시 확인
- Room 에뮬레이터 테스트 2개 통과: DB 재열기, 중복 이벤트 ID 재저장, 미종료 세션 복구,
  정상 세션 종료, 같은 시각의 안정적 페이지 조회, FK 위반 시 저장 오류 반환
- 실제 TPMS ON을 DB 저장 후 앱 강제 종료·재실행: 기존 기록 유지 + 관측 공백 + 관측 재개 확인
- Lint에는 기존 의존성/SDK 버전의 업데이트 권고가 남아 있습니다.

2026-10-26 추가 검증 (`08a3616`, 앱 0.2.0, API 34 Pleos Emulator):

- debug 빌드·Lint 작업 성공 (변경 없는 작업은 Gradle 캐시 사용),
  상태 처리 단위 테스트 8개는 `--rerun-tasks`로 다시 실행해 통과
- 설치 APK와 로컬 debug APK의 SHA-256 일치 확인:
  `83ef586fac337c2ae0fb21589d75e1599f61d7100a09786ca21ab8d7eaadebd1`
- Virtual Console의 실제 제어 요청으로 TPMS ON → 동일 ON 2회 → OFF → ON 검증:
  화면·DB에 중복 이벤트 없이 목록 제외와 재관측 기록
- TPMS + ABS ON → TPMS만 OFF: SDK 콜백에 ABS가 남고 화면에서도 유지됨.
  이 조합에서 전체 목록 동작을 확인했으며 다른 환경까지 계약을 일반화하지 않음
- TPMS ON → BLINK: 원시 상태 표시와 `STATE_CHANGED` 저장 확인
- 설정 앱으로 이동 후 복귀: `SCREEN_STOPPED`, 관측 공백 및 경고별 관측 재개 확인.
  Home/Back 키만으로는 이 환경에서 앱이 숨겨지지 않아 화면 이탈 검증으로 사용하지 않음
- D단·30 km/h에서 상세 영역·재연결 접근 차단, 0 km/h·P단 복귀 후 상세 표시 확인
- 이력 화면을 연 상태에서도 주행 제한 시 숨김, 주차 복귀 후 같은 이력 화면 표시 확인
- 다시 연결 버튼: 기존 세션 `RECONNECT` 종료 및 새 수신 구간의 관측 재개 확인
- 이력 화면에서 과거 기록 유지 확인, 강제 종료·재실행 후 종료 기록 부재와 관측 재개 확인
- 강제 종료 후 DB·WAL을 함께 복사한 로컬 검사에서 `integrity_check=ok`,
  이벤트 42개와 고유 이벤트 ID 42개 확인 (복구 재실행 직전 스냅샷)
- 기존 앱 데이터는 삭제하지 않았으며 테스트에서 만든 관측 이력이 추가됨.
  종료 시 TPMS·ABS는 OFF, 기어 P·속도 0으로 복원

이번 검증은 [Virtual Console 공식 연결 방식](https://document.pleos.ai/en/docs/connect/guide/getting-started/application-development/use-vehicle-emulator)의
포트 전달 후, 로컬 콘솔 페이지가 사용하는 제어 요청으로 수행했습니다.
화면 XML과 SDK 로그는 Git 제외 경로 `docs/verification/2026-10-26/`에 보관합니다.
DB 파일·WAL은 이 증빙 폴더나 저장소에 넣지 않습니다.

다음 항목은 추가 확인해야 합니다.

- 차량 서비스·권한 오류의 실제 재현과 복구 (정상 재연결 검증과 별개)
- 다른 경고 조합과 제출용 서명 release APK에서의 동일 시나리오

수동 시연 재현 순서:

1. 주차 상태에서 TPMS ON → 경고 종류·ON·관측 시각이 나타나는지 확인
2. 동일 ON 반복 → 최근 변화 로그가 중복 추가되지 않는지 확인
3. TPMS OFF → 목록 제외 관측, 다시 ON → 재관측 표시 확인
4. 다른 경고와 동시 ON 후 하나만 OFF → 전체 목록인지 변경분인지 확인
5. 사용 제한 상태 전환 → 상세 화면/재연결 접근 차단 및 복귀 확인
6. 앱을 나갔다 돌아오기 → 수신 재개, 공백 중 해제 이력 미생성 확인
7. 차량 서비스/권한 오류 → 이전 정보 표시와 확인 불가 상태 확인

Logcat 태그: `CHECKMATE_VEHICLE`, `CHECKMATE_UX`.
위 단위 테스트는 실제 차량/SDK 계약 검증을 대신하지 않습니다.

## Room 저장 확인 방법

1. 새 버전을 실행하고 주차 상태에서 `로컬 DB 저장 완료`를 확인합니다.
2. Virtual Console에서 TPMS를 ON → OFF → ON으로 바꿉니다.
3. 앱의 **경고 이력 보기**를 누릅니다. 기존 상태에 따라 최초 관측 또는 관측 재개,
   목록 제외 관측, 재관측이 시간순으로 저장되어야 합니다.
4. 저장 완료를 확인한 뒤 앱을 중지하고 다시 실행합니다. **경고 이력 보기**에서
   이전 시각의 기록이 유지되는지 확인합니다. 신규 `관측 재개`는 새로운 고장 판정이 아닙니다.
5. 강제 종료 때에는 `이전 수신 구간의 종료 기록 없음`이 추가될 수 있습니다.
   정상적으로 화면을 나갔을 때에는 `관측 공백 시작`을 기록합니다.
6. 기록이 50개를 넘으면 **이전 기록 / 더 최근 기록**으로 페이지를 이동합니다.
   **최신 기록 새로고침**은 첫 페이지로 돌아갑니다.

DB는 앱 내부 `databases/checkmate-history.db`에 있습니다. SQLite WAL 모드를 사용하므로
실행 중 파일 하나만 복사하는 대신 Android Studio **App Inspection → Database Inspector**로 확인하세요.
테이블은 `observation_sessions`, `warning_events`입니다. 타임스탬프는 UTC epoch 밀리초이며
화면에서는 에뮬레이터에 설정된 시간대로 표시합니다.

DB 파일·저널은 Git/서버에 전송하지 않습니다. 앱 삭제 또는 데이터 지우기를 하면 기록이 삭제됩니다.
데이터 스키마 v1은 `android/app/schemas/`에 보존하며 자동 파괴 마이그레이션은 사용하지 않습니다.
추후 DB 구조 변경 시 명시적 migration을 추가해야 합니다.
저장 중 강제 종료하면 아직 커밋되지 않은 이벤트는 유실될 수 있으므로 확인은 `저장 완료` 후 수행하세요.

Room 통합 테스트는 테스트용 DB 이름을 사용합니다. 실제 이력에 테스트 경고를 삽입하지 않습니다.
Gradle의 connected test 실행 과정에서 앱이 제거될 수 있으므로 기존 기록이 중요한 에뮬레이터에서는
별도 테스트 AVD를 사용하세요.

```powershell
cd android
.\gradlew.bat :app:testDebugUnitTest :app:connectedDebugAndroidTest
```

## 제출 빌드

`assembleRelease`는 현재 서명되지 않은 APK를 생성합니다. 제출 전에 로컬 서명 설정으로
서명된 release APK를 생성하고 Pleos 에뮬레이터에서 다시 검증해야 합니다.
서명 키, API 키, `.env`, `local.properties`는 커밋하지 않습니다.
제출 시 APK는 `apk/` 또는 GitHub Releases에 두고 실행 방법과 시험 환경을 기록합니다.

## 공식 참고 문서

- [공모전 제출 안내](https://appdevchallenge.auto-hmg.io/guide/submission)
- [Pleos 앱 개발 시작](https://document.pleos.ai/en/docs/pleos-only/getting-started)
- [주행 제한 구현](https://document.pleos.ai/en/docs/pleos-only/vehicle-app-developer-guide/driving-restriction-development-guide)
- [하드웨어 접근 및 전화 기능 제한](https://document.pleos.ai/en/docs/pleos-only/vehicle-app-planning-guide/platform-api-architecture)

## 단계별 기능 확정 기록

### 1단계 이력과 오류 처리

- 실제 콘솔 경고 변경으로 누적 75개 이력을 만들고 UI의 1–50 / 51–75 페이지,
  앞뒤 이동, 최신 새로고침, 페이지 간 중복 없음, 주행 제한 후 페이지 이동 복구를 확인했습니다.
- 이력 조회 완료 시점에만 버튼 상태를 설정하던 부분을 수정했습니다.
  이제 조회 중 여부·페이지 범위·현재 UX 제한에 따라 활성 상태를 다시 계산합니다.
- 단위 테스트 9개, debug 빌드, Lint 통과.
  권한 오류·서비스 오류가 반복돼도 이전 관측값을 보존하고 공백을 한 번 기록한 후
  유효 수신 시 관측 재개로 복구하는 상태 처리 테스트를 포함합니다.
- 실제 `CAR_SAFETY` 권한 회수는 에뮬레이터에서 `not a changeable permission type`으로
  거부되었습니다. 권한 설정은 변경되지 않았습니다. 실제 SDK의 권한 오류 및 서비스 장애는
  미검증이며, 상태 처리 테스트 통과와 구분합니다.

### 2단계 매뉴얼 범위 확정

- 최초 지원 프로필: **2025 현대 아이오닉 5 / 전기차 / 대한민국 / 한국어**.
  공식 사이트의 프로젝트 코드 `NE1`. 2026-10-28부터 공식 PDF 취급설명서(최종 게시일
  2025-04-16, SHA-256 `7c92b1e3…6eb30725`)를 근거로 사용합니다. 이전 기준은 웹 문서 `rev=1.27`
  (확인일 2026-10-26)였으며, 저장된 선택이 유지되도록 프로필 ID는 바꾸지 않았습니다.
- [공식 차종 선택 페이지](https://ownersmanual.hyundai.com/manual/%EC%95%84%EC%9D%B4%EC%98%A4%EB%8B%89%205?countryCode=A99&langCode=ko_KR&projCode=NE1&year=2025)
- [TPMS 원문 PDF](https://ownersmanual.hyundai.com/full_pdf/NE1/2025/ko_KR): 시스템 개요(PDF 493쪽),
  저압 타이어 감지·시스템 이상(495쪽), 다른 점등 원인과 주의 사항(496쪽), 클러스터 경고등 표(138쪽)를
  검토 요약 5개로 사용합니다. 출처에는 문서명·절·PDF 쪽수를 표시합니다. 검토 근거는
  `data/manual-review/2026-10-28/hyundai-pdf-tpms-review.json`과 `hyundai-pdf-table-review.json`입니다.
  타이어 응급 처치 키트(TMK) 절차는 키트 사양 확인이 필요해 설명 범위에 넣지 않았습니다.
- 전자식 주차 브레이크(EPB) 원문 PDF(2026-10-29 추가): 개요·주의(331쪽), 비상 제동(332쪽),
  이상 시 대처·체결/해제 실패(333쪽), 클러스터 경고등 표(138쪽)를 검토 요약 5개로 사용합니다.
  SDK `ELECTRONIC_PARKING_BRAKE`의 `ON`만 설명합니다. 매뉴얼은 EPB 경고등을 '켜짐'으로만 설명하고
  깜빡임은 별도의 브레이크 경고등 동작이므로 `BLINK`는 설명하지 않습니다. 빨간 브레이크 경고
  (`PARKING_BRAKE`)는 브레이크액 부족·브레이크 이상과 겹쳐 아직 지원하지 않습니다.
  오프라인 안내는 `manual/ManualGuides`가 경고별로 제공하며 관측 순서 대조는 TPMS에만 적용합니다.
- **SDK `TPMS` 상태와 매뉴얼 분기 대조** (`manual/TpmsSignalMapping`). SDK는 `OFF/ON/BLINK`만 주고
  색상·시동 경과·타이어별 압력은 주지 않으므로, 앱은 현재 관측의 **순서만** 매뉴얼 설명과 대조해 표시하고
  저압·고장을 판정하지 않습니다. 과거 기록·관측 공백 이전 상태는 대조하지 않습니다.

  | 현재 관측 | 표시 | 확인할 수 없는 것 |
  |---|---|---|
  | 끊김 없는 수신에서 `BLINK` → `ON` | 시스템 이상 설명(깜빡인 뒤 켜짐, 표 기준 약 1분)과 같은 순서. BLINK 관측 시간 표시(시작 시 이미 BLINK면 "최소") | 실제 깜빡임 시간(수신 간격으로 잰 값) |
  | `BLINK` | 깜빡임은 시스템 이상 설명에 나오며 저압은 '켜짐'으로 설명됨 | 이후 켜지는지 |
  | 끊김 없는 수신에서 `BLINK` 없이 `ON` | 저압 감지는 '켜짐'으로 설명됨 | 시동 직후 약 3초 점검 점등, 앱이 놓친 짧은 깜빡임 |
  | 관측 시작·공백 직후 이미 `ON` | 저압과 시스템 이상을 구분할 수 없음 | 그 전 상태 전체 |
  | `OFF`, 목록 제외 | 대조하지 않음 | 정상·수리 완료 여부 |

  `BLINK` → 목록 제외 → `ON`은 깜빡인 뒤 켜짐으로 묶지 않습니다. 대조 결과는 서버 요청에 보내지 않으며
  서버 설명은 상태와 무관하게 같은 근거를 반환합니다.
- `manual/ManualCatalog`는 프로필과 원문 URL·SHA-256을 보존합니다.
  `ManualPreferences`는 사용자의 명시적 선택만 저장하며 처음에는 미선택입니다.
  알 수 없는 프로필 ID는 다른 차량으로 자동 대체하지 않습니다.
- 선택 프로필은 설명 자료의 범위입니다. 실제 연결 차량의 식별 결과나 에뮬레이터 차량 이미지의
  차종 판정을 의미하지 않습니다. 타이어 규격별 압력 수치는 이번 설명 범위에 포함하지 않습니다.
- 원문에 현대자동차 저작권 및 권리 유보가 명시되어 있습니다. 원문·이미지·PDF를 앱이나
  저장소에 재배포하지 않고, 직접 작성한 짧은 요약과 원문 링크·메타데이터만 사용합니다.
  원문 전체를 서버에 수집·임베딩하는 RAG 단계의 이용 조건은 별도로 확인해야 합니다.

### 3단계 화면 흐름

- 상단 `현재 경고 / 이력 / 매뉴얼` 이동을 고정하고, 경고 카드를 누르면 상세로 이동합니다.
- 이력의 경고 기록을 누르면 `과거 관측 기록`으로 표시합니다. 공백 기록은 설명 대상으로
  잘못 선택되지 않도록 일반 텍스트로 표시합니다.
- 매뉴얼 선택·해제·선택한 경고로 복귀, 선택 프로필의 재실행 후 유지가 가능합니다.
- 상세에서 경고가 목록에서 사라지면 선택 당시 정보임을 표시하고, 수신이 중단되면
  현재 상태 확인 불가를 표시합니다. 최근 변화 로그는 펼치기로 분리했습니다.
- 에뮬레이터에서 현재→상세→프로필→상세, 이력→과거 상세,
  상세 화면의 주행 제한·주차 복귀, 강제 종료 후 프로필 복원을 확인했습니다.
  debug 빌드·Lint 및 단위 테스트 11개 통과.

### 4단계 TPMS 매뉴얼 설명

- 앱 0.3.0: `현재 경고 → TPMS 카드 → 상세` 또는 `이력 → TPMS 기록`에서
  관측 사실, 선택 프로필, 직접 작성한 매뉴얼 요약, 확인 불가 정보, 원문 출처를 구분합니다.
- `매뉴얼`에서 2025 아이오닉 5 프로필을 선택해야 설명을 표시합니다.
  선택 없음·알 수 없는 프로필·지원하지 않는 경고(예: ABS)·지원하지 않는 상태는
  다른 설명을 재사용하지 않고 각각의 사유를 표시합니다.
- ON 또는 BLINK는 SDK 관측값입니다. 하나의 원시 상태값만으로 저압·시스템 고장을
  단정하지 않고, 매뉴얼에 설명된 저압 경고 및 깜빡임 후 점등 패턴과 구분합니다.
- 원문 출처는 문서명·절·버전·확인일·HTTPS URL입니다. `현대 공식 원문 열기`는
  외부 앱으로 연결하며, 실행할 앱이 없거나 제한된 경우 안내를 표시합니다.
  현재 Pleos 에뮬레이터에는 해당 링크를 여는 앱이 없어 대체 안내 표시까지 확인했습니다.
- 설명은 앱에 포함된 검토 요약으로 서버·API 키 없이 동작합니다. AI 생성·RAG 기능은 아닙니다.
- 단위 테스트 15개, debug 빌드·Lint 통과. 에뮬레이터에서 설명·출처, 프로필 해제 후
  설명 차단, 재선택 후 복원, ABS 미지원, BLINK 한계 안내, 과거 상세, 주행 제한·복귀를 확인했습니다.

확인 순서: `매뉴얼 → 2025 현대 아이오닉 5 선택 → 현재 경고 → TPMS ON → TPMS 카드`.
TPMS가 꺼져 있어도 `이력`의 TPMS 기록에서 과거 관측에 대한 설명을 확인할 수 있습니다.
주행 제한 시에는 프로필 변경·설명·원문 열기·이력 탐색 모두 상세 영역과 함께 차단됩니다.

### 기본 UI 정리

- 시스템 `sans-serif`를 XML/AppCompat 테마와 동적 경고 카드에 명시했습니다.
  현재 Pleos 에뮬레이터의 시스템 설정은 이 계열을 Asta Sans로 연결합니다.
  폰트 파일을 앱에 복사하지 않으며 다른 기기에서는 해당 기기의 시스템 글꼴을 사용합니다.
- 선택된 메뉴 강조, 제목·본문·보조 정보의 크기 구분, 둥근 버튼과 카드 여백을 적용했습니다.
- 본문은 가용 폭 안에서 최대 1080dp로 표시해 긴 설명의 줄 길이를 줄였습니다.
- 상세의 관측 사실·매뉴얼 설명·확인 불가 정보·출처를 별도 카드로 구분했습니다.
- 상세 진입 시 화면 상단으로 이동하도록 초점·스크롤 처리를 보완했습니다.
- debug 빌드·Lint(오류 0개), 에뮬레이터 메뉴 이동·과거 상세·출처 스크롤·프로필 화면 확인 완료.


### 서버 설명 연결 (앱 0.4.0)

TPMS 상세에서 **서버 설명 요청**을 누르면 선택 프로필·경고 종류·원시 상태와 요청 ID만
전송합니다. 위치·VIN·전체 이력·메모는 보내지 않습니다. 요청 중에도 로컬 요약을 유지하고,
성공하면 인용 번호가 있는 서버 설명으로 전환합니다. 실패하면 로컬 요약과 재요청 안내를 표시합니다.
**로컬 요약 사용**으로 취소할 수 있으며 화면·프로필·관측값 변경, 주행 제한, 화면 종료 시
이전 요청의 결과를 적용하지 않습니다. 관측 사실은 계속 SDK 데이터로 표시합니다.

로컬 실행 (저장소 루트, Ollama에 `qwen2.5:7b`가 설치된 환경):

```bash
CHECKMATE_GENERATION=ollama uv run --directory backend uvicorn checkmate.main:app --host 127.0.0.1 --port 8000
```

에뮬레이터와 연결된 호스트에서 Android SDK의 adb로 실행합니다.
WSL 서버를 사용할 때 Windows에서도 localhost:8000에 접근할 수 있어야 합니다.

```text
adb reverse tcp:8000 tcp:8000
```

`매뉴얼 → 2025 아이오닉 5 선택 → TPMS 현재/과거 상세 → 서버 설명 요청`으로 확인합니다.
TPMS가 꺼져 있으면 이력의 TPMS ON/BLINK 기록을 사용할 수 있습니다.
서버 없이도 기존 오프라인 기능은 동작합니다. 서버 모드 기본값은 검토 요약 검색이며,
`CHECKMATE_GENERATION=ollama`일 때만 모델을 호출합니다. 상세 설정은 [서버 README](backend/README.md)를 참조하세요.

Debug는 localhost HTTP만 허용합니다. Release는 기본적으로 서버 버튼을 숨기며
`-PcheckmateServerUrl=https://서버호스트`로 HTTPS origin을 지정해 빌드합니다.
Release APK는 아직 미서명이며 공개 서버 배포는 포함하지 않습니다.

현재 근거는 직접 작성한 검토 요약 3개입니다. Qwen 연결은 실제로 동작하지만
공식 매뉴얼 전체를 수집한 RAG나 임베딩 검색이 완성된 것은 아닙니다.

2026-10-26 검증: Android 단위 테스트 19개, backend 테스트 27개 통과.
Debug·미서명 release 빌드 및 debug Lint 성공(오류 0, 기존 업데이트/리소스 권고 등 경고 유지).
Pleos API 34 에뮬레이터에서 실제 Qwen 설명·인용 표시, 로컬 요약 복귀,
연결 실패 안내, 요청 후 화면 이동, 주행 제한 중 상세 차단과 주차 복귀 후
이전 응답 미적용을 확인했습니다. 종료 시 P단·속도 0·TPMS OFF로 복원했습니다. 테스트 중 기존 앱 데이터는 유지했습니다.

### 정비 전달용 관측 요약 (앱 0.5.0)

`이력 → 정비 전달용 요약`에서 **오늘 / 최근 7일 / 최근 30일**을 선택합니다.
기간은 기기 시간대의 오늘을 포함한 달력 날짜 기준이며, 조회 버튼을 누른 시각까지의
저장 기록을 정리합니다. 기본값은 최근 7일이고 화면 재생성 시 선택 기간을 복원합니다.

- 선택 기간의 전체 기록을 경고별로 집계합니다. 원시 상태, 기간 내 첫·마지막 기록,
  최초 관측·상태 변경·재관측·관측 재개·목록 제외 기록 수를 표시합니다.
- 수신 중단과 이전 수신 구간의 종료 시각 미확인 기록을 구분합니다.
  공백 기록이 0개여도 연속 관측을 보장하지 않으며, 기간 이전부터 유지된 경고는
  새 변화가 없으면 이번 기간의 요약에 포함되지 않을 수 있습니다.
- 최근 변화 상세는 최신순 50개까지 표시하고 생략된 수를 안내합니다.
  경고별 집계와 전체 건수에는 상세 표시 한도와 관계없이 모든 해당 기록이 포함됩니다.
- 집계·건수·상세 조회는 하나의 DB 트랜잭션으로 처리합니다. DB 스키마는 v1을 유지하며
  이 기능은 기존 데이터를 읽기만 합니다. 요약은 서버나 모델 호출 없이 생성합니다.
- 새 기록은 **요약 새로고침**으로 반영합니다. 기간 변경·화면 이동·주행 제한 시
  늦은 조회 결과를 적용하지 않으며, 주차 복귀 후 현재 선택 기간을 다시 조회합니다.
- 목록 제외의 상태값은 `제외 전 기록 상태`로 표시합니다. 관측 횟수·시각을 고장 횟수나
  고장 지속 시간으로 해석하지 않습니다. 사용자 메모·파일 내보내기는 아직 포함하지 않습니다.

2026-10-27 로컬 검증:

- Windows의 한글 JSON 읽기에 UTF-8을 명시했습니다. UTF-8 강제 실행 옵션 없이
  Anaconda Python 3.13.9에서 카탈로그·계약 테스트 9개 통과.
- Android Studio에 포함된 Kotlin 2.3.10과 JUnit 4.13.2로 기존 19개와 새 요약 테스트 12개,
  총 31개 JVM 테스트 통과. 이 직접 실행은 캐시된 JSON 20180813을 사용했으며,
  프로젝트의 Gradle 의존성 전체를 해석한 Android 빌드 검증과는 구분합니다.
- 실제 DAO SQL을 저장된 v1 스키마로 만든 메모리 SQLite에 실행해 기간 경계, 전체 59개
  집계와 50개 상세 한도, 같은 시각 정렬, 빈 기간, 공백 및 조회 전후 데이터 일치를 확인했습니다.
- 설치된 SDK Build Tools 36.0.0의 AAPT2로 리소스 컴파일 통과.
- 초기에는 네트워크 권한 제한으로 전체 실행 환경을 준비하지 못했으나, 이후 의존성을 설치하고
  Gradle `:app:assembleDebug :app:testDebugUnitTest :app:lintDebug`를 정상 완료했습니다.
  프로젝트 의존성을 사용한 Android 단위 테스트 31개와 백엔드 테스트 27개가 통과했습니다.
- 별도 `Checkmate_Pleos_API_34` AVD(Pleos Connect 2.1.0)에 앱을 설치했습니다.
  기존 이력 테스트 2개와 새 요약 Room 통합 테스트 1개가 실제 에뮬레이터에서 통과했습니다.
  ADB에서 MainActivity 실행 상태를 확인했습니다. UI 자동 조작 권한이 없어 새 요약 화면의
  클릭·시각 검증은 수행하지 못했습니다.
- 실제 Qwen2.5:7b TPMS ON 요청에서 READY / AI_GENERATED, 설명 3개·인용 3개 응답을
  확인했습니다(45.38초, 첫 요청은 타임아웃). 이 결과는 지연 시간 보장이 아닙니다.

2026-10-28 추가 검증 (앱 0.5.0, Pleos Connect 2.1.0 / API 34):

- 이번에는 UI 조작이 가능해 `현재 경고 → 이력 → 정비 전달용 요약`을 실제 화면에서 확인했습니다.
  오늘·최근 7일·최근 30일 선택, 본문 줄바꿈, 스크롤과 마지막 안내 문구를 확인했습니다.
  날짜는 에뮬레이터의 `America/Los_Angeles` 시간대 기준입니다.
- Virtual Console API로 TPMS ON → BLINK → OFF → ON을 입력하고 SDK 수신 화면과 실제 Room
  데이터베이스를 대조했습니다. 각각 재관측·상태 변경·목록 제외·재관측으로 저장됐으며,
  동일 ON을 두 번 더 입력해도 기록 수가 증가하지 않았습니다. DB 무결성 검사도 통과했습니다.
- 새 기록 저장 후 요약 새로고침으로 전체 20개 → 21개 반영을 확인했습니다.
  OFF는 `제외 전 기록 상태 BLINK · 목록 제외 관측`으로 표시되고 수리 완료로 표현되지 않았습니다.
- 30일 요약을 연 상태에서 D / 20km/h를 입력하면 Pleos의 `주행 중에는 사용할 수 없습니다`
  화면으로 차단됐습니다. P / 0km/h 복귀 후 30일 선택을 유지하고 조회 시각이 갱신됐습니다.
  조회 완료와 제한 전환 사이의 경쟁 조건은 기존 SummaryPresenter 단위 테스트로 검증합니다.
- 별도 `Checkmate_Verification_Empty_API_34` AVD에서 기존 사용자 데이터와 분리해 빈 이력을
  확인했습니다. DB 0건과 화면의 전체 변화 0개·경고 종류 0개·상세 0개가 일치하며,
  `선택 기간에 저장된 경고 변화 기록이 없습니다. 차량 정상 여부를 뜻하지 않습니다.`가 표시됐습니다.
- 기존 AVD를 종료·재부팅한 뒤 이전 이력 22개를 모든 필드로 비교해 동일함을 확인했습니다.
  재시작에 따른 관측 공백 2개가 추가됐고 기존 기록은 보존됐습니다. 마지막에는 기존 AVD와 앱을
  다시 실행하고 P / 0km/h / TPMS OFF, 콘솔·API 응답과 앱 프로세스를 확인했습니다.
- 백엔드 테스트 27개를 다시 실행해 통과했습니다. Starlette/httpx 사용 중단 예정 경고 1개가 있으며
  실패는 없습니다. 앞서 완료한 Android 단위 테스트 31개, Room 통합 테스트 3개 및 빌드·Lint 결과와
  이번 UI 검증을 구분해 기록합니다. 앱 소스 변경 없이 화면 검증을 보완했습니다.

위 결과는 에뮬레이터의 기능 검증입니다. 실차 검증이나 전체 자동차 매뉴얼에 대한 검색·답변
품질 검증은 포함하지 않습니다. 현재 근거는 검토 요약 3개이며 임베딩·벡터 검색은 아직 없습니다.

실행 중인 로컬 서비스 주소:

- Pleos 차량 조작 웹 콘솔: http://127.0.0.1:8088/
- CHECKMATE API 문서: http://127.0.0.1:8000/docs

웹 콘솔에는 에뮬레이터 부팅 후 `adb -s emulator-5554 forward tcp:8088 tcp:8088` 연결이
필요합니다. 앱의 로컬 서버 연결에는 `adb -s emulator-5554 reverse tcp:8000 tcp:8000`을
사용합니다. 장치 일련번호는 `adb devices` 출력에 맞추세요. 두 주소 모두 개발 PC 전용이며,
CHECKMATE 앱 화면은 Pleos 에뮬레이터에서 실행됩니다.
