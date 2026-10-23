# CHECKMATE

Pleos 차량 경고를 매뉴얼 기반 설명, 관측 이력, 정비 전달용 요약으로 연결하는 Android 앱입니다.

## 현재 상태

- Kotlin + XML / View Binding 기반 Android 프로젝트와 시작 화면
- Pleos Vehicle SDK 2.3.2 의존성 설정
- 차량 데이터는 아직 연결하지 않았으며 시작 화면에 미연결 상태를 표시합니다.
- TPMS 수신, 사용 제한 연동, Room, FastAPI, RAG는 후속 구현입니다.
- 근처 현대·기아 정비점 검색 및 전화 연결은 지원 여부 검증 후 추가할 옵션입니다.

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
5. CHECKMATE의 `현재 경고`와 `차량 데이터 미연결` 문구를 확인합니다.

Windows PowerShell에서는:

```powershell
cd android
.\gradlew.bat :app:assembleDebug :app:lintDebug
```

Linux/macOS에서는 해당 OS용 JDK와 Android SDK를 설치한 후:

```bash
cd android
./gradlew :app:assembleDebug :app:lintDebug
```

디버그 APK: `android/app/build/outputs/apk/debug/app-debug.apk`

## 첫 기능 브랜치

`feature/vehicle-status-monitor`에서 다음 순서로 구현합니다.

1. Vehicle SDK 수신부를 Activity와 분리하고 필요한 권한을 검증
2. 초기 TPMS 조회와 실시간 리스너 연결, 종료 시 등록 해제
3. 연결 오류·null·유효한 빈 목록을 구분하고 중복 이벤트 제거
4. `CarUxRestrictions`에 따른 화면 사용 제한 반영
5. ON → OFF → ON 및 다중 경고 스냅샷 동작 검증

현재 앱은 주차 상태를 기본으로 하며 `distractionOptimized`를 선언하지 않습니다.
SDK를 연결하거나 차량 상태가 정상이라고 표시하는 기능은 아직 없습니다.
기존 시험 앱의 PRIVATE 권한은 승인 범위 확인 전 자동으로 복사하지 않습니다.

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
