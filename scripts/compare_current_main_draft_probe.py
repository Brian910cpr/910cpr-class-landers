"""Run original main and draft V2 engines on the same private, frozen inputs.

This is an Actions-runner-only diagnostic. It never publishes, pushes, books,
contacts customers, or toggles checkout. Main's only disposable modification is
an optional clock argument at its selector entry point; the engine remains main.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from scripts.run_layered_release_probe import (
    SOURCE_PATHS,
    compare_safe_summaries,
    public_safe_summary,
    source_fingerprint,
)

ROOT = Path(__file__).resolve().parents[1]
PROBE = Path("data/runtime/audit_previews/v2_release_probe")
COMPARISON = ROOT / PROBE / "same_source_main_draft_comparison.json"
# Mirror the data inputs used by both engines, not code, into disposable main.
# Caches/replay artifacts are generated independently for each engine.
MIRROR = (
    "data/config", "data/inventory", "data/audit", "data/runtime",
    "data/sessions_current.json", "docs/data",
)
CLOCK_SIGNATURE = "def build_block_schedule_page(page_config: dict[str, Any]) -> dict[str, Any]:"
CLOCK_CALL = "    reference_now = selector_reference_datetime()"


class ComparisonBlocked(RuntimeError):
    """No release comparison can be claimed; keep all live gates closed."""


def _run_checked(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    # Captured output may contain private appointments or diagnostic provenance.
    # Never forward raw output into public CI logs or stored comparison artifacts.
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", check=False)
    if result.returncode:
        raise ComparisonBlocked("isolated_command_failed")
    return result


def _load_clock(report: dict) -> datetime:
    if not isinstance(report, dict) or report.get("published") is not False:
        raise ComparisonBlocked("draft_proof_missing")
    try:
        clock = datetime.fromisoformat(report["replay_clock_utc"].replace("Z", "+00:00"))
    except (KeyError, ValueError, TypeError) as exc:
        raise ComparisonBlocked("draft_clock_invalid") from exc
    if clock.tzinfo is None or clock.utcoffset() != timedelta(0):
        raise ComparisonBlocked("draft_clock_not_utc")
    return clock


def _mirror_inputs(main_root: Path) -> None:
    for name in MIRROR:
        source, dest = ROOT / name, main_root / name
        if not source.exists():
            raise ComparisonBlocked("required_source_tree_missing")
        if dest.is_dir():
            shutil.rmtree(dest)
        elif dest.exists():
            dest.unlink()
        dest.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, dest, ignore=shutil.ignore_patterns(
                "audit_previews", "layered_day_cache", "__pycache__", "*.pyc"))
        else:
            shutil.copy2(source, dest)
    # Required exact inputs cannot disappear under optional tree exclusions.
    for name in SOURCE_PATHS:
        src, dst = ROOT / name, main_root / name
        if not src.is_file() or not dst.is_file() or src.read_bytes() != dst.read_bytes():
            raise ComparisonBlocked("frozen_input_missing_or_mismatched")


def _install_diagnostic_adapter(main_root: Path) -> None:
    selector = main_root / "scripts/block_start_time_selector.py"
    original = selector.read_text(encoding="utf-8")
    if original.count(CLOCK_SIGNATURE) != 1 or original.count(CLOCK_CALL) != 1:
        raise ComparisonBlocked("baseline_clock_adapter_incompatible")
    adapted = original.replace(
        CLOCK_SIGNATURE,
        "def build_block_schedule_page(page_config: dict[str, Any], "
        "*, replay_now: datetime | None = None) -> dict[str, Any]:"
    ).replace(CLOCK_CALL, "    reference_now = selector_reference_datetime(replay_now)")
    selector.write_text(adapted, encoding="utf-8")
    # The draft probe is a read-only instrumentation shell, not the engine.
    # Import resolution in this subprocess loads ALL main engine modules.
    shutil.copy2(ROOT / "scripts/run_layered_release_probe.py",
                 main_root / "scripts/run_layered_release_probe.py")


def _main_proof(main_root: Path, clock: datetime) -> dict:
    code = (
        "from datetime import datetime\n"
        "from scripts.run_layered_release_probe import run\n"
        "run(replay_clock_utc=datetime.fromisoformat(" + repr(clock.isoformat()) + "))\n"
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(main_root)
    # Never pass customer details, credentials or full reports through argv.
    result = subprocess.run(
        [sys.executable, "-B", "-c", code], cwd=main_root,
        env=environment, capture_output=True, text=True, check=False
    )
    path = main_root / PROBE / "proof.json"
    if result.returncode or not path.is_file():
        raise ComparisonBlocked("main_engine_replay_failed")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise ComparisonBlocked("main_engine_proof_invalid") from exc


def execute() -> dict:
    draft_path = ROOT / PROBE / "proof.json"
    if not draft_path.is_file():
        raise ComparisonBlocked("draft_proof_not_generated")
    try:
        draft_proof = json.loads(draft_path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise ComparisonBlocked("draft_proof_invalid") from exc
    clock = _load_clock(draft_proof)
    draft_safe = public_safe_summary(draft_proof)
    if draft_safe["calculation_completed"] is not True or draft_safe["diagnostic_passed"] is not True:
        raise ComparisonBlocked("draft_engine_release_not_passed")
    # The V2 probe fingerprints a *temporary active-mode policy*. After its
    # finally block restores that file, the ordinary on-disk digest must be
    # different. Compare the unchanged raw files here, and compare the
    # effective active-mode digest separately against each engine's proof.
    source_digest = source_fingerprint(ROOT)

    # The base ref may be shallow; fetch explicit current main, then detach in a
    # throwaway worktree. Neither checkout nor its output is ever pushed.
    with tempfile.TemporaryDirectory(prefix="p0-v2-compare-") as temporary:
        main_root = Path(temporary) / "main"
        _run_checked(["git", "fetch", "--no-tags", "--depth=1", "origin", "main"], cwd=ROOT)
        _run_checked(["git", "worktree", "add", "--detach", str(main_root), "FETCH_HEAD"], cwd=ROOT)
        try:
            main_sha = _run_checked(["git", "rev-parse", "HEAD"], cwd=main_root).stdout.strip()
            _mirror_inputs(main_root)
            if source_fingerprint(main_root) != source_digest:
                raise ComparisonBlocked("main_source_snapshot_mismatched")
            _install_diagnostic_adapter(main_root)
            main_proof = _main_proof(main_root, clock)
            if source_fingerprint(main_root) != source_digest:
                raise ComparisonBlocked("main_source_mutated_during_replay")
            main_safe = public_safe_summary(main_proof)
            # The comparator enforces identical effective active-mode hashes;
            # the raw-source checks above and below guard post-replay drift.
            delta = compare_safe_summaries(main_safe, draft_safe)
            if source_fingerprint(ROOT) != source_digest:
                raise ComparisonBlocked("draft_source_mutated_during_comparison")
            delta.update({
                "comparison_status": "executed_same_source",
                "main_commit": main_sha,
                "source_input_count": len(SOURCE_PATHS),
                "main_engine_from_default_branch": True,
                "main_clock_change_diagnostic_only": True,
                "hosted_public_booking_proven": False,
                "native_checkout_proven": False,
            })
            return delta
        finally:
            # Prevent worktree registrations from being left behind on failure.
            subprocess.run(["git", "worktree", "remove", "--force", str(main_root)],
                           cwd=ROOT, capture_output=True, check=False)


def main() -> int:
    COMPARISON.parent.mkdir(parents=True, exist_ok=True)
    try:
        report = execute()
    except (ComparisonBlocked, ValueError, FileNotFoundError, OSError) as exc:
        code = str(exc) if isinstance(exc, ComparisonBlocked) else "validation_failed"
        # Only fixed/sanitized status codes are allowed in public Actions logs.
        allowed = {
            "isolated_command_failed", "draft_proof_missing", "draft_clock_invalid",
            "draft_clock_not_utc", "required_source_tree_missing",
            "frozen_input_missing_or_mismatched", "baseline_clock_adapter_incompatible",
            "main_engine_replay_failed", "main_engine_proof_invalid",
            "draft_proof_not_generated", "draft_proof_invalid",
            "draft_engine_release_not_passed", "draft_source_changed_since_replay",
            "main_source_snapshot_mismatched", "main_source_mutated_during_replay",
            "draft_source_mutated_during_comparison",
        }
        report = {"published": False, "same_source_verified": False,
                  "hosted_public_booking_proven": False, "native_checkout_proven": False,
                  "comparison_status": "blocked",
                  "reason_code": code if code in allowed else "validation_failed"}
        COMPARISON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("P0 same-source main/draft comparison blocked:", report["reason_code"])
        return 1
    COMPARISON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("P0 same-source main/draft comparison executed for",
          len(report["families"]), "actual course families;",
          "source and clock matched. No publishing, booking or checkout performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
