"""Safety/false-positive regressions; no Android SDK or device required."""

import unittest
from unittest.mock import patch

import pleos


class PleosSafetyTest(unittest.TestCase):
    def test_unsafe_backend_url_never_reaches_batch_wrapper(self):
        for address in ("http://localhost/&echo", "http://user:password@localhost", "http://localhost/%TEMP%", "http://localhost/?token=value"):
            with self.subTest(address=address), patch("pleos.run") as run:
                with self.assertRaisesRegex(RuntimeError, "plain HTTP"):
                    pleos.build({}, address)
                run.assert_not_called()

    def test_only_a_real_one_test_success_passes(self):
        self.assertTrue(pleos.smoke_passed("Time: 1.5\n\nOK (1 test)\n\nINSTRUMENTATION_CODE: -1\n"))
        for output in (
            "INSTRUMENTATION_CODE: -1", "OK (0 tests)", "OK (2 tests)",
            "FAILURES!!!\nTests run: 1, Failures: 1", "INSTRUMENTATION_FAILED: runner",
            "OK (1 test)\nINSTRUMENTATION_RESULT: shortMsg=Process crashed",
        ):
            with self.subTest(output=output):
                self.assertFalse(pleos.smoke_passed(output))

    def test_physical_device_is_rejected_before_adb(self):
        with patch("pleos.run") as run:
            with self.assertRaisesRegex(RuntimeError, "physical devices"):
                pleos.validate_target("adb", "physical-device", {})
            run.assert_not_called()

    def test_generic_android_emulator_is_rejected(self):
        with patch("pleos.run", side_effect=["1", "1", ""]):
            with self.assertRaisesRegex(RuntimeError, "Vehicle Service is absent"):
                pleos.validate_target("adb", "emulator-5556", {})

    def test_target_must_be_explicit_even_when_environment_sets_serial(self):
        with patch.dict("os.environ", {"ANDROID_SERIAL": "emulator-5556"}), patch("sys.argv", ["pleos.py", "stop", "--sdk", "/sdk"]), patch("pleos.run") as run:
            with self.assertRaises(SystemExit) as result:
                pleos.main()
            self.assertEqual(result.exception.code, 2)
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
