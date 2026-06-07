from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_status import BuildStatusReporter


def run_command(command: str, cwd: Path) -> int:
    print(f"$ {command}")
    completed = subprocess.run(command, cwd=str(cwd), shell=True)
    return completed.returncode


def run_python_script(script: Path, cwd: Path) -> int:
    print(f"$ {sys.executable} {script}")
    completed = subprocess.run([sys.executable, str(script)], cwd=str(cwd))
    return completed.returncode


def find_first_existing(root: Path, candidates: Iterable[str]) -> Optional[Path]:
    for rel in candidates:
        candidate = root / rel
        if candidate.exists():
            return candidate
    return None


def main() -> int:
    reporter = BuildStatusReporter("build_all_v4")
    parser = argparse.ArgumentParser(description="Combined 910CPR build runner")
    parser.add_argument("--root", default=".", help="Repo root")
    parser.add_argument("--skip-landers", action="store_true", help="Skip the lander build phase")
    parser.add_argument("--lander-cmd", default="", help="Exact command to run for lander generation")
    parser.add_argument("--index-cmd", default=r".\build\build_all_v3.bat", help="Command to run for index/data generation")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    data_dir = root / "data"
    if not data_dir.exists():
        print(f"ERROR: Missing data folder: {data_dir}")
        return 1

    course_candidates = ["course-export.xlsx", "enrollware_export.xlsx"]
    class_candidates = ["Class Report.xlsx", "class-report.xlsx"]

    course_file = find_first_existing(data_dir, course_candidates)
    class_file = find_first_existing(data_dir, class_candidates)

    if course_file is None:
        print("ERROR: Missing course export in data/")
        return 1
    if class_file is None:
        print("ERROR: Missing class report in data/")
        return 1

    public_steps = 1 if args.skip_landers else 2
    total_steps = public_steps + 1
    reporter.set_context(
        inputs=[course_file, class_file],
        outputs=[root / "docs", root / "data" / "runtime", root / "debug" / "status", root / "debug" / "control_booth_data.json"],
    )
    reporter.waiting(total=total_steps)
    print("=== 910CPR BUILD ALL V4 ===")
    print(f"Repo root    : {root}")
    print(f"Course export: {course_file}")
    print(f"Class report : {class_file}")
    print()

    print("=== CONFIG VALIDATION PHASE ===")
    rc = run_python_script(root / "scripts" / "validate_calendar_sources.py", root)
    if rc != 0:
        print("\nCONFIG VALIDATION FAILED.")
        reporter.error(current=0, total=total_steps, message="Calendar source config validation failed.")
        return rc
    print()

    print("=== INSTRUCTOR AVAILABILITY REPORT PHASE ===")
    rc = run_python_script(root / "scripts" / "build_instructor_availability_report.py", root)
    if rc != 0:
        print("\nWARNING: Instructor availability report failed. Continuing because this phase is report-only.")
    print()

    if not args.skip_landers:
        reporter.start(total=total_steps)
        print("=== LANDER BUILD PHASE ===")
        lander_cmd = args.lander_cmd.strip() or os.environ.get("LANDER_CMD", "").strip()

        if not lander_cmd:
            detected = find_first_existing(root, [
                "run_910cpr_landers.bat",
                "run_rebuild.bat",
                "run_landers_worker.bat",
            ])
            if detected is not None:
                if detected.suffix.lower() == ".bat":
                    lander_cmd = f'"{detected}"'
                else:
                    lander_cmd = str(detected)

        if lander_cmd:
            rc = run_command(lander_cmd, root)
            if rc != 0:
                print("\nLANDER BUILD FAILED.")
                reporter.error(current=0, total=total_steps, message="Lander build phase failed.")
                return rc
        else:
            print("No lander command found. Skipping lander phase.")
        reporter.update(current=1, total=total_steps, counts={"lander_phase_completed": True})
        print()
    else:
        reporter.start(total=total_steps)

    print("=== INDEX / DATA PHASE ===")
    rc = run_command(args.index_cmd, root)
    if rc != 0:
        print("\nINDEX PIPELINE FAILED.")
        reporter.error(current=total_steps - 1, total=total_steps, message="Index/data phase failed.")
        return rc
    reporter.update(current=public_steps, total=total_steps, counts={"public_build_completed": True})

    print("=== CONTROL BOOTH RECEIPT PHASE ===")
    rc = run_python_script(root / "scripts" / "build_control_booth.py", root)
    if rc != 0:
        print("\nCONTROL BOOTH RECEIPT FAILED.")
        print("Public build completed, but debug/control_booth_data.json was not regenerated.")
        reporter.error(current=public_steps, total=total_steps, message="Control Booth receipt generation failed after public build.")
        return rc

    reporter.done(
        current=total_steps,
        total=total_steps,
        counts={
            "skip_landers": args.skip_landers,
            "phases_completed": total_steps,
            "public_build_completed": True,
            "control_booth_receipt_completed": True,
        },
    )
    print("\nDONE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
