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
    index.write_text(fresh_html, encoding="utf-8")
    try:
        result = routes.refresh(
            root=root, retired_previous_ids=set(previous_ids) - public_ids
        )
    except Exception:
        index.write_text(old_html, encoding="utf-8")
        raise
    return {
        "listed": len(public_ids),
        "retired_previous": len(set(previous_ids) - public_ids),
        "route_files": result["files"],
    }


if __name__ == "__main__":
    print(json.dumps(refresh()))
