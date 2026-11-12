"""Build and run the Pleos debug smoke test; Python 3.12+, standard library only."""

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app/build/outputs/apk/pleos/debug/app-pleos-debug.apk"
TEST = ROOT / "app/build/outputs/apk/androidTest/pleos/debug/app-pleos-debug-androidTest.apk"
SERVICE = "ai.pleos.playground.service.vehicle"


def run(command: list[str], env: dict[str, str], *, timeout: int = 60, capture: bool = True) -> str:
    result = subprocess.run(
        command, cwd=ROOT, env=env, check=True, timeout=timeout,
        text=True, encoding="utf-8", errors="replace", capture_output=capture,
    )
    return result.stdout.strip() if capture else ""


def tool(sdk: Path, relative: str) -> str:
    path = sdk / (relative + (".exe" if os.name == "nt" else ""))
    if not path.is_file():
        raise RuntimeError(f"Missing SDK tool: {path}. Install it using Android Studio SDK Manager.")
    return str(path)


def doctor(sdk: Path, env: dict[str, str]) -> None:
    java = str(Path(env["JAVA_HOME"]) / "bin" / ("java.exe" if os.name == "nt" else "java")) if env.get("JAVA_HOME") else "java"
    version = subprocess.run([java, "-version"], env=env, capture_output=True, text=True, check=True, timeout=20)
    if not re.search(r'version "21(?:\.|\")', version.stderr + version.stdout):
        raise RuntimeError("Use JDK 21 (JAVA_HOME and Android Studio Gradle JDK).")
    for relative in ("platforms/android-35/android.jar", "build-tools/35.0.0/source.properties"):
        if not (sdk / relative).is_file():
            raise RuntimeError(f"Install the pinned SDK component: {relative}")
    run([tool(sdk, "platform-tools/adb"), "version"], env)
    avds = run([tool(sdk, "emulator/emulator"), "-list-avds"], env)
    print(f"JDK 21, SDK 35 and Build Tools 35.0.0: OK\nAvailable AVDs:\n{avds or '(none)'}")
    if os.name == "nt" and (not str(sdk).isascii() or not env.get("ANDROID_AVD_HOME", "").isascii()):
        print("NOTE: Use ASCII SDK/AVD paths if native emulator tools fail; see docs/local-tools.md.")


def validate_target(adb: str, serial: str, env: dict[str, str], *, require_pleos: bool = True) -> None:
    if not re.fullmatch(r"emulator-\d+", serial):
        raise RuntimeError("Specify an emulator serial with --serial; physical devices are not supported.")
    if run([adb, "-s", serial, "shell", "getprop", "ro.kernel.qemu"], env) != "1":
        raise RuntimeError("The selected target is not an Android emulator.")
    if require_pleos:
        if run([adb, "-s", serial, "shell", "getprop", "sys.boot_completed"], env) != "1":
            raise RuntimeError("Wait for the emulator to finish booting.")
        packages = run([adb, "-s", serial, "shell", "pm", "list", "packages", SERVICE], env)
        if f"package:{SERVICE}" not in packages.splitlines():
            raise RuntimeError("Vehicle Service is absent. Select a dedicated Pleos AVD.")


def start(sdk: Path, adb: str, args: argparse.Namespace, env: dict[str, str]) -> None:
    if not args.avd or args.avd.startswith("-"):
        raise RuntimeError("start requires --avd with an existing Pleos AVD name.")
    if args.port < 5554 or args.port > 5682 or args.port % 2:
        raise RuntimeError("--port must be even and between 5554 and 5682.")
    emulator = tool(sdk, "emulator/emulator")
    if args.avd not in run([emulator, "-list-avds"], env).splitlines():
        raise RuntimeError("AVD not found. Create it with Android Studio first; check --avd-home.")
    serial = f"emulator-{args.port}"
    if re.search(rf"^{re.escape(serial)}\s", run([adb, "devices"], env), re.MULTILINE):
        raise RuntimeError(f"{serial} is already present. Use it explicitly or choose another --port.")
    logs = ROOT / ".local/pleos"
    logs.mkdir(parents=True, exist_ok=True)
    log = logs / f"emulator-{args.port}-{time.time_ns()}.log"
    command = [emulator, "-avd", args.avd, "-port", str(args.port), "-memory", "4096", "-gpu", "software", "-no-snapshot"]
    if args.headless:
        command += ["-no-window", "-no-audio"]
    with log.open("w", encoding="utf-8") as stream:
        process = subprocess.Popen(
            command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    print(f"Starting {serial}; log: {log}", flush=True)
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Emulator exited ({process.returncode}); inspect {log}")
        try:
            if run([adb, "-s", serial, "shell", "getprop", "sys.boot_completed"], env, timeout=5) == "1":
                validate_target(adb, serial, env)
                print(f"Pleos AVD booted: {serial}. Use --serial {serial} for test/launch/stop.")
                return
        except subprocess.SubprocessError:
            pass
        time.sleep(2)
    raise RuntimeError(f"Boot timeout. Emulator remains available for diagnosis; log: {log}. Stop it with stop --serial {serial}.")


def build(env: dict[str, str], api_base_url: str | None) -> None:
    wrapper = [str(ROOT / "gradlew.bat")] if os.name == "nt" else ["bash", str(ROOT / "gradlew")]
    command = wrapper + ["--no-daemon", "-PenablePleos=true", ":app:assemblePleosDebug", ":app:assemblePleosDebugAndroidTest", ":app:lintPleosDebug"]
    if api_base_url:
        command.append(f"-PapiBaseUrl={api_base_url}")
    run(command, env, capture=False, timeout=1800)


def smoke_passed(output: str) -> bool:
    # adb may exit 0 even when instrumentation fails or no tests run.
    return bool(re.search(r"^OK \(1 test\)\s*$", output, re.MULTILINE)) and not re.search(
        r"FAILURES!!!|INSTRUMENTATION_FAILED|INSTRUMENTATION_ABORTED|shortMsg=|Process crashed", output
    )


def installed_apk(adb: str, serial: str, apk: Path, env: dict[str, str], *, test: bool = False) -> None:
    if not apk.is_file():
        raise RuntimeError(f"Missing {apk.name}; run build first.")
    result = run([adb, "-s", serial, "install", "-r", *(["-t"] if test else []), str(apk)], env, timeout=120)
    if "Success" not in result.splitlines():
        raise RuntimeError(f"APK installation did not report Success: {result}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["doctor", "start", "build", "test", "launch", "stop"])
    parser.add_argument("--sdk", default=os.environ.get("ANDROID_HOME"), help="installed SDK root (or ANDROID_HOME); local.properties is not parsed")
    parser.add_argument("--avd-home", help="existing AVD directory (or ANDROID_AVD_HOME)")
    parser.add_argument("--avd", help="AVD name for start")
    parser.add_argument("--port", type=int, default=5556, help="emulator console port for start (default: 5556)")
    parser.add_argument("--headless", action="store_true", help="start without emulator window/audio")
    parser.add_argument("--serial", help="explicit target for test/launch/stop, e.g. emulator-5556")
    parser.add_argument("--api-base-url", help="debug backend address for build; does not load workspace .env")
    args = parser.parse_args()
    if not args.sdk:
        parser.error("set ANDROID_HOME or supply --sdk; see docs/local-tools.md")
    if args.action in ("test", "launch", "stop") and not args.serial:
        parser.error(f"{args.action} requires --serial (no implicit device selection)")
    # abspath intentionally preserves an existing ASCII junction on Windows.
    sdk = Path(os.path.abspath(os.path.expanduser(args.sdk)))
    env = os.environ.copy()
    env["ANDROID_HOME"] = str(sdk)
    env["ANDROID_SDK_ROOT"] = str(sdk)
    if args.avd_home:
        env["ANDROID_AVD_HOME"] = os.path.abspath(os.path.expanduser(args.avd_home))
    # Preserve ANDROID_USER_HOME and the current ADB identity.
    if args.action == "doctor":
        doctor(sdk, env)
    elif args.action == "build":
        doctor(sdk, env)
        build(env, args.api_base_url)
    else:
        adb = tool(sdk, "platform-tools/adb")
        if args.action == "start":
            start(sdk, adb, args, env)
        else:
            validate_target(adb, args.serial, env, require_pleos=args.action != "stop")
            if args.action == "stop":
                print(run([adb, "-s", args.serial, "emu", "kill"], env))
            else:
                installed_apk(adb, args.serial, APP, env)
                if args.action == "launch":
                    result = run([adb, "-s", args.serial, "shell", "am", "start", "--user", "current", "-W", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.LAUNCHER", "-n", "com.hpc.app.debug/com.hpc.app.MainActivity"], env)
                    print(result)
                    if not re.search(r"^Status: ok\s*$", result, re.MULTILINE):
                        raise RuntimeError("Android did not report a successful activity launch.")
                else:
                    installed_apk(adb, args.serial, TEST, env, test=True)
                    result = run([adb, "-s", args.serial, "shell", "am", "instrument", "-w", "-r", "--user", "current", "-e", "class", "com.hpc.app.VehicleSdkSmokeTest", "com.hpc.app.debug.test/androidx.test.runner.AndroidJUnitRunner"], env, timeout=150)
                    logs = ROOT / ".local/pleos"
                    logs.mkdir(parents=True, exist_ok=True)
                    log = logs / f"smoke-{args.serial}-{time.time_ns()}.log"
                    log.write_text(result + "\n", encoding="utf-8")
                    print(f"{result}\nLog: {log}")
                    if not smoke_passed(result):
                        raise RuntimeError("Expected exactly one successful Vehicle SDK smoke test. Inspect the log.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
