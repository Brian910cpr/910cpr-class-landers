from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from scripts.local_data_paths import resolve_live_input_path, resolve_live_output_dir


class LocalDataPathTests(unittest.TestCase):
    def test_cli_path_wins_over_private_and_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cli = root / "operator" / "Class Report.xlsx"
            private = root / "data" / "private" / "enrollware" / "Class Report.xlsx"
            legacy = root / "data" / "Class Report.xlsx"
            cli.parent.mkdir(parents=True)
            private.parent.mkdir(parents=True)
            legacy.parent.mkdir(parents=True, exist_ok=True)
            cli.write_text("cli", encoding="utf-8")
            private.write_text("private", encoding="utf-8")
            legacy.write_text("legacy", encoding="utf-8")

            resolved = resolve_live_input_path(
                root,
                label="Class report",
                cli_path=str(cli),
                env_var=None,
                private_path="data/private/enrollware/Class Report.xlsx",
                legacy_paths=["data/Class Report.xlsx"],
            )

            self.assertEqual(resolved.path, cli.resolve())
            self.assertEqual(resolved.source, "cli")

    def test_env_path_wins_when_no_cli_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env_path = root / "env" / "students.csv"
            private = root / "data" / "private" / "raw" / "students_raw_live.csv"
            env_path.parent.mkdir(parents=True)
            private.parent.mkdir(parents=True)
            env_path.write_text("student_id,name\n90000001,Test Student\n", encoding="utf-8")
            private.write_text("student_id,name\n90000002,Other Student\n", encoding="utf-8")

            old_value = os.environ.get("LANDER_TEST_STUDENTS_PATH")
            os.environ["LANDER_TEST_STUDENTS_PATH"] = str(env_path)
            try:
                resolved = resolve_live_input_path(
                    root,
                    label="Students CSV",
                    cli_path=None,
                    env_var="LANDER_TEST_STUDENTS_PATH",
                    private_path="data/private/raw/students_raw_live.csv",
                    legacy_paths=["data/raw/students_raw_live.csv"],
                )
            finally:
                if old_value is None:
                    os.environ.pop("LANDER_TEST_STUDENTS_PATH", None)
                else:
                    os.environ["LANDER_TEST_STUDENTS_PATH"] = old_value

            self.assertEqual(resolved.path, env_path.resolve())
            self.assertEqual(resolved.source, "env")

    def test_private_path_wins_over_legacy_when_no_cli_or_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private = root / "data" / "private" / "raw" / "classes_raw_live.csv"
            legacy = root / "data" / "raw" / "classes_raw_live.csv"
            private.parent.mkdir(parents=True)
            legacy.parent.mkdir(parents=True)
            private.write_text("class_id,title\n99000001,Synthetic Class\n", encoding="utf-8")
            legacy.write_text("class_id,title\n99000002,Legacy Class\n", encoding="utf-8")

            resolved = resolve_live_input_path(
                root,
                label="Classes CSV",
                cli_path=None,
                env_var=None,
                private_path="data/private/raw/classes_raw_live.csv",
                legacy_paths=["data/raw/classes_raw_live.csv"],
            )

            self.assertEqual(resolved.path, private.resolve())
            self.assertEqual(resolved.source, "private")

    def test_legacy_path_remains_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = root / "data" / "Class Report.xlsx"
            legacy.parent.mkdir(parents=True)
            legacy.write_text("legacy", encoding="utf-8")

            resolved = resolve_live_input_path(
                root,
                label="Class report",
                cli_path=None,
                env_var=None,
                private_path="data/private/enrollware/Class Report.xlsx",
                legacy_paths=["data/Class Report.xlsx"],
            )

            self.assertEqual(resolved.path, legacy.resolve())
            self.assertEqual(resolved.source, "legacy")

    def test_missing_path_points_to_private_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            resolved = resolve_live_input_path(
                root,
                label="Class report",
                cli_path=None,
                env_var=None,
                private_path="data/private/enrollware/Class Report.xlsx",
                legacy_paths=["data/Class Report.xlsx"],
            )

            self.assertEqual(resolved.path, (root / "data/private/enrollware/Class Report.xlsx").resolve())
            self.assertEqual(resolved.source, "missing")

    def test_live_output_dir_prefers_private_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            resolved = resolve_live_output_dir(
                root,
                label="Enrollware sync output directory",
                cli_path=None,
                env_var=None,
                private_path="data/private/runtime/enrollware_sync",
                legacy_path="data/runtime/enrollware_sync",
            )

            self.assertEqual(resolved.path, (root / "data/private/runtime/enrollware_sync").resolve())
            self.assertEqual(resolved.source, "private")


if __name__ == "__main__":
    unittest.main()
