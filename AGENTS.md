# HPC-fe 작업 지침

- 이 저장소는 Pleos Connect 차량용 Android 앱이다. Kotlin + Jetpack Compose를 사용한다.
- 협업·브랜치·커밋·PR 작업 전 `CONTRIBUTING.md`를 읽는다.
- 환경과 명령의 기준은 `README.md`, 의존성 버전의 기준은 `gradle/libs.versions.toml`이다.
- 저장소 루트에서 `./gradlew :app:assembleMockDebug :app:lintMockDebug :app:testMockDebugUnitTest`로 검증한다. Windows에서는 `./gradlew.bat`을 사용한다.
- 기본 `mock`은 차량 연결이 없는 초기 화면이다. SDK 연동 성공이나 실제 차량 데이터로 설명하지 않는다.
- `-PenablePleos=true`는 별도 `pleos` flavor와 공식 SDK 의존성을 활성화한다. SDK 제공·접근 상태를 확인한 뒤 사용하고, 공개 문서와 실제 artifact의 차이를 보고한다.
- 실제 차량 접근은 향후 별도 data 계층에서 SDK/AAOS 어댑터로 구현한다. UI에서 SDK를 직접 호출하거나 mock 값을 실제 값으로 표시하지 않는다.
- 차량 기능 추가 시 capability, permission, 수명주기 해제, 주행 제한, 네트워크 단절 처리를 포함한다. 현재 scaffold에는 차량 권한·제어·주행 기능이 없다.
- SDK/API 키·서명 키·실제 차량 식별자·개인정보를 저장소에 넣지 않는다. BuildConfig에 들어간 값은 APK에서 추출 가능하므로 비밀을 넣지 않는다.
- `apiBaseUrl`은 debug만, `releaseApiBaseUrl`은 HTTPS만 사용한다. `.env` 자동 로딩을 가정하지 않는다.
- 실제 실행한 검증과 미실행한 에뮬레이터/차량 검증을 구분해서 보고한다.
