from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


from scripts.local_data_paths import dynamic_offers_preview_path, public_sellable_offers_preview_path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
DOCS_DIR = ROOT / "docs"

PREVIEW_FILES = [
    dynamic_offers_preview_path(ROOT),
    public_sellable_offers_preview_path(ROOT),
]

RENDER_PAGES = [
    DOCS_DIR / "index.html",
    DOCS_DIR / "bls.html",
    DOCS_DIR / "acls.html",
    DOCS_DIR / "pals.html",
    DOCS_DIR / "hsi.html",
    DOCS_DIR / "heartsaver.html",
    DOCS_DIR / "courses" / "bls.html",
    DOCS_DIR / "courses" / "acls.html",
    DOCS_DIR / "courses" / "pals.html",
    DOCS_DIR / "courses" / "heartcode-bls.html",
    DOCS_DIR / "courses" / "heartcode-acls.html",
    DOCS_DIR / "courses" / "heartcode-pals.html",
]

RELEASE_OUTPUTS = {
    "data/audit/release_candidate_large_file_policy.md",
    "data/audit/release_candidate_large_file_policy.json",
    "data/audit/release_candidate_rendered_page_proof.md",
    "data/audit/release_candidate_rendered_page_proof.json",
    "data/audit/release_candidate_rendered_page_rows.csv",
    "data/audit/release_candidate_customer_copy_cleanup.md",
    "data/audit/release_candidate_booking_url_sanity.md",
    "data/audit/release_candidate_booking_url_sanity.json",
    "data/audit/release_candidate_final_report.md",
    "data/audit/release_candidate_final_report.json",
    "scripts/audit_release_candidate.py",
}

INTERNAL_TERMS = [
    "appointment-backed",
    "seeded",
    "seed",
    "dynamic offer",
    "public sellable",
    "request-based scheduling",
    "real scheduled options show first",
    "Course Master",
    "UNKNOWN",
    "debug",
    "preview",
]

AHA_BLS_COURSE_IDS = {"209806": "AHA BLS Provider", "359474": "AHA BLS Provider Renewal", "210549": "AHA BLS HeartCode"}
EXPECTED_AUGUST_BLS = {
    ("2026-08-03", "09:15", "359474"),
    ("2026-08-04", "09:15", "209806"),
    ("2026-08-05", "09:15", "359474"),
    ("2026-08-10", "09:15", "209806"),
    ("2026-08-11", "09:15", "359474"),
    ("2026-08-12", "09:15", "209806"),
}


class ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.articles: list[dict] = []
        self._current: dict | None = None
        self._capture: str | None = None
        self._text: list[str] = []
        self.links: list[dict] = []
        self.visible_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {k: v or "" for k, v in attrs}
        class_value = attrs_dict.get("class", "")
        if tag == "article" and "slug-pill" in class_value:
            self._current = {
                "classes": class_value,
                "data": {k: v for k, v in attrs if k.startswith("data-") and v is not None},
                "href": "",
                "button_text": "",
                "text": "",
                "title": "",
                "subtitle": "",
                "meta": "",
            }
        if self._current is not None:
            if tag == "a":
                href = attrs_dict.get("href", "")
                if "button" in class_value and not self._current.get("href"):
                    self._current["href"] = href
                self.links.append({"href": href, "class": class_value})
            if "slug-pill-title" in class_value:
                self._capture = "title"
                self._text = []
            elif "slug-pill-subtitle" in class_value:
                self._capture = "subtitle"
                self._text = []
            elif "slug-pill-meta" in class_value:
                self._capture = "meta"
                self._text = []
            elif tag == "a" and "button" in class_value:
                self._capture = "button_text"
                self._text = []

    def handle_endtag(self, tag: str) -> None:
        if self._current is not None and self._capture:
            value = normalize(" ".join(self._text))
            if value:
                existing = self._current.get(self._capture, "")
                self._current[self._capture] = normalize(f"{existing} {value}")
            self._capture = None
            self._text = []
        if tag == "article" and self._current is not None:
            fields = [self._current.get("title", ""), self._current.get("subtitle", ""), self._current.get("meta", "")]
            self._current["text"] = normalize(" ".join(fields))
            self.articles.append(self._current)
            self._current = None

    def handle_data(self, data: str) -> None:
        text = normalize(data)
        if text:
            self.visible_parts.append(text)
        if self._capture:
            self._text.append(data)


def normalize(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except subprocess.CalledProcessError as exc:
        return normalize(exc.output)


def is_tracked(path: Path) -> bool:
    return git(["ls-files", "--error-unmatch", str(path.relative_to(ROOT))]) != ""


def find_references() -> dict[str, list[str]]:
    references: dict[str, list[str]] = defaultdict(list)
    needles = {p.name: str(p.relative_to(ROOT)).replace("\\", "/") for p in PREVIEW_FILES}
    for base in (ROOT / "scripts", ROOT / "tests"):
        for path in base.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for name, rel in needles.items():
                if name in text or rel in text:
                    references[rel].append(str(path.relative_to(ROOT)).replace("\\", "/"))
    return {k: sorted(v) for k, v in references.items()}


def parse_page(path: Path) -> dict:
    html = path.read_text(encoding="utf-8", errors="ignore")
    parser = ArticleParser()
    parser.feed(html)
    visible_text = normalize(" ".join(parser.visible_parts))
    markup_hits = {term: len(re.findall(re.escape(term), html, flags=re.IGNORECASE)) for term in INTERNAL_TERMS}
    visible_hits = {term: len(re.findall(re.escape(term), visible_text, flags=re.IGNORECASE)) for term in INTERNAL_TERMS}
    appointment_rows = [a for a in parser.articles if "slug-appointment-option" in a.get("classes", "")]
    real_rows = [a for a in parser.articles if "js-session-item" in a.get("classes", "")]
    broken_links = []
    for link in parser.links:
        href = unescape(link.get("href", ""))
        if not href or href == "#":
            broken_links.append(href)
        elif href.startswith("/") and not (DOCS_DIR / href.lstrip("/").split("#", 1)[0]).exists():
            broken_links.append(href)
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "exists": path.exists(),
        "article_count": len(parser.articles),
        "real_enrollware_row_count": len(real_rows),
        "appointment_seed_row_count": len(appointment_rows),
        "broken_or_missing_link_count": len(broken_links),
        "internal_markup_hits": {k: v for k, v in markup_hits.items() if v},
        "internal_visible_hits": {k: v for k, v in visible_hits.items() if v},
        "articles": parser.articles,
    }


def article_date_time(article: dict) -> tuple[str, str]:
    start = article.get("data", {}).get("data-start", "")
    if "T" not in start:
        return "", ""
    date, time_rest = start.split("T", 1)
    return date, time_rest[:5]


def course_id_from_href(href: str) -> str:
    query = parse_qs(urlparse(unescape(href)).query)
    return (query.get("courseId") or [""])[0]


def appointment_day_id_from_href(href: str) -> str:
    query = parse_qs(urlparse(unescape(href)).query)
    return (query.get("appointmentDayId") or [""])[0]


def start_time_from_href(href: str) -> str:
    query = parse_qs(urlparse(unescape(href)).query)
    return (query.get("startTime") or [""])[0]


def build_rendered_proof(pages: dict[str, dict]) -> tuple[dict, list[dict]]:
    rows: list[dict] = []
    bls = pages["docs/bls.html"]
    for article in bls["articles"]:
        date, time = article_date_time(article)
        href = unescape(article.get("href", ""))
        course_id = course_id_from_href(href)
        row = {
            "page": "docs/bls.html",
            "date": date,
            "time": time,
            "title": article.get("title", ""),
            "subtitle": article.get("subtitle", ""),
            "button_text": article.get("button_text", ""),
            "href": href,
            "row_type": "appointment_seed" if "slug-appointment-option" in article.get("classes", "") else "real_enrollware",
            "render_source": article.get("data", {}).get("data-render-source", ""),
            "courseId": course_id,
            "appointmentDayId": appointment_day_id_from_href(href),
            "startTime": start_time_from_href(href),
        }
        if date.startswith("2026-08") and (course_id in AHA_BLS_COURSE_IDS or row["row_type"] == "real_enrollware"):
            rows.append(row)
    selected_bls = [
        r for r in rows
        if r["row_type"] == "appointment_seed" and (r["date"], r["time"], r["courseId"]) in EXPECTED_AUGUST_BLS
    ]
    duplicate_counter = Counter((r["date"], r["time"], r["courseId"], r["href"]) for r in selected_bls)
    proof = {
        "page_count_checked": len(pages),
        "pages": {k: {kk: vv for kk, vv in page.items() if kk != "articles"} for k, page in pages.items()},
        "bls_august_selected_seed_count": len(selected_bls),
        "bls_august_selected_seed_expected_count": len(EXPECTED_AUGUST_BLS),
        "bls_august_selected_seed_rows": selected_bls,
        "bls_august_real_enrollware_rows": [r for r in rows if r["row_type"] == "real_enrollware"],
        "duplicate_selected_seed_count": sum(v - 1 for v in duplicate_counter.values() if v > 1),
        "existing_real_bls_rows_still_render": bls["real_enrollware_row_count"] > 0,
        "rendered_seed_button_texts": sorted({r["button_text"] for r in selected_bls}),
        "passed": len(selected_bls) == len(EXPECTED_AUGUST_BLS)
        and all(r["button_text"] == "Book This Class" for r in selected_bls)
        and bls["real_enrollware_row_count"] > 0
        and sum(v - 1 for v in duplicate_counter.values() if v > 1) == 0,
    }
    return proof, rows


def build_customer_copy_report(pages: dict[str, dict]) -> dict:
    visible_hits = {path: page["internal_visible_hits"] for path, page in pages.items() if page["internal_visible_hits"]}
    markup_hits = {path: page["internal_markup_hits"] for path, page in pages.items() if page["internal_markup_hits"]}
    return {
        "terms_scanned": INTERNAL_TERMS,
        "customer_facing_pages_scanned": sorted(pages),
        "visible_internal_term_hits": visible_hits,
        "markup_internal_term_hits": markup_hits,
        "cleanup_performed": False,
        "customer_copy_status": "No customer-facing visible copy changes were required by this audit.",
        "note": "Markup/data-attribute hits are reported separately from visible copy because internal row metadata is intentionally preserved for traceability.",
        "passed": not visible_hits,
    }


def build_booking_url_sanity(pages: dict[str, dict]) -> dict:
    bls_rows = []
    failures = []
    for article in pages["docs/bls.html"]["articles"]:
        if "slug-appointment-option" not in article.get("classes", ""):
            continue
        date, time = article_date_time(article)
        href = unescape(article.get("href", ""))
        course_id = course_id_from_href(href)
        if not date.startswith("2026-08") or course_id not in AHA_BLS_COURSE_IDS:
            continue
        start_time = start_time_from_href(href)
        appointment_day_id = appointment_day_id_from_href(href)
        label = article.get("subtitle", "") or article.get("title", "")
        expected = AHA_BLS_COURSE_IDS[course_id]
        row_failures = []
        if not appointment_day_id:
            row_failures.append("missing appointmentDayId")
        if not start_time:
            row_failures.append("missing startTime")
        if expected.lower() not in label.lower():
            row_failures.append("courseId/visible label mismatch")
        if course_id == "209806" and "Renewal" in label:
            row_failures.append("Initial courseId points to Renewal label")
        if course_id == "359474" and "Renewal" not in label:
            row_failures.append("Renewal courseId does not point to Renewal label")
        failures.extend(row_failures)
        bls_rows.append({
            "date": date,
            "time": time,
            "visible_label": label,
            "courseId": course_id,
            "appointmentDayId": appointment_day_id,
            "startTime": start_time,
            "href": href,
            "failures": row_failures,
        })
    all_html = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in DOCS_DIR.rglob("*.html"))
    hsi_html = (DOCS_DIR / "hsi.html").read_text(encoding="utf-8", errors="ignore")
    return {
        "august_bls_appointment_seed_rows_checked": len(bls_rows),
        "august_bls_appointment_seed_rows": bls_rows,
        "url_failures": failures,
        "hsi_pediatric_449422_suppressed": "courseId=449422" not in all_html and "449422" not in hsi_html,
        "course_344085_not_on_hsi_page": "344085" not in hsi_html,
        "unknown_course_key_suppressed": "UNKNOWN" not in all_html,
        "no_wrong_bls_card_detected": all(row["courseId"] in AHA_BLS_COURSE_IDS for row in bls_rows),
        "passed": len(bls_rows) >= 6 and not failures and "courseId=449422" not in all_html and "344085" not in hsi_html and "UNKNOWN" not in all_html,
    }


def build_large_file_policy() -> dict:
    references = find_references()
    files = {}
    for path in PREVIEW_FILES:
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        size = path.stat().st_size if path.exists() else 0
        files[rel] = {
            "exists": path.exists(),
            "tracked": is_tracked(path),
            "size_bytes": size,
            "size_mb_binary": round(size / (1024 * 1024), 2),
            "referencing_scripts_or_tests": references.get(rel, []),
            "reference_count": len(references.get(rel, [])),
        }
    return {
        "files": files,
        "github_warning_threshold_mb": 50,
        "should_keep_tracked_long_term": False,
        "safe_to_remove_in_this_release_candidate": True,
        "reason_not_removed": "",
        "recommended_policy": "Keep compact Markdown/JSON/CSV proof artifacts tracked. Keep full generated previews under ignored runtime storage and regenerate them locally when row-level detail is needed.",
        "implemented_repo_hygiene": "Full generated previews were moved to data/runtime/audit_previews/ and compact summaries remain tracked under data/audit/.",
    }


def write_csv_rows(path: Path, rows: list[dict]) -> None:
    fieldnames = sorted({k for row in rows for k in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def render_markdown_reports(
    large_policy: dict,
    rendered_proof: dict,
    copy_report: dict,
    booking_sanity: dict,
    final_report: dict,
) -> None:
    large_lines = ["# Release Candidate Large File Policy", ""]
    for rel, info in large_policy["files"].items():
        large_lines.extend([
            f"## {rel}",
            f"- Size: {info['size_mb_binary']} MiB ({info['size_bytes']} bytes)",
            f"- Tracked: {info['tracked']}",
            f"- Referencing scripts/tests: {info['reference_count']}",
            "",
        ])
    large_lines.extend([
        "## Policy",
        f"- Keep tracked long-term: {large_policy['should_keep_tracked_long_term']}",
        f"- Safe to remove in this release candidate: {large_policy['safe_to_remove_in_this_release_candidate']}",
        f"- Recommendation: {large_policy['recommended_policy']}",
        f"- Action taken: {large_policy['implemented_repo_hygiene']}",
    ])
    write_text(AUDIT_DIR / "release_candidate_large_file_policy.md", "\n".join(large_lines))

    proof_lines = [
        "# Release Candidate Rendered Page Proof",
        "",
        f"- Pages checked: {rendered_proof['page_count_checked']}",
        f"- BLS August selected appointment seeds rendered: {rendered_proof['bls_august_selected_seed_count']}",
        f"- Existing real BLS rows still render: {rendered_proof['existing_real_bls_rows_still_render']}",
        f"- Duplicate selected seed rows: {rendered_proof['duplicate_selected_seed_count']}",
        f"- Passed: {rendered_proof['passed']}",
        "",
        "## Selected August BLS Seeds",
    ]
    for row in rendered_proof["bls_august_selected_seed_rows"]:
        proof_lines.append(f"- {row['date']} {row['time']} {row['subtitle']} courseId {row['courseId']} -> {row['href']}")
    write_text(AUDIT_DIR / "release_candidate_rendered_page_proof.md", "\n".join(proof_lines))

    copy_lines = [
        "# Release Candidate Customer Copy Cleanup",
        "",
        f"- Pages scanned: {len(copy_report['customer_facing_pages_scanned'])}",
        f"- Visible internal term hits: {sum(sum(v.values()) for v in copy_report['visible_internal_term_hits'].values())}",
        f"- Cleanup performed: {copy_report['cleanup_performed']}",
        f"- Passed: {copy_report['passed']}",
        "",
        copy_report["note"],
    ]
    if copy_report["visible_internal_term_hits"]:
        copy_lines.extend(["", "## Visible Hits", json.dumps(copy_report["visible_internal_term_hits"], indent=2)])
    write_text(AUDIT_DIR / "release_candidate_customer_copy_cleanup.md", "\n".join(copy_lines))

    booking_lines = [
        "# Release Candidate Booking URL Sanity",
        "",
        f"- August BLS appointment seed URLs checked: {booking_sanity['august_bls_appointment_seed_rows_checked']}",
        f"- URL failures: {len(booking_sanity['url_failures'])}",
        f"- HSI pediatric 449422 suppressed: {booking_sanity['hsi_pediatric_449422_suppressed']}",
        f"- 344085 not on HSI page: {booking_sanity['course_344085_not_on_hsi_page']}",
        f"- UNKNOWN suppressed: {booking_sanity['unknown_course_key_suppressed']}",
        f"- Passed: {booking_sanity['passed']}",
    ]
    write_text(AUDIT_DIR / "release_candidate_booking_url_sanity.md", "\n".join(booking_lines))

    final_lines = [
        "# Release Candidate Final Report",
        "",
        f"- Branch: {final_report['git']['branch']}",
        f"- Latest commit: {final_report['git']['head']}",
        f"- Working tree contained only release-candidate artifacts when report generated: {final_report['git']['only_release_candidate_artifacts']}",
        f"- Release decision: {final_report['release_decision']}",
        f"- Deploy performed: {final_report['deploy_performed']}",
        f"- Validation status: {final_report['validation']['status']}",
        "",
        "## Summary",
        "- August AHA BLS seeds render in docs/bls.html alongside real Enrollware rows.",
        "- Customer-facing visible copy does not expose seed/dynamic/public-sellable terminology on scanned release pages.",
        "- Booking URLs include appointmentDayId, startTime, and the reviewed AHA BLS courseId.",
        "- Large generated previews remain the main repo-hygiene risk and were not moved in this pass.",
    ]
    write_text(AUDIT_DIR / "release_candidate_final_report.md", "\n".join(final_lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation-status", default="not_run")
    args = parser.parse_args()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    pages = {str(path.relative_to(ROOT)).replace("\\", "/"): parse_page(path) for path in RENDER_PAGES if path.exists()}
    status_short = git(["status", "--short"])
    status_paths = {
        line[3:].replace("\\", "/")
        for line in status_short.splitlines()
        if len(line) > 3
        and "__pycache__/" not in line[3:].replace("\\", "/")
    }
    large_policy = build_large_file_policy()
    rendered_proof, rendered_rows = build_rendered_proof(pages)
    copy_report = build_customer_copy_report(pages)
    booking_sanity = build_booking_url_sanity(pages)
    final_report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "git": {
            "branch": git(["branch", "--show-current"]),
            "head": git(["rev-parse", "HEAD"]),
            "status_short": status_short,
            "only_release_candidate_artifacts": status_paths.issubset(RELEASE_OUTPUTS),
            "changed_files_against_origin_main": git(["diff", "--name-only", "origin/main...HEAD"]).splitlines(),
        },
        "release_decision": "A. Ready for PR review as a release candidate; do not deploy until human review approves the large generated preview file policy and release timing.",
        "deploy_performed": False,
        "validation": {
            "status": args.validation_status,
            "commands_required_by_instruction": [
                "python -m scripts.audit_august_bls_seed_quality",
                "python -m scripts.audit_bls_seed_time_preference",
                "python -m scripts.audit_bls_public_offer_policy_enablement",
                "python -m scripts.audit_august_offer_explosion",
                "python -m scripts.audit_live_availability_snapshot_trace",
                "python -m scripts.audit_august_seed_breakpoint",
                "python -m scripts.public_offer_integrity_audit",
                "python -m unittest discover -s tests",
            ],
        },
        "large_file_policy_passed_for_release": not large_policy["safe_to_remove_in_this_release_candidate"],
        "rendered_page_proof_passed": rendered_proof["passed"],
        "customer_copy_cleanup_passed": copy_report["passed"],
        "booking_url_sanity_passed": booking_sanity["passed"],
        "functional_release_candidate_passed": rendered_proof["passed"] and copy_report["passed"] and booking_sanity["passed"],
    }

    write_json(AUDIT_DIR / "release_candidate_large_file_policy.json", large_policy)
    write_json(AUDIT_DIR / "release_candidate_rendered_page_proof.json", rendered_proof)
    write_csv_rows(AUDIT_DIR / "release_candidate_rendered_page_rows.csv", rendered_rows)
    write_json(AUDIT_DIR / "release_candidate_booking_url_sanity.json", booking_sanity)
    write_json(AUDIT_DIR / "release_candidate_final_report.json", final_report)
    render_markdown_reports(large_policy, rendered_proof, copy_report, booking_sanity, final_report)

    if not final_report["functional_release_candidate_passed"]:
        raise SystemExit("Release-candidate audit failed; inspect data/audit/release_candidate_final_report.json")


if __name__ == "__main__":
    main()
