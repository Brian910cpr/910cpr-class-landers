"""Refresh the public finder, numeric detail routes and sitemap as one job.

Preserve previously listed identities BEFORE regenerating the finder. Otherwise
an expired class omitted by the fresh source has no way to retire its stale,
still-directly-addressable detail page. This is the same-source, commit-gated
publication path; any error aborts the CI job before publication.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from scripts import refresh_class_finder_index as finder
from scripts import refresh_class_registration_routes as routes

ROOT = Path(__file__).resolve().parents[1]


def refresh(root: Path = ROOT) -> dict[str, int]:
    index = root / "docs/classes/index.html"
    old_html = index.read_text(encoding="utf-8")
    previous_ids = re.findall(
        r'class="class-finder-secondary" href="/classes/(\d+)\.html"',
        old_html,
    )
    if len(previous_ids) != len(set(previous_ids)):
        raise ValueError("duplicate previously published class identity")
    fresh_html, public_ids = finder.render_current_class_finder()
    # A concurrent source change between the finder and the route rewriter
    # causes the latter to fail closed, preventing the workflow's Git push.
    # Capture all potentially rewritten public artifacts before touching them:
    # route.refresh writes details and sitemap as well as the directory, and
    # an I/O failure halfway through must not leave a mixed local publication.
    # This is a runner-local rollback, not a substitute for the final CI gate
    # and all-or-nothing Git publication.
    snapshots = {index: index.read_bytes()}
    classes_dir = root / "docs/classes"
    snapshots.update(
        (path, path.read_bytes()) for path in classes_dir.glob("*.html")
        if path.is_file() and routes.DETAIL_ID.fullmatch(path.stem)
    )
    # Archive/topic indexes may be rewritten by the same guarded route refresh.
    # They need the same rollback coverage as finder, detail files and sitemap.
    for directory in routes.class_index.STALE_CLASS_INDEX_DIRS:
        relative = directory.relative_to(routes.class_index.ROOT)
        archive_dir = root / relative
        if archive_dir.is_dir():
            snapshots.update(
                (path, path.read_bytes()) for path in archive_dir.rglob("*.html")
                if path.is_file()
            )
    for archive in routes.class_index.STALE_CLASS_INDEX_FILES:
        relative = archive.relative_to(routes.class_index.ROOT)
        path = root / relative
        if path.is_file():
            snapshots[path] = path.read_bytes()
    sitemap = root / "docs/sitemap.xml"
    if sitemap.is_file():
        snapshots[sitemap] = sitemap.read_bytes()
    try:
        index.write_text(fresh_html, encoding="utf-8")
        result = routes.refresh(
            root=root, retired_previous_ids=set(previous_ids) - public_ids
        )
    except Exception:
        for path, original in snapshots.items():
            if not path.is_file() or path.read_bytes() != original:
                path.write_bytes(original)
        raise
    return {
        "listed": len(public_ids),
        "retired_previous": len(set(previous_ids) - public_ids),
        "route_files": result["files"],
    }


if __name__ == "__main__":
    print(json.dumps(refresh()))
