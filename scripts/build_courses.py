"""Build the durable, individual public course landers.

This pipeline entry point used to delete every ``docs/courses/*.html`` page and
replace the set with thin family hubs. That erased the richer individual BLS,
HeartCode, ACLS, PALS, and Heartsaver sales pages. Keep the stable entry point,
but delegate to the authoritative individual-course builder.

Build order is deliberate: generate the safe, request-only long-range BLS
inventory first, then render course landers from it. The generated preview is a
build artifact and does not need to be committed.
"""

import subprocess
import sys
from pathlib import Path

from scripts import build_course_landers
from scripts.build_status import BuildStatusReporter


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = REPO_ROOT / "docs" / "courses"
ARCHIVE_INPUT = REPO_ROOT / "raw" / "course_archive_v4.json"
SCHEDULE_INPUT = REPO_ROOT / "docs" / "data" / "schedule_future.json"
PROPOSAL_POLICY_INPUT = REPO_ROOT / "data" / "config" / "long_range_bls_inventory_policy.json"
PROPOSAL_OUTPUT = REPO_ROOT / "data" / "audit" / "long_range_bls_inventory_preview.json"


def build_proposed_inventory() -> None:
    subprocess.run(
        [sys.executable, "-m", "scripts.build_long_range_bls_inventory", "--output", str(PROPOSAL_OUTPUT)],
        cwd=REPO_ROOT,
        check=True,
    )


def build() -> None:
    reporter = BuildStatusReporter("build_courses")
    reporter.set_context(inputs=[ARCHIVE_INPUT, SCHEDULE_INPUT, PROPOSAL_POLICY_INPUT], outputs=[PROPOSAL_OUTPUT, OUTPUT])
    reporter.start()
    try:
        build_proposed_inventory()
        build_course_landers.main()
        generated = sorted(OUTPUT.glob("*.html"))
        reporter.done(
            current=len(generated),
            total=len(generated),
            last_output_file=generated[-1] if generated else None,
            pages_generated=len(generated),
            counts={"individual_course_landers": len(generated)},
        )
    except Exception:
        reporter.error()
        raise


if __name__ == "__main__":
    build()
