"""Cross-platform entry point for the validated public build."""

from __future__ import annotations

import os
import subprocess
import sys
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
    for command in command_plan(skip_tests):
        print(f"Running: {' '.join(command)}", flush=True)
        completed = subprocess.run(command, cwd=ROOT)
        if completed.returncode:
            print(f"Build failed with exit code {completed.returncode}: {' '.join(command)}", file=sys.stderr)
            return completed.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
