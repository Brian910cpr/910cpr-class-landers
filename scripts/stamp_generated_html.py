from __future__ import annotations

import argparse
from pathlib import Path

try:
    from scripts.build_metadata import apply_build_metadata, current_build_metadata
except ModuleNotFoundError:
    from build_metadata import apply_build_metadata, current_build_metadata


def iter_html(root: Path):
    for path in sorted(root.rglob("*.html")):
        parts = {part.lower() for part in path.parts}
        if "debug" in parts or "quarantine" in parts:
            continue
        yield path


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply shared BUILD_CODE metadata to generated HTML.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument("--source", default="full class lander rebuild")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    docs_dir = (repo_root / args.docs_dir).resolve()
    meta = current_build_metadata("scripts/stamp_generated_html.py", args.source)
    count = 0

    for path in iter_html(docs_dir):
        html = path.read_text(encoding="utf-8", errors="ignore")
        stamped = apply_build_metadata(html, meta)
        if stamped != html:
            path.write_text(stamped, encoding="utf-8")
        count += 1

    print(f"Stamped HTML files: {count}")
    print(f"Build: {meta.visible}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
