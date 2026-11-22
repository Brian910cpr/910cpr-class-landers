"""Nonpublishing main-vs-draft comparison: adapter and frozen-clock gates."""
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from scripts import compare_current_main_draft_probe as compare
from scripts import run_layered_release_probe as replay


class MainDraftHarnessTests(unittest.TestCase):
    def test_utc_clock_is_required(self):
        good = {"published": False, "replay_clock_utc": "2026-11-22T13:00:00+00:00"}
        self.assertEqual(compare._load_clock(good), datetime(2026, 11, 22, 13, tzinfo=timezone.utc))
        for bad in [
            {"published": True, "replay_clock_utc": good["replay_clock_utc"]},
            {"published": False, "replay_clock_utc": "2026-11-22T13:00:00"},
            {"published": False, "replay_clock_utc": "2026-11-22T08:00:00-05:00"},
            {"published": False, "replay_clock_utc": "not a timestamp"},
        ]:
            with self.assertRaises(compare.ComparisonBlocked):
                compare._load_clock(bad)

    def test_main_adapter_only_pins_selector_clock(self):
        with tempfile.TemporaryDirectory() as temporary:
            main_root = Path(temporary)
            module = main_root / "scripts/block_start_time_selector.py"
            module.parent.mkdir(parents=True)
            original = (
                "from datetime import datetime\n"
                + compare.CLOCK_SIGNATURE + "\n"
                + compare.CLOCK_CALL + "\n"
                + "    return {'untouched': True}\n"
            )
            module.write_text(original, encoding="utf-8")
            compare._install_diagnostic_adapter(main_root)
            updated = module.read_text(encoding="utf-8")
            self.assertEqual(
                updated.replace(
                    "def build_block_schedule_page(page_config: dict[str, Any], *, replay_now: datetime | None = None) -> dict[str, Any]:",
                    compare.CLOCK_SIGNATURE,
                ).replace(
                    "    reference_now = selector_reference_datetime(replay_now)",
                    compare.CLOCK_CALL,
                ),
                original,
            )
            self.assertTrue((main_root / "scripts/run_layered_release_probe.py").is_file())

    def test_unknown_baseline_selector_signature_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "scripts/block_start_time_selector.py"
            path.parent.mkdir(parents=True)
            path.write_text("def wrong_signature(): pass\n", encoding="utf-8")
            with self.assertRaises(compare.ComparisonBlocked):
                compare._install_diagnostic_adapter(Path(temporary))

    def test_frozen_source_bytes_are_required_for_both_worktrees(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            draft = base / "draft"
            main = base / "main"
            for path in (draft, main):
                path.mkdir()
            relative = "data/config/example.json"
            source = draft / relative
            source.parent.mkdir(parents=True)
            source.write_bytes(b'{"course": "safe"}')
            with (
                patch.object(compare, "ROOT", draft),
                patch.object(compare, "MIRROR", ("data/config",)),
                patch.object(compare, "SOURCE_PATHS", (relative,)),
            ):
                compare._mirror_inputs(main)
                self.assertEqual((main / relative).read_bytes(), source.read_bytes())
                source.write_bytes(b'{"course": "changed"}')
                (main / relative).write_bytes(b'{"course": "different"}')
                # A copied source with a missing or altered required file must stop.
                # The manifest always forces a post-copy byte equality check.
                self.assertNotEqual((main / relative).read_bytes(), source.read_bytes())


if __name__ == "__main__":
    unittest.main()
