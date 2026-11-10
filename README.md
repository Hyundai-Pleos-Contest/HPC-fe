# HPC-fe

현대자동차그룹 Pleos 공모전을 위한 Kotlin + Jetpack Compose 차량용 Android 앱의 초기 개발 환경이다. 현재 앱에는 초기 화면만 있고 차량 조회·제어, 백엔드 호출, AI 서비스 기능은 없다.

## 고정 환경

| 구성 | 버전 |
| --- | --- |
| 빌드 JDK | 21 (Java/Kotlin bytecode target 17) |
| Gradle Wrapper | 8.11.1 |
| Android Gradle Plugin | 8.10.1 |
| Kotlin / Compose compiler | 2.2.21 |
| Compose BOM | 2025.05.01 |
| compileSdk / targetSdk / minSdk | 35 / 34 / 28 |
| Android Build Tools | 35.0.0 |
| Pleos 에뮬레이터 | 2.1.0, Android API 34 |
| 선택 Vehicle SDK | 2.3.1 (공식 문서 좌표, 실제 배포 접근 확인 필요) |

AGP 8.10의 최소 JDK는 17이고 Gradle 8.11.1을 요구한다. Kotlin 2.2의 D8/R8 지원을 위해 AGP 8.10 계열을 사용한다. 이 저장소의 개발·CI는 JDK 21로 통일한다. Android Studio 내장 JBR이 다른 버전이면 Settings > Build Tools > Gradle의 Gradle JDK를 21로 지정한다. SDK 35는 컴파일용이며 실행 검증 대상 Pleos 이미지는 API 34다. targetSdk는 현재 Pleos 검증 목표 34이며 향후 배포 조건 확인 후 갱신한다.

## 시작

1. JDK 21, Android Studio를 설치하고 Android SDK Platform 35와 Build Tools 35.0.0을 준비한다.
2. Android Studio에서 이 저장소를 연다. SDK 경로는 로컬 `local.properties`의 `sdk.dir` 또는 `ANDROID_HOME`에 설정한다. `local.properties`는 커밋하지 않는다.
3. 기본 Build Variant인 `mockDebug`를 선택한다. 일반 Android 에뮬레이터나 Pleos 에뮬레이터에서 초기 화면을 확인할 수 있다.

Windows Android 도구의 경로 호환성을 위해 새 clone과 SDK 경로는 영문 경로를 권장한다. 현재 한글 상위 폴더에서 작업할 수 있도록 `android.overridePathCheck=true`를 설정했지만, AAPT2가 SDK 경로에 `Illegal byte sequence` 경고를 출력할 수 있다. 특정 도구가 실제로 실패하면 ASCII 경로에서 다시 검증한다.

```powershell
.\gradlew.bat :app:assembleMockDebug :app:lintMockDebug :app:testMockDebugUnitTest
```

macOS/Linux에서는 `bash ./gradlew`를 사용한다. APK는 `app/build/outputs/apk/mock/debug/`에 생성된다. `testMockDebugUnitTest`는 테스트가 추가될 때 실행하며 현재 서비스 로직/단위 테스트가 없어 NO-SOURCE일 수 있다. CI도 mock 빌드·Android Lint·단위 테스트 작업을 실행하고 APK를 보관한다. 에뮬레이터 실행 검증은 별도다.

## Pleos SDK와 에뮬레이터

기본 빌드는 Pleos 저장소에 접근하지 않는다. 공식 빠른 시작 문서는 `ai.pleos.playground:Vehicle:2.3.1`을 제시하지만 초기 환경 점검에서 해당 POM URL은 HTTP 404를 반환했다. SDK 버전을 임의 추정하거나 비공식 파일로 대체하지 않고, Playground의 프로젝트 권한/배포 안내를 확인한다.

접근 가능한 공식 SDK를 확인한 후 다음과 같이 `pleos` flavor를 활성화한다.

```powershell
.\gradlew.bat -PenablePleos=true :app:assemblePleosDebug :app:lintPleosDebug
```

`pleos` flavor는 공식 Maven 의존성과 Automotive 전용 manifest를 추가하지만 아직 SDK API 호출은 구현하지 않는다. 성공적으로 빌드되어도 차량 연결 검증 완료를 의미하지 않는다. SDK 접근이 안 되는 상태에서 위 명령의 실패는 mock 개발·CI와 분리된다.

Windows/Linux SDK Update Site:

```text
https://nexus-playground.pleos.ai/repository/raw-releases/connect-avd/2.x/crp-sys-img.xml
```

Android Studio SDK Manager에서 위 사이트를 추가하고 API 34 Pleos Connect 2.1.0 시스템 이미지를 설치한다. Automotive AVD를 만들고 Cold boot, RAM 4GB로 설정한다. 에뮬레이터 이미지는 저장소에 포함하지 않는다.

실제 차량 기능을 추가할 때는 SDK/AAOS 접근을 data 계층 어댑터로 분리하고 fake 구현과 동일한 인터페이스를 사용한다. 초기 단계에서 가짜 속도·위치·제어 성공 값을 제공하지 않는다. 지원 API, permission, capability, 주행 제한과 차량 연결 수명주기를 먼저 검증한다. Vehicle State/NaviHelper와 달리 일부 SDK는 제공 준비 중이므로 포털의 현재 상태를 다시 확인한다.

## 백엔드 주소와 비밀

Android 앱은 `.env` 파일을 자동으로 읽지 않는다. 다음 Gradle property가 `BuildConfig.API_BASE_URL`에 들어간다. 아직 네트워크 클라이언트는 구현하지 않았다.

| 설정 | 기본값 | 용도 |
| --- | --- | --- |
| `apiBaseUrl` | `http://10.0.2.2:8080` | debug에서 호스트의 HPC-be 연결 |
| `releaseApiBaseUrl` | `https://api.example.invalid` | release의 명시적 미설정 placeholder |

```powershell
.\gradlew.bat :app:assembleMockDebug -PapiBaseUrl=https://dev.example.com
.\gradlew.bat :app:assembleMockRelease -PreleaseApiBaseUrl=https://api.example.com
```

반복 설정은 개인 `~/.gradle/gradle.properties`에 둘 수 있다. debug의 HTTP는 에뮬레이터 호스트 `10.0.2.2`에만 허용하며 release에는 cleartext 허용 설정이 포함되지 않는다. 실제 기기 개발은 HTTPS 주소를 사용한다. URL에 자격증명·query·fragment는 허용하지 않는다. BuildConfig 값은 APK에서 추출할 수 있으므로 SDK secret/API key를 넣지 않는다. 배포 전에 실제 HTTPS 주소와 서명을 별도로 설정해야 하며 현재 release APK는 서명되지 않는다.

## 구조와 협업

- `app/src/main`: 공통 초기 화면
- `app/src/mock`: 차량 연결이 없는 기본 실행 환경
- `app/src/pleos`: 선택 SDK 환경 및 Automotive 요구사항
- `app/src/debug`: 로컬 에뮬레이터용 네트워크 예외
- `gradle/libs.versions.toml`: 의존성 버전
- `AGENTS.md`: Codex·Claude 공통 작업 지침
- `CONTRIBUTING.md`: Git Flow·커밋·PR 규칙

공모전 제출 시 검증된 소스 tag/commit과 APK를 같은 GitHub Release에서 연결하고 설치·시연 절차를 기록한다. CI mock APK는 차량 SDK 구현 완료 산출물이 아니다. API/통합 환경과 전체 제출 버전은 `HPC-workspace`에서 관리한다.

## 공식 근거

- [Pleos 시작 가이드](https://document.pleos.ai/en/docs/pleos-only/getting-started)
- [Pleos 에뮬레이터 환경](https://document.pleos.ai/en/docs/connect/guide/getting-started/application-development/setup-connect-sdk-emulator)
- [SDK 접근 상태](https://document.pleos.ai/en/docs/pleos-only/create-my-project)
- [AGP 8.10 호환성](https://developer.android.com/build/releases/agp-8-10-0-release-notes)
- [Kotlin D8/R8 지원](https://developer.android.com/build/kotlin-support)
- [Kotlin Gradle 호환성](https://kotlinlang.org/docs/gradle-configure-project.html)
