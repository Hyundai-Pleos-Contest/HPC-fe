# Pleos 공용 로컬 실행 도구

Python 3.12 이상, JDK 21, Android SDK Platform 35 / Build Tools 35.0.0 /
Platform Tools / Emulator가 필요하다. 스크립트는 Python 외 패키지를 설치하지 않는다.
Pleos API 34 이미지와 AVD는 [README의 공식 설치 절차](../README.md#pleos-sdk와-에뮬레이터)로 준비한다.
이미지 다운로드·AVD 생성·라이선스 동의·개인 경로 변경은 자동으로 진행하지 않는다.

## 경로 지정

`HPC-fe`에서 실행한다. SDK 루트를 `ANDROID_HOME` 또는 매 명령의 `--sdk`로 전달한다.
`--sdk`가 우선한다. `local.properties`는 스크립트에서 읽거나 수정하지 않으며,
기존 `sdk.dir`이 있다면 Gradle도 같은 SDK를 사용하도록 개발자가 맞춘다.
새 clone에서는 `local.properties` 없이 `ANDROID_HOME`만으로 빌드할 수 있다.

PowerShell:

```powershell
$env:ANDROID_HOME = 'C:\Android\Sdk' # 실제 설치 위치로 변경
python scripts/pleos.py doctor
```

Linux:

```sh
export ANDROID_HOME="$HOME/Android/Sdk" # 실제 설치 위치로 변경
python3 scripts/pleos.py doctor
```

`doctor`는 JDK/컴파일 SDK/도구와 AVD 목록을 확인한다. AVD 목록이 비어 있으면 Android Studio에서
Pleos AVD를 생성한다. 이 단계만으로 Vehicle SDK 연결 성공을 의미하지 않는다.
AVD가 기본 위치에 없으면 `ANDROID_AVD_HOME` 또는 매 명령에 `--avd-home <AVD_DIRECTORY>`를 지정한다.
스크립트는 기존 ADB 서버를 종료하거나 `ANDROID_USER_HOME`과 인증 키를 바꾸지 않는다.

## 부팅 → 빌드 → 테스트 → 화면 실행 → 종료

아래 `YOUR_PLEOS_AVD`를 doctor에 표시된 Pleos AVD 이름으로 바꾼다.

```sh
python scripts/pleos.py start --avd YOUR_PLEOS_AVD
python scripts/pleos.py build --api-base-url http://10.0.2.2:8080
python scripts/pleos.py test --serial emulator-5556
python scripts/pleos.py launch --serial emulator-5556
python scripts/pleos.py stop --serial emulator-5556
```

- `start`: RAM 4GB, software GPU, Cold boot로 실행한다. 기본 포트는 5556이며
  `--port 5558`로 바꾸면 대상 serial도 `emulator-5558`이 된다. `--headless`는 화면 창과 오디오를 끈다.
  부팅은 최대 240초 기다리고 Vehicle Service 패키지 존재를 확인한다.
  timeout 시 진단용 프로세스/로그는 남으며 표시된 serial로 `stop`한다.
- `build`: Pleos debug 앱·테스트 APK 빌드와 Lint를 수행한다. 기본 mock 빌드 명령은 README를 따른다.
  서버 포트를 바꿨다면 `--api-base-url`도 바꾼다. debug 주소만 설정하며 실제 API 호출 기능은 아직 없다.
- `test`: **먼저 build가 필요하다.** 마지막 빌드의 APK 두 개를 설치하고 현재 Android 사용자에게
  읽기 전용 Vehicle SDK 계측 1개를 직접 adb로 실행한다. 소스를 고쳤다면 다시 build한다.
  `OK (1 test)`를 확인하며 실패/비정상 종료/0개 실행은 성공으로 취급하지 않는다.
  stdout 로그는 `.local/pleos/smoke-*.log`에 저장한다. Gradle XML/HTML 보고서는 생성하지 않는다.
- `launch`: 마지막 빌드 APK를 설치하고 현재 사용자의 Launcher intent로 초기 화면을 실행한다.
- `stop`: 명시한 emulator만 종료한다. AVD 데이터·스냅샷을 삭제하지 않는다.

`test`, `launch`, `stop`은 `--serial`이 필수다. 암묵적인 첫 기기 선택이나 실제 기기 실행은 지원하지 않는다.
test/launch는 부팅 완료와 Pleos Vehicle Service 설치 여부를 확인한다.
test는 capability 및 비-null 도어 상태 콜백을 검증하며 SET/차량 제어를 수행하지 않는다.
Gradle connected 보고서가 필요하면 README의 `ANDROID_SERIAL` 방식 명령을 사용한다.

## 문제 해결과 보존 범위

- Windows 한글 SDK/AVD 경로에서 네이티브 부팅 파일 오류가 나면 ASCII 설치 경로를 사용한다.
  스크립트는 경로를 이동하거나 Junction을 자동 생성하지 않는다. 이미 관리하는 ASCII Junction은 그대로 전달할 수 있다.
- `unauthorized`는 ADB 키/사용자 환경을 확인한다. AVD 디렉터리 분리를 위해 `ANDROID_USER_HOME`까지
  변경하면 기존 ADB 서버와 다른 인증 키를 사용할 수 있다. AVD만 분리할 때는 `ANDROID_AVD_HOME`을 사용한다.
- 포트가 이미 사용 중이면 해당 AVD를 명시적으로 사용하거나 다른 `--port`를 선택한다.
- 부팅 로그는 `.local/pleos/emulator-*.log`에 남는다. 앱 설치 지연/서비스 이상 시 로그와 기존 README를 확인한다.
- 종료 실패 시 Android Studio에서 해당 AVD를 종료한다. `adb kill-server`, SDK 삭제, AVD wipe는 수행하지 않는다.
- SDK/AVD/Gradle 캐시는 개발 머신의 사전 설치 자원이다. 저장소에 넣지 않는다.

## 도구 자체 검사

```sh
python -m unittest discover -s scripts -p "test_*.py"
```

이 검사는 SDK 없이 실행되며 실제 기기 거부와 계측 결과 오판 방지를 확인한다.
CI의 이 검사와 APK 빌드는 에뮬레이터 런타임 테스트를 대신하지 않는다.

## 공식 명령 근거

- [Emulator 명령](https://developer.android.com/studio/run/emulator-commandline)
- [adb 계측 테스트](https://developer.android.com/studio/test/command-line#run-tests-with-adb)

현재 프로젝트에서 검증한 Emulator 실행 파일을 사용한다. 도구 변경 시 고정된 Pleos 이미지와의
호환성을 확인한 뒤 공용 절차를 갱신한다.
