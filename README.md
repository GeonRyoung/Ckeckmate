# CHECKMATE

Pleos 차량 경고를 매뉴얼 기반 설명, 관측 이력, 정비 전달용 요약으로 연결하는 Android 앱입니다.

## 현재 상태

- Kotlin + XML / View Binding 기반 현재 경고 화면
- Pleos Vehicle SDK 2.3.2: capability 확인, 초기 조회, 실시간 리스너, 화면 종료 시 해제
- 경고 종류·원시 상태·관측 시각·마지막 수신 시각 표시
- 오류/null과 유효한 빈 목록 구분, 반복 상태 중복 제거, 관측 공백 표시
- `CarUxRestrictions` 확인 전 또는 제한 중에는 상세 영역과 재연결 조작 차단
- 최근 50개 관측 변화는 메모리에만 보관 (프로세스 종료·Activity 재생성 시 초기화)
- Room 영속 저장, FastAPI, RAG는 후속 구현
- 근처 현대·기아 정비점 검색 및 전화 연결은 지원 여부 검증 후 추가할 옵션

## 프로젝트 구조

```text
android/                 Android Studio에서 열 프로젝트
  app/src/main/          Kotlin 코드, 화면 리소스, Manifest
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
- 상태 처리 단위 테스트 7개 통과: 중복, 목록 제외/재관측, null/공백, 다중 경고,
  상태 변경, 잘못된 중복 종류 입력, 로그 크기 제한
- 실행 중인 API 34 Pleos 에뮬레이터에 debug APK 설치·실행 성공
- 초기 조회와 리스너의 유효한 빈 목록 수신, 사용 제한 없음 상태 및 UI 표시 확인
- Lint에는 기존 의존성/SDK 버전의 업데이트 권고가 남아 있습니다.

다음 항목은 실제 Virtual Console 조작으로 추가 확인해야 합니다.

1. 주차 상태에서 TPMS ON → 경고 종류·ON·관측 시각이 나타나는지 확인
2. 동일 ON 반복 → 최근 변화 로그가 중복 추가되지 않는지 확인
3. TPMS OFF → 목록 제외 관측, 다시 ON → 재관측 표시 확인
4. 다른 경고와 동시 ON 후 하나만 OFF → 전체 목록인지 변경분인지 확인
5. 사용 제한 상태 전환 → 상세 화면/재연결 접근 차단 및 복귀 확인
6. 앱을 나갔다 돌아오기 → 수신 재개, 공백 중 해제 이력 미생성 확인
7. 차량 서비스/권한 오류 → 이전 정보 표시와 확인 불가 상태 확인

Logcat 태그: `CHECKMATE_VEHICLE`, `CHECKMATE_UX`.
위 단위 테스트는 실제 차량/SDK 계약 검증을 대신하지 않습니다.

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
