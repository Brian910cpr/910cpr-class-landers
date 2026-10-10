"""Cross-platform entry point for the validated public build."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_MODULES = (
    "scripts.build_sessions_current",
    "scripts.build_schedule_future",
    "scripts.build_landers",
    "scripts.generate_dynamic_offers",
    "scripts.filter_public_sellable_offers",
    "scripts.select_schedule_seeds",
    "scripts.build_seed_appointment_url_preview",
    "scripts.build_universal_offer_inventory",
    "scripts.build_slug_hubs",
    "scripts.build_deployed_selector_pages",
    "scripts.build_index_and_sitemap",
    "scripts.ensure_analytics_tags",
    "scripts.inject_global_theme_assets",
)


def command_plan(skip_tests: bool) -> list[list[str]]:
    commands = [[sys.executable, "-m", module] for module in BUILD_MODULES]
    if not skip_tests:
        commands.append([sys.executable, "-m", "unittest", "discover", "tests"])
    return commands


def main() -> int:
    if not (ROOT / "scripts" / "generate_dynamic_offers.py").is_file():
        print("ERROR: This does not look like the 910CPR lander repository.", file=sys.stderr)
        return 1

    skip_tests = os.environ.get("LANDER_SKIP_REPOSITORY_TESTS", "").casefold() == "1"
    print(f"910CPR validated public build: {ROOT}", flush=True)
    timeout_seconds = int(os.environ.get("LANDER_BUILD_MODULE_TIMEOUT_SECONDS", "300"))
    for command in command_plan(skip_tests):
        label = command[-1]
        started = time.monotonic()
        print(f"::group::Running {label}", flush=True)
        print(f"Running: {' '.join(command)}", flush=True)
        try:
            completed = subprocess.run(command, cwd=ROOT, timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            elapsed = time.monotonic() - started
            print(f"::endgroup::", flush=True)
            print(
                f"ERROR: Build module timed out after {elapsed:.1f}s "
                f"(limit {timeout_seconds}s): {label}",
                file=sys.stderr,
                flush=True,
            )
            return 124
        elapsed = time.monotonic() - started
        print(f"Completed {label} in {elapsed:.1f}s with exit code {completed.returncode}", flush=True)
        print(f"::endgroup::", flush=True)
        if completed.returncode:
            print(f"Build failed with exit code {completed.returncode}: {' '.join(command)}", file=sys.stderr)
            return completed.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
