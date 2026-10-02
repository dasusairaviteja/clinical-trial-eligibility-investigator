import subprocess
import sys
import unittest
import os
from clinical_trial.config import Environment, read_environment


class EnvironmentTests(unittest.TestCase):
    def test_local_default_is_eng(self):
        self.assertEqual(read_environment({}), Environment.ENG)

    def test_each_explicit_environment(self):
        for value in ("ENG", "TEST", "PROD"):
            with self.subTest(value=value):
                self.assertEqual(read_environment({"APP_ENV": value}).value, value)

    def test_invalid_values_fail_closed(self):
        for value in ("", "production", "prod", " PROD", "PROD ", "DEV"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                read_environment({"APP_ENV": value})

    def test_error_does_not_echo_untrusted_value(self):
        with self.assertRaises(ValueError) as caught:
            read_environment({"APP_ENV": "sensitive-input"})
        self.assertNotIn("sensitive-input", str(caught.exception))

    def test_cli_success(self):
        result = subprocess.run([sys.executable, "-m", "clinical_trial"],
            env={**os.environ, "APP_ENV": "TEST"}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Environment validated: TEST", result.stdout)

    def test_cli_invalid_environment_exits_nonzero(self):
        result = subprocess.run([sys.executable, "-m", "clinical_trial"],
            env={**os.environ, "APP_ENV": "invalid"}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
