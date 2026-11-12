# HPC-fe

현대자동차그룹 Pleos 공모전을 위한 Kotlin + Jetpack Compose 차량용 Android 앱의 초기 개발 환경이다. 현재 앱에는 초기 화면만 있고 차량 조회·제어, 백엔드 호출, AI 서비스 기능은 없다.

## 고정 환경

| 구성 | 버전 |
| --- | --- |
| 빌드 JDK | 21 (Java/Kotlin bytecode target 17) |
| Gradle Wrapper | 8.14.6 |
| Android Gradle Plugin | 8.10.1 |
| Kotlin / Compose compiler | 2.2.21 |
| Compose BOM | 2025.05.01 |
| compileSdk / targetSdk / minSdk | 35 / 34 / 28 |
| Android Build Tools | 35.0.0 |
| Pleos 에뮬레이터 | 2.1.0, Android API 34 |
| 선택 Vehicle SDK | 2.3.2 |
| AndroidX Test runner / JUnit extension | 1.7.0 / 1.3.0 (Pleos debug 계측 테스트용) |

AGP 8.10의 최소 JDK는 17, 최소 Gradle은 8.11.1이다. 이 저장소는 Gradle 8.x 보안 수정이 포함된 8.14.6으로 고정한다. Kotlin 2.2의 D8/R8 지원을 위해 AGP 8.10 계열을 사용한다. 개발·CI는 JDK 21로 통일한다. Android Studio 내장 JBR이 다른 버전이면 Settings > Build Tools > Gradle의 Gradle JDK를 21로 지정한다. SDK 35는 컴파일용이며 실행 검증 대상 Pleos 이미지는 API 34다. targetSdk는 현재 Pleos 검증 목표 34이며 향후 배포 조건 확인 후 갱신한다.

## 시작

1. JDK 21, Android Studio를 설치하고 Android SDK Platform 35와 Build Tools 35.0.0을 준비한다.
2. Android Studio에서 이 저장소를 연다. SDK 경로는 로컬 `local.properties`의 `sdk.dir` 또는 `ANDROID_HOME`에 설정한다. `local.properties`는 커밋하지 않는다.
3. 기본 Build Variant인 `mockDebug`를 선택한다. 일반 Android 에뮬레이터나 Pleos 에뮬레이터에서 초기 화면을 확인할 수 있다.

Windows Android 도구의 경로 호환성을 위해 새 clone과 SDK 경로는 영문 경로를 권장한다. 현재 한글 상위 폴더에서 작업할 수 있도록 `android.overridePathCheck=true`를 설정했지만, AAPT2가 SDK 경로에 `Illegal byte sequence` 경고를 출력할 수 있다. 특정 도구가 실제로 실패하면 ASCII 경로에서 다시 검증한다.

```powershell
.\gradlew.bat :app:assembleMockDebug :app:lintMockDebug :app:testMockDebugUnitTest
```

macOS/Linux에서는 `bash ./gradlew`를 사용한다. APK는 `app/build/outputs/apk/mock/debug/`에 생성된다. `testMockDebugUnitTest`는 테스트가 추가될 때 실행하며 현재 서비스 로직/단위 테스트가 없어 NO-SOURCE일 수 있다. CI의 `verify`는 mock 빌드·Android Lint·단위 테스트 작업을 실행한 다음, 공개 Vehicle SDK를 사용하는 Pleos 앱·계측 APK 빌드와 Lint를 검사한다. `mock-debug-apk`, `pleos-debug-apk`, `pleos-debug-android-test-apk`를 각각 14일간 보관한다. CI는 AVD 설치나 계측 테스트 실행을 하지 않으며 런타임 검증은 별도다. 로컬 기본 빌드는 계속 `mock`이다.

## Pleos SDK와 에뮬레이터

반복 실행은 [공용 Pleos 도구](docs/local-tools.md)의 `python scripts/pleos.py`를 사용할 수 있다.
SDK/AVD 설치 뒤 `doctor → start → build → test → launch → stop`을 제공한다.
Python 3.12 이상이 필요하며, 아래의 직접 Gradle/adb 명령도 계속 사용할 수 있다.

기본 빌드는 Pleos 저장소에 접근하지 않는다. 선택 `pleos` flavor는 공식 가져오기 문서와 공개 Maven 메타데이터에 맞춰 `ai.pleos.playground:Vehicle:2.3.2`를 사용한다. 빠른 시작 문서에 남아 있는 2.3.1의 POM은 404지만 2.3.2 POM·module·AAR은 인증 없이 200을 반환한다. 2.3.2 AAR은 983,759 bytes이며 SHA-256은 `e11fdfe498cad3ecc0d5a2a6992b0c4a4d135195f1455018127bc069fd5ef937`이다. 실제 다운로드와 공식 checksum의 일치를 확인했다.

다음 명령으로 `pleos` flavor와 읽기 전용 계측 테스트 APK를 빌드한다.

```powershell
.\gradlew.bat -PenablePleos=true :app:assemblePleosDebug :app:assemblePleosDebugAndroidTest :app:lintPleosDebug
```

일반 앱 UI는 초기 화면만 표시하며 SDK 호출을 하지 않는다. 별도 debug 계측 테스트만 Vehicle SDK를 초기화하고 Door `ROW_1_LEFT`의 capability 및 현재 상태를 읽는다. SDK AAR이 요구하는 최소 Vehicle Service는 2.3.13(code 65)이고, 공식 샘플 기준은 SDK 2.3.2 / Service 2.3.22 / AVD 2.1(Android 14)다. 단순 빌드 성공이나 `initialize()` 반환은 서비스 연결 성공이 아니다.

Windows/Linux SDK Update Site:

```text
https://nexus-playground.pleos.ai/repository/raw-releases/connect-avd/2.x/crp-sys-img.xml
```

Android Studio SDK Manager에서 위 사이트를 추가하고 API 34 Pleos Connect 2.1.0 시스템 이미지를 설치한다. Automotive AVD를 만들고 Cold boot, RAM 4GB로 설정한다. 에뮬레이터 이미지는 저장소에 포함하지 않는다.

에뮬레이터가 완전히 부팅된 뒤 `adb devices`에서 대상 serial을 확인한다. 아래 `<PLEOS_SERIAL>`을 그 값으로 바꾸고 저장소 루트에서 실행한다. 실제 기기나 일반 Android 이미지를 대상으로 실행하지 않는다.

```powershell
$env:ANDROID_SERIAL = '<PLEOS_SERIAL>'
adb -s $env:ANDROID_SERIAL shell getprop sys.boot_completed
adb -s $env:ANDROID_SERIAL install -r app/build/outputs/apk/pleos/debug/app-pleos-debug.apk
adb -s $env:ANDROID_SERIAL shell am start --user current -W -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n com.hpc.app.debug/com.hpc.app.MainActivity
.\gradlew.bat -PenablePleos=true :app:connectedPleosDebugAndroidTest
```

`adb`는 선택한 Android SDK의 `platform-tools`를 PATH에 추가해 사용한다. `sys.boot_completed`는 `1`이어야 한다. AGP 8.10.1의 connected 작업은 `ANDROID_SERIAL`로 대상을 선택한다. `--serial`은 Gradle의 불변 목록을 수정하는 AGP 코드에서 `UnsupportedOperationException`을 일으킬 수 있어 사용하지 않는다. 앱 APK는 `app/build/outputs/apk/pleos/debug/`, 테스트 APK는 `app/build/outputs/apk/androidTest/pleos/debug/`에 생성된다. Gradle 계측 결과는 `app/build/reports/androidTests/connected/`와 `app/build/outputs/androidTest-results/connected/`에서 확인한다.

Gradle 계측 테스트 종료 후 앱이 제거될 수 있다. 초기 화면을 다시 확인하려면 위 앱 APK 설치와 현재 사용자 대상 launcher 실행 명령을 다시 실행한다.

이전 로컬 실행에서는 Gradle connected가 APK 설치 전에 실행하는 `service list` 조회가 멈췄고, 직접 조회도 `accessibility` 항목 뒤에 응답이 끝나지 않았다. 이 현상의 구체 원인은 확정하지 않았다. 같은 문제가 발생하면 진행 중인 connected 작업을 종료한 뒤, Android가 공식 지원하는 [adb 계측 실행](https://developer.android.com/studio/test/command-line#run-tests-with-adb)으로 같은 테스트 APK를 실행한다. 이 경로는 Gradle의 서비스 목록 사전검사를 거치지 않고 AndroidJUnitRunner를 실행하며 SDK 테스트의 성공 조건은 그대로 유지한다.

```powershell
$env:ANDROID_SERIAL = '<PLEOS_SERIAL>'
.\gradlew.bat -PenablePleos=true :app:assemblePleosDebug :app:assemblePleosDebugAndroidTest
adb -s $env:ANDROID_SERIAL install -r app/build/outputs/apk/pleos/debug/app-pleos-debug.apk
adb -s $env:ANDROID_SERIAL install -r -t app/build/outputs/apk/androidTest/pleos/debug/app-pleos-debug-androidTest.apk
adb -s $env:ANDROID_SERIAL shell am instrument -w -r --user current -e class com.hpc.app.VehicleSdkSmokeTest com.hpc.app.debug.test/androidx.test.runner.AndroidJUnitRunner
```

테스트 APK 설치의 `-t`는 `testOnly` APK를 허용한다. `--user current`는 Automotive의 현재 로그인 사용자에서 테스트를 실행한다. 직접 adb 실행 결과는 표준 출력으로 확인하며 Gradle HTML/XML 보고서는 생성되지 않는다. 실제 테스트 1개가 실행되었는지와 실패/예외 출력을 확인하고 로그를 보관한다. APK 설치 성공이나 adb 프로세스 종료 코드만으로 SDK 스모크 성공을 판정하지 않는다.

스모크 테스트는 최대 30초 동안 서비스 준비를 기다리며 capability 성공 뒤 비-null 상태 콜백을 받아야 통과한다. 미지원·권한 거부·null·timeout은 테스트 실패로 남기고 mock 값으로 대체하지 않는다. SET·제어·이벤트 구독은 하지 않으며 종료 시 SDK를 해제한다. `CAR_DOORS` 권한은 `pleosDebug`에만 있고 release에는 추가하지 않는다. CI에서는 계측 APK의 컴파일을 검증하고, 실제 테스트는 전용 Pleos AVD에서 connected 또는 직접 adb 명령으로 실행한다.

2026-11-10 검증: 공개 SDK 다운로드/checksum, Pleos debug 앱·계측 APK 빌드, Android Lint, 원격 CI를 통과했다. 전용 AVD에서 직접 adb 계측도 `OK (1 test)`로 통과했다(12.081초). `HpcPleosSmoke` 로그에서 capability와 실제 도어 상태 콜백 `position=0`을 확인했다. `ANDROID_SERIAL`만 설정한 Gradle connected도 58초에 `BUILD SUCCESSFUL`, 테스트 1개 성공 및 정상 보고서 생성을 확인했다. 이는 에뮬레이터 Vehicle Service의 읽기 연동 검증이며 실제 차량 검증은 아니다.

성공한 실행 환경은 Windows의 `HPC_Pleos_21_API34` AVD, Android Emulator 37.1.11, WHPX, API 34 / Pleos 2.1 / Vehicle Service 2.3.22(code 74), RAM 4GB, software GPU, Cold boot, ASCII SDK·AVD 경로다. 현재 사용자(user 10)를 지정한 launcher intent로 앱을 실행했고, activity의 `visible=true`와 스크린샷에서 HPC 초기 화면 표시를 확인했다.

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
- `app/src/pleosDebug`: 계측 테스트용 읽기 권한
- `app/src/androidTestPleos`: debug 전용 Vehicle Service 콜백 검증
- `app/src/debug`: 로컬 에뮬레이터용 네트워크 예외
- `gradle/libs.versions.toml`: 의존성 버전
- `AGENTS.md`: Codex·Claude 공통 작업 지침
- `CONTRIBUTING.md`: Git Flow·커밋·PR 규칙

공모전 제출 시 검증된 소스 tag/commit과 APK를 같은 GitHub Release에서 연결하고 설치·시연 절차를 기록한다. CI mock APK는 차량 SDK 구현 완료 산출물이 아니다. API/통합 환경과 전체 제출 버전은 `HPC-workspace`에서 관리한다.

## 공식 근거

- [Pleos 시작 가이드](https://document.pleos.ai/en/docs/pleos-only/getting-started)
- [Vehicle SDK 가져오기](https://document.pleos.ai/en/docs/pleos-only/connect-sdk-pleos/Vehicle/project-setup)
- [공개 SDK 메타데이터](https://nexus-playground.pleos.ai/repository/maven-releases/ai/pleos/playground/Vehicle/maven-metadata.xml)
- [공식 샘플과 연결 검증 기준](https://document.pleos.ai/en/docs/pleos-only/tutorial/vehicle-sdk-sample-app)
- [Pleos 에뮬레이터 환경](https://document.pleos.ai/en/docs/connect/guide/getting-started/application-development/setup-connect-sdk-emulator)
- [SDK 접근 상태](https://document.pleos.ai/en/docs/pleos-only/create-my-project)
- [AGP 8.10 호환성](https://developer.android.com/build/releases/agp-8-10-0-release-notes)
- [Kotlin D8/R8 지원](https://developer.android.com/build/kotlin-support)
- [Kotlin Gradle 호환성](https://kotlinlang.org/docs/gradle-configure-project.html)
- [Gradle 8.14.6 보안 수정](https://docs.gradle.org/8.14.6/release-notes.html)
