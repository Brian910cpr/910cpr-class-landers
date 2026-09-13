"""Read-only, value-free admin auth inventory from an exact committed Git tree.

This is a literal/source-reference inventory, not JavaScript execution or proof
of authorization. It never reads browser storage, environment values or APIs.
"""
from __future__ import annotations

import argparse
import json
import posixpath
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
STORAGE = re.compile(r"\b(sessionStorage|localStorage)\s*\.\s*(getItem|setItem|removeItem)\s*\(\s*([^,)\n]+)")
LITERAL = re.compile(r"^(['\"])([^'\"\n]*)\1$")
ASSIGN = re.compile(r"\b([A-Za-z_$][\w$]*)\s*=\s*(['\"])([^'\"\n]*)\2")
TOKENS = ("hotSyncAdminKey", "HOT_SYNC_ADMIN_KEY", "X-Hot-Sync-Admin-Key",
          "maximPortalSession", "x-maxim-session", "authorization")
ENDPOINTS = (
    "worker/admin-api.js", "worker/finance-worker.js",
    "supabase/functions/canonical-session-workspace/index.ts",
    "supabase/functions/class-registry/index.ts",
    "supabase/functions/production-board/index.ts",
    "supabase/functions/instructor-workbench/index.ts",
    "supabase/functions/session-workspace/index.ts",
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8")


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and attrs.get("src"):
            self.assets.append(attrs["src"])
        if tag == "link" and "stylesheet" in attrs.get("rel", "").split() and attrs.get("href"):
            self.assets.append(attrs["href"])


def asset_path(page: str, reference: str) -> str | None:
    parts = urlsplit(reference)
    if parts.scheme or parts.netloc:
        return None
    # Discard query/fragment values: source assets can carry private parameters.
    base = "docs" if parts.path.startswith("/") else posixpath.dirname(page)
    path = posixpath.normpath(posixpath.join(base, parts.path.lstrip("/")))
    return path if path.startswith("docs/") else None


def inspect_source(path: str, source: str) -> dict:
    assignments = {}
    for match in ASSIGN.finditer(source):
        assignments.setdefault(match[1], set()).add(match[3])
    storage = []
    for match in STORAGE.finditer(source):
        expression = match[3].strip()
        literal = LITERAL.fullmatch(expression)
        candidates = assignments.get(expression, set())
        key = literal[2] if literal else next(iter(candidates)) if len(candidates) == 1 else None
        storage.append({"line": source.count("\n", 0, match.start()) + 1,
                        "store": match[1], "operation": match[2], "key": key,
                        "resolution": "literal" if literal else "constant_candidate" if key else "unresolved"})
    # Dot-property access is separate from Storage methods.
    for match in re.finditer(r"\b(sessionStorage|localStorage)\s*\.\s*([A-Za-z_$][\w$]*)", source):
        if match[2] not in {"getItem", "setItem", "removeItem", "clear", "key", "length"}:
            storage.append({"line": source.count("\n", 0, match.start()) + 1,
                            "store": match[1], "operation": "property_reference", "key": match[2],
                            "resolution": "property"})
    token_lines = {token: [i for i, line in enumerate(source.splitlines(), 1)
                          if token.lower() in line.lower()] for token in TOKENS}
    # Only operation locations are recorded, never arguments, values or snippets.
    markers = {name: [source.count("\n", 0, m.start()) + 1 for m in re.finditer(pattern, source)]
               for name, pattern in {
                   "prompt_calls": r"\bprompt\s*\(",
                   "fetch_calls": r"\bfetch\s*\(",
                   "xhr_header_calls": r"\.setRequestHeader\s*\(",
                   "status_401_mentions": r"\b401\b",
                   "status_403_mentions": r"\b403\b",
                   "storage_clear_calls": r"\b(?:sessionStorage|localStorage)\s*\.\s*clear\s*\(",
               }.items()}
    parser = References()
    if path.endswith(".html"):
        parser.feed(source)
    dependencies = sorted({p for ref in parser.assets if (p := asset_path(path, ref))})
    return {"path": path, "line_count": len(source.splitlines()), "storage": storage,
            "token_lines": {k: v for k, v in token_lines.items() if v},
            "markers": {k: v for k, v in markers.items() if v}, "direct_assets": dependencies}


def build_inventory(ref: str) -> dict:
    commit = git("rev-parse", "--verify", "--end-of-options", ref + "^{commit}").strip()
    tracked = set(git("ls-tree", "-r", "--name-only", commit, "docs").splitlines())
    files = {p for p in tracked if p.startswith("docs/admin/")}
    admin_files = set(files)
    records = {}
    pending = sorted(files)
    while pending:
        path = pending.pop(0)
        if path in records:
            continue
        exists = path in tracked
        source = git("show", f"{commit}:{path}") if exists else ""
        record = inspect_source(path, source)
        record["exists_in_source_commit"] = exists
        record["scope"] = "admin_file" if path in admin_files else "referenced_asset"
        records[path] = record
        pending.extend(p for p in record["direct_assets"] if p not in records)
    for path in ENDPOINTS:
        record = inspect_source(path, git("show", f"{commit}:{path}"))
        record["exists_in_source_commit"] = True
        record["scope"] = "endpoint_boundary"
        records[path] = record
    for path, record in records.items():
        if record["scope"] != "referenced_asset":
            continue
        result = subprocess.run(["git", "grep", "-I", "-l", "-F", "-e", posixpath.basename(path),
                                 commit, "--", "docs"], cwd=ROOT, text=True, encoding="utf-8", capture_output=True)
        if result.returncode not in (0, 1):
            raise RuntimeError("Git reference inventory failed")
        matches = sorted(set(line.split(":", 1)[1] for line in result.stdout.splitlines()))
        outside = [p for p in matches if not p.startswith("docs/admin/") and p != path]
        record["reference_matches"] = {"total": len(matches), "outside_admin": len(outside),
                                       "outside_admin_examples": outside[:5]}
    return {"schema_version": 1, "source_commit": commit,
            "contract": {"secret_name": "HOT_SYNC_ADMIN_KEY", "storage_key": "sessionStorage.hotSyncAdminKey",
                         "header": "X-Hot-Sync-Admin-Key"},
            "counts": {"admin_files": len(admin_files),
                       "admin_html_pages": sum(p.endswith(".html") for p in admin_files),
                       "referenced_assets": sum(r["scope"] == "referenced_asset" for r in records.values()),
                       "missing_referenced_assets": sum(not r["exists_in_source_commit"] for r in records.values()),
                       "endpoint_boundaries": len(ENDPOINTS)},
            "limitations": ["Literal matches and constant candidates require manual semantic review.",
                            "Does not execute JavaScript, resolve imports/dynamic assets or prove server authorization.",
                            "Only source storage key identifiers and known contract tokens are recorded; no stored values.",
                            "Reference matching by asset basename is conservative, not a complete runtime dependency graph.",
                            "No remote APIs, browser storage, credentials or operational records were read."],
            "files": [records[p] for p in sorted(records)]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_inventory(args.ref)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_commit": result["source_commit"], "counts": result["counts"],
                      "output": args.output.as_posix()}))


if __name__ == "__main__":
    main()
