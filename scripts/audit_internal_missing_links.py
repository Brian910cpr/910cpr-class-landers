from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse


csv.field_size_limit(10_000_000)

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
DEBUG_DIR = ROOT / "debug"

INPUT_MISSING_LINKS = DEBUG_DIR / "gsc_404_missing_internal_links.csv"
INPUT_GSC_AUDIT = DEBUG_DIR / "gsc_404_url_audit.json"
SITEMAP_PATH = DOCS_DIR / "sitemap.xml"

OUT_JSON = DEBUG_DIR / "internal_missing_links_audit.json"
OUT_SUMMARY = DEBUG_DIR / "internal_missing_links_summary.md"
OUT_BY_SOURCE = DEBUG_DIR / "internal_missing_links_by_source.csv"
OUT_BY_TARGET = DEBUG_DIR / "internal_missing_links_by_target.csv"

HREF_RE = re.compile(r"""<(?P<tag>[a-zA-Z0-9:-]+)\b[^>]*(?P<attr>href|src)\s*=\s*["'](?P<href>[^"']+)["'][^>]*>""", re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s,\"'<>]+|/[A-Za-z0-9._~!$&'()*+,;=:@%/?#-]+")


@dataclass
class LinkFinding:
    source_file: str
    target_href: str
    normalized_target: str
    expected_local_file: str
    context: str
    family: str
    appears_in_sitemap: bool
    appears_in_data_json: bool
    is_gsc_audited_url: bool
    priority: str
    likely_type: str
    recommendation: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def normalize_path(raw: str, source_file: Path | None = None) -> tuple[str, str]:
    raw = raw.strip()
    parsed = urlparse(raw)
    if parsed.scheme and parsed.netloc:
        return unquote(parsed.path or "/"), parsed.query
    if raw.startswith("//"):
        parsed = urlparse("https:" + raw)
        return unquote(parsed.path or "/"), parsed.query
    if raw.startswith("/"):
        parsed = urlparse(raw)
        return unquote(parsed.path or "/"), parsed.query

    clean = raw.split("#", 1)[0]
    query = ""
    if "?" in clean:
        clean, query = clean.split("?", 1)
    if source_file is not None:
        try:
            resolved = (source_file.parent / clean).resolve()
            path = "/" + resolved.relative_to(DOCS_DIR.resolve()).as_posix()
        except ValueError:
            path = "/" + clean.lstrip("/")
    else:
        path = "/" + clean.lstrip("/")
    return unquote(path), query


def local_refs(path: str, query: str = "") -> set[str]:
    refs = {path, path.lstrip("/")}
    if query:
        refs.add(f"{path}?{query}")
        refs.add(f"{path.lstrip('/')}?{query}")
    return refs


def expected_file(path: str) -> Path:
    if path == "/":
        return DOCS_DIR / "index.html"
    if path.endswith("/"):
        return DOCS_DIR / path.lstrip("/") / "index.html"
    return DOCS_DIR / path.lstrip("/")


def classify_family(path: str, query: str, href: str = "") -> str:
    low_href = href.lower()
    if href.startswith("#"):
        return "anchor_only"
    if low_href.startswith(("mailto:", "tel:", "sms:", "javascript:", "data:")):
        return "other"
    if urlparse(href).scheme in {"http", "https"} and "910cpr.com" not in urlparse(href).netloc:
        return "external"
    if re.search(r"\.(png|jpe?g|gif|webp|svg|ico|css|js|pdf|zip|json|xml|txt)$", path, re.IGNORECASE):
        return "asset"
    if re.fullmatch(r"/classes/\d+\.html", path):
        return "class_numeric"
    if re.fullmatch(r"/classes/session_[^/]+\.html", path):
        return "class_session_slug"
    if re.fullmatch(r"/courses/[^/]+\.html", path):
        return "course"
    if re.fullmatch(r"/fliers/[^/]+\.html", path):
        return "flier"
    if re.fullmatch(r"/locations/[^/]+\.html", path):
        return "location"
    if re.fullmatch(r"/landers/job/[^/]+\.html", path):
        return "job_lander"
    if query or (path == "/which-class.html" and "near=" in parse_qs(query)):
        return "query_route"
    return "other"


def load_missing_links_csv() -> dict[str, list[str]]:
    if not INPUT_MISSING_LINKS.exists():
        raise FileNotFoundError(f"Missing {INPUT_MISSING_LINKS}")
    out: dict[str, list[str]] = {}
    with INPUT_MISSING_LINKS.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            path = (row.get("path") or "").strip()
            sources = [s for s in (row.get("sources") or "").split("|") if s]
            if path:
                out[path] = sources
    return out


def load_gsc_audited_refs() -> set[str]:
    if not INPUT_GSC_AUDIT.exists():
        return set()
    data = json.loads(read_text(INPUT_GSC_AUDIT))
    refs = set()
    for row in data.get("audits", []):
        path = row.get("path") or ""
        query = row.get("query") or ""
        refs.update(local_refs(path, query))
    return refs


def load_sitemap_refs() -> set[str]:
    if not SITEMAP_PATH.exists():
        return set()
    refs = set()
    for url in URL_RE.findall(read_text(SITEMAP_PATH)):
        path, query = normalize_path(url)
        refs.update(local_refs(path, query))
    return refs


def load_data_refs() -> set[str]:
    refs = set()
    data_dir = DOCS_DIR / "data"
    if not data_dir.exists():
        return refs
    for json_file in data_dir.rglob("*.json"):
        text = read_text(json_file)
        for url in URL_RE.findall(text):
            path, query = normalize_path(url)
            refs.update(local_refs(path, query))
    return refs


def source_href_index(source_file: Path) -> dict[str, list[tuple[str, str]]]:
    index: dict[str, list[tuple[str, str]]] = defaultdict(list)
    if not source_file.exists():
        return index
    text = read_text(source_file)
    for match in HREF_RE.finditer(text):
        href = match.group("href")
        low = href.lower()
        if href.startswith("#") or low.startswith(("mailto:", "tel:", "sms:", "javascript:", "data:")):
            continue
        path, query = normalize_path(href, source_file)
        context = re.sub(r"\s+", " ", match.group(0)).strip()
        if len(context) > 260:
            context = context[:257] + "..."
        for ref in local_refs(path, query):
            index[ref].append((href, context))
    return index


def classify_priority_and_recommendation(
    family: str,
    source_file: str,
    target: str,
    in_sitemap: bool,
    in_data: bool,
    is_gsc: bool,
) -> tuple[str, str, str]:
    source_lower = source_file.lower()

    if family in {"anchor_only", "external", "asset"}:
        return "false_positive", "false_positive", "ignore as false positive"
    if family == "query_route":
        return "review", "query_route", "redirect or route/rewrite if intentional"
    if "/classes/months/" in source_lower or "/classes/cities/" in source_lower or "/classes/courses/" in source_lower or "/classes/certifying-bodies/" in source_lower:
        likely = "old_generated_reference"
    elif "canonical" in source_lower or target in source_file:
        likely = "self_or_canonical_artifact"
    else:
        likely = "real_broken_link"

    if family in {"class_numeric", "class_session_slug"}:
        rec = "restore page or update generated index/hub target"
    elif family in {"course", "location", "job_lander"}:
        rec = "restore page, redirect, or update target"
    elif family == "flier":
        rec = "restore page/asset or remove link"
    else:
        rec = "remove link, restore page, redirect, or update target"

    if is_gsc or in_sitemap or in_data:
        priority = "fix"
    elif likely == "old_generated_reference":
        priority = "fix_generated_source"
    else:
        priority = "review"
    return priority, likely, rec


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def build_summary(findings: list[LinkFinding], by_target: list[dict[str, Any]], by_source: list[dict[str, Any]]) -> str:
    family_counts = Counter(f.family for f in findings)
    priority_counts = Counter(f.priority for f in findings)
    likely_counts = Counter(f.likely_type for f in findings)
    top_sources = by_source[:25]
    top_targets = by_target[:25]
    user_facing = [f for f in findings if f.priority in {"fix", "fix_generated_source", "review"} and f.family not in {"asset", "anchor_only", "external"}]
    false_or_low = [f for f in findings if f.priority == "false_positive" or f.likely_type in {"self_or_canonical_artifact"}]

    lines = [
        "# Internal Missing Links Follow-Up Audit",
        "",
        f"- Total missing internal link occurrences: {len(findings)}",
        f"- Unique missing target paths: {len(by_target)}",
        f"- User-facing or review-needed occurrences: {len(user_facing)}",
        f"- False-positive or low-priority occurrences: {len(false_or_low)}",
        "",
        "## Counts By Family",
        "",
    ]
    for key, value in sorted(family_counts.items()):
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Counts By Priority", ""])
    for key, value in sorted(priority_counts.items()):
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Counts By Likely Type", ""])
    for key, value in sorted(likely_counts.items()):
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Top 25 Source Files Creating Missing Links", ""])
    for row in top_sources:
        lines.append(f"- {row['source_file']}: {row['missing_link_count']} links, {row['unique_target_count']} targets")

    lines.extend(["", "## Top 25 Missing Targets", ""])
    for row in top_targets:
        lines.append(f"- {row['normalized_target']}: {row['source_count']} sources, {row['occurrence_count']} occurrences, family={row['family']}")

    lines.extend(["", "## User-Facing Fix Guidance", ""])
    lines.append("- `fix`: restore the missing page, redirect it, or update the link target before relying on the page.")
    lines.append("- `fix_generated_source`: likely generated hub/index references; update generation inputs/templates, then rebuild.")
    lines.append("- `review`: inspect manually, often query routes or miscellaneous HTML paths.")
    lines.append("- `false_positive`: ignored protocols, external links, anchors, or assets that should not be treated as missing docs pages.")

    lines.extend(["", "## Recommendation Types", ""])
    rec_counts = Counter(f.recommendation for f in findings)
    for rec, count in rec_counts.most_common():
        lines.append(f"- {rec}: {count}")

    return "\n".join(lines) + "\n"


def main() -> int:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    missing_by_target = load_missing_links_csv()
    gsc_refs = load_gsc_audited_refs()
    sitemap_refs = load_sitemap_refs()
    data_refs = load_data_refs()

    source_cache: dict[str, dict[str, list[tuple[str, str]]]] = {}
    findings: list[LinkFinding] = []

    for target, sources in sorted(missing_by_target.items()):
        target_path, target_query = normalize_path(target)
        expected = expected_file(target_path)
        target_refs = local_refs(target_path, target_query)
        in_sitemap = bool(target_refs & sitemap_refs)
        in_data = bool(target_refs & data_refs)
        is_gsc = bool(target_refs & gsc_refs)

        for source in sources:
            source_path = ROOT / source
            if source not in source_cache:
                source_cache[source] = source_href_index(source_path)
            matches: list[tuple[str, str]] = []
            for ref in target_refs:
                matches.extend(source_cache[source].get(ref, []))
            matches = list(dict.fromkeys(matches))
            if not matches:
                matches = [("", "target listed by prior reverse audit; exact href not recovered")]

            for href, context in matches:
                family = classify_family(target_path, target_query, href)
                priority, likely_type, recommendation = classify_priority_and_recommendation(
                    family,
                    source,
                    target_path,
                    in_sitemap,
                    in_data,
                    is_gsc,
                )
                findings.append(
                    LinkFinding(
                        source_file=source,
                        target_href=href,
                        normalized_target=target_path + (f"?{target_query}" if target_query else ""),
                        expected_local_file=expected.relative_to(ROOT).as_posix(),
                        context=context,
                        family=family,
                        appears_in_sitemap=in_sitemap,
                        appears_in_data_json=in_data,
                        is_gsc_audited_url=is_gsc,
                        priority=priority,
                        likely_type=likely_type,
                        recommendation=recommendation,
                    )
                )

    by_source_counter: dict[str, list[LinkFinding]] = defaultdict(list)
    by_target_counter: dict[str, list[LinkFinding]] = defaultdict(list)
    for finding in findings:
        by_source_counter[finding.source_file].append(finding)
        by_target_counter[finding.normalized_target].append(finding)

    by_source = [
        {
            "source_file": source,
            "missing_link_count": len(rows),
            "unique_target_count": len({r.normalized_target for r in rows}),
            "families": "|".join(sorted({r.family for r in rows})),
            "priorities": "|".join(sorted({r.priority for r in rows})),
        }
        for source, rows in by_source_counter.items()
    ]
    by_source.sort(key=lambda row: (-row["missing_link_count"], row["source_file"]))

    by_target = [
        {
            "normalized_target": target,
            "occurrence_count": len(rows),
            "source_count": len({r.source_file for r in rows}),
            "family": Counter(r.family for r in rows).most_common(1)[0][0],
            "priority": Counter(r.priority for r in rows).most_common(1)[0][0],
            "likely_type": Counter(r.likely_type for r in rows).most_common(1)[0][0],
            "appears_in_sitemap": any(r.appears_in_sitemap for r in rows),
            "appears_in_data_json": any(r.appears_in_data_json for r in rows),
            "is_gsc_audited_url": any(r.is_gsc_audited_url for r in rows),
            "recommendation": Counter(r.recommendation for r in rows).most_common(1)[0][0],
            "sources": "|".join(sorted({r.source_file for r in rows})),
        }
        for target, rows in by_target_counter.items()
    ]
    by_target.sort(key=lambda row: (-row["occurrence_count"], row["normalized_target"]))

    payload = {
        "input": str(INPUT_MISSING_LINKS.relative_to(ROOT)),
        "total_missing_link_occurrences": len(findings),
        "unique_missing_target_paths": len(by_target),
        "findings": [asdict(finding) for finding in findings],
        "by_source": by_source,
        "by_target": by_target,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    OUT_SUMMARY.write_text(build_summary(findings, by_target, by_source), encoding="utf-8")

    write_csv(
        OUT_BY_SOURCE,
        by_source,
        ["source_file", "missing_link_count", "unique_target_count", "families", "priorities"],
    )
    write_csv(
        OUT_BY_TARGET,
        by_target,
        [
            "normalized_target",
            "occurrence_count",
            "source_count",
            "family",
            "priority",
            "likely_type",
            "appears_in_sitemap",
            "appears_in_data_json",
            "is_gsc_audited_url",
            "recommendation",
            "sources",
        ],
    )

    print(f"Loaded {len(missing_by_target)} unique missing targets from {INPUT_MISSING_LINKS}")
    print(f"Expanded to {len(findings)} source-target occurrences")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_BY_SOURCE}")
    print(f"Wrote {OUT_BY_TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
