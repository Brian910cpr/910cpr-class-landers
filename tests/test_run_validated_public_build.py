import unittest
from unittest.mock import patch

from scripts.run_validated_public_build import BUILD_MODULES, command_plan


class ValidatedPublicBuildTests(unittest.TestCase):
    @patch("scripts.run_validated_public_build.sys.executable", "python")
    def test_skip_tests_plan_contains_only_build_modules(self):
        self.assertEqual(command_plan(True), [["python", "-m", module] for module in BUILD_MODULES])

    @patch("scripts.run_validated_public_build.sys.executable", "python")
    def test_default_plan_finishes_with_repository_tests(self):
        self.assertEqual(command_plan(False)[-1], ["python", "-m", "unittest", "discover", "tests"])


if __name__ == "__main__":
    unittest.main()
