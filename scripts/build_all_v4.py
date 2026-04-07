from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Optional


def run_command(command: str, cwd: Path) -> int:
    print(f"$ {command}")
    completed = subprocess.run(command, cwd=str(cwd), shell=True)
    return completed.returncode


def find_first_existing(root: Path, candidates: Iterable[str]) -> Optional[Path]:
    for rel in candidates:
        candidate = root / rel
        if candidate.exists():
            return candidate
    return None


def main() -> int:
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

    print("=== 910CPR BUILD ALL V4 ===")
    print(f"Repo root    : {root}")
    print(f"Course export: {course_file}")
    print(f"Class report : {class_file}")
    print()

    if not args.skip_landers:
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
                return rc
        else:
            print("No lander command found. Skipping lander phase.")
        print()

    print("=== INDEX / DATA PHASE ===")
    rc = run_command(args.index_cmd, root)
    if rc != 0:
        print("\nINDEX PIPELINE FAILED.")
        return rc

    print("\nDONE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
