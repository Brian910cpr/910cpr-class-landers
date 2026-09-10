import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import build_courses


class BuildCoursesEntryPointTests(unittest.TestCase):
    def test_delegates_without_purging_existing_course_landers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            existing = output / "heartcode-bls.html"
            existing.write_text("existing rich course page", encoding="utf-8")

            with (
                patch.object(build_courses, "OUTPUT", output),
                patch.object(build_courses, "build_proposed_inventory") as proposal_builder,
                patch.object(build_courses.build_course_landers, "main") as rich_builder,
                patch.object(build_courses, "BuildStatusReporter"),
            ):
                build_courses.build()

            proposal_builder.assert_called_once_with()
            rich_builder.assert_called_once_with()
            self.assertEqual(existing.read_text(encoding="utf-8"), "existing rich course page")

    def test_pipeline_inputs_are_the_rich_lander_inputs(self) -> None:
        self.assertEqual(build_courses.ARCHIVE_INPUT.name, "course_archive_v4.json")
        self.assertEqual(build_courses.SCHEDULE_INPUT.name, "schedule_future.json")
        self.assertEqual(build_courses.PROPOSAL_POLICY_INPUT.name, "long_range_bls_inventory_policy.json")
        self.assertEqual(build_courses.PROPOSAL_OUTPUT.name, "long_range_bls_inventory_preview.json")

    def test_proposal_inventory_is_built_before_course_landers(self) -> None:
        calls = []
        with (
            patch.object(build_courses, "build_proposed_inventory", side_effect=lambda: calls.append("proposal")),
            patch.object(build_courses.build_course_landers, "main", side_effect=lambda: calls.append("landers")),
            patch.object(build_courses, "BuildStatusReporter"),
            patch.object(build_courses, "OUTPUT", Path("missing-output")),
        ):
            build_courses.build()
        self.assertEqual(["proposal", "landers"], calls)


if __name__ == "__main__":
    unittest.main()
