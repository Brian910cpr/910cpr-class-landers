"""Reject unapproved case-insensitive path collisions in the tracked Git tree."""

from __future__ import annotations

import subprocess
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# These public aliases are intentional and must remain independently representable.
# GitHub Pages serves paths case-sensitively, so uppercase legacy URLs can coexist
# with lowercase canonical pages when builds and publication run on Linux.
ALLOWED_COLLISIONS = {
    frozenset(("docs/ACLS.html", "docs/acls.html")),
    frozenset(("docs/BLS.html", "docs/bls.html")),
    frozenset(("docs/Earl/index.html", "docs/earl/index.html")),
    frozenset(("docs/HEARTSAVER.html", "docs/heartsaver.html")),
    frozenset(("docs/PALS.html", "docs/pals.html")),
}


def collision_groups(paths: list[str]) -> set[frozenset[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for path in paths:
        grouped[path.casefold()].append(path)
    return {frozenset(group) for group in grouped.values() if len(group) > 1}


def tracked_paths() -> list[str]:
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.splitlines()


def main() -> int:
    found = collision_groups(tracked_paths())
    unexpected = found - ALLOWED_COLLISIONS
    missing = ALLOWED_COLLISIONS - found

    print("Case-insensitive tracked-path collision inventory:")
    for group in sorted(found, key=lambda value: sorted(value, key=str.casefold)):
        status = "allowed" if group in ALLOWED_COLLISIONS else "UNAPPROVED"
        print(f"- [{status}] {' | '.join(sorted(group))}")

    if missing:
        print("\nExpected legacy collision groups no longer match the repository:", file=sys.stderr)
        for group in sorted(missing, key=lambda value: sorted(value, key=str.casefold)):
            print(f"- {' | '.join(sorted(group))}", file=sys.stderr)
    if unexpected:
        print("\nNew case-insensitive collisions are prohibited:", file=sys.stderr)
        for group in sorted(unexpected, key=lambda value: sorted(value, key=str.casefold)):
            print(f"- {' | '.join(sorted(group))}", file=sys.stderr)

    if missing or unexpected:
        return 1
    print(f"Validated {len(found)} approved collision groups; no new collisions found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
