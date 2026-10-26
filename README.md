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
- FastAPI, RAG, 사용자 메모·정비 요약은 후속 구현
- 근처 현대·기아 정비점 검색 및 전화 연결은 지원 여부 검증 후 추가할 옵션

## 프로젝트 구조

```text
android/                 Android Studio에서 열 프로젝트
  app/src/main/          Kotlin 코드, 화면 리소스, Manifest
  app/schemas/           Room DB 버전별 스키마 (Git 관리)
  gradle/                버전 카탈로그 및 Gradle Wrapper
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
  공식 사이트의 프로젝트 코드 `NE1`, 웹 문서 `rev=1.27`, 확인일 2026-10-26.
- [공식 차종 선택 페이지](https://ownersmanual.hyundai.com/manual/%EC%95%84%EC%9D%B4%EC%98%A4%EB%8B%89%205?countryCode=A99&langCode=ko_KR&projCode=NE1&year=2025)
- [TPMS 원문](https://ownersmanual.hyundai.com/full_webhelp/NE1/2025/ko_KR/id23C5E0QD0YK.html):
  시스템 개요, `저압 타이어 감지`, `타이어 공기압 경보 시스템 이상`을 설명 범위로 사용합니다.
  HTML 문서이므로 임의의 PDF 페이지를 표시하지 않고 문서명·절·URL을 출처로 표시합니다.
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
