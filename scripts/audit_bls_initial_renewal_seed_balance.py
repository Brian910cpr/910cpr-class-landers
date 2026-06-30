from __future__ import annotations

import csv
import html
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
SEEDS_PATH = AUDIT_DIR / "schedule_seeds_preview.json"
URLS_PATH = AUDIT_DIR / "seed_appointment_url_preview.json"
SELLABLE_PATH = AUDIT_DIR / "public_sellable_offers_preview.json"
BLS_HTML_PATH = ROOT / "docs" / "bls.html"
SCHEDULE_FUTURE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
REPORT_MD = AUDIT_DIR / "bls_initial_renewal_seed_balance_report.md"
REPORT_JSON = AUDIT_DIR / "bls_initial_renewal_seed_balance_report.json"
CANDIDATE_CSV = AUDIT_DIR / "bls_initial_renewal_candidate_trace.csv"
BEFORE_AFTER_CSV = AUDIT_DIR / "bls_seed_balance_before_after.csv"
PROOF_MD = AUDIT_DIR / "bls_rendered_seed_proof_after_balance.md"
PROOF_JSON = AUDIT_DIR / "bls_rendered_seed_proof_after_balance.json"

COURSE_LABELS = {
    "209806": "Initial",
    "359474": "Renewal",
    "210549": "HeartCode",
}
BEFORE = [
    {"date": "2026-08-03", "start_time": "09:15", "course_id": "209806", "variant": "Initial"},
    {"date": "2026-08-04", "start_time": "09:15", "course_id": "209806", "variant": "Initial"},
    {"date": "2026-08-05", "start_time": "09:15", "course_id": "209806", "variant": "Initial"},
    {"date": "2026-08-10", "start_time": "09:15", "course_id": "209806", "variant": "Initial"},
    {"date": "2026-08-11", "start_time": "09:15", "course_id": "209806", "variant": "Initial"},
    {"date": "2026-08-12", "start_time": "09:15", "course_id": "209806", "variant": "Initial"},
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def norm(value: Any) -> str:
    return str(value or "").strip()


def is_august_aha_bls(row: dict[str, Any]) -> bool:
    return norm(row.get("date") or row.get("start_at")).startswith("2026-08") and norm(row.get("course_id") or row.get("courseId")) in COURSE_LABELS


def html_url(url: str) -> str:
    return html.escape(url, quote=True)


def article_for_url(page_html: str, url: str) -> str:
    pos = page_html.find(html_url(url))
    if pos < 0:
        pos = page_html.find(url)
    if pos < 0:
        return ""
    start = page_html.rfind("<article", 0, pos)
    end = page_html.find("</article>", pos)
    return page_html[start : end + len("</article>")] if start >= 0 and end >= 0 else ""


def strip_tags(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def visible(article: str, class_name: str) -> str:
    match = re.search(rf'<[^>]*class="[^"]*{re.escape(class_name)}[^"]*"[^>]*>(.*?)</[^>]+>', article, re.S)
    return html.unescape(strip_tags(match.group(1))) if match else ""


def attr(article: str, name: str) -> str:
    match = re.search(rf'{re.escape(name)}="([^"]*)"', article)
    return html.unescape(match.group(1)) if match else ""


def main() -> None:
    seeds = read_json(SEEDS_PATH)
    urls = read_json(URLS_PATH)
    sellable = read_json(SELLABLE_PATH)
    schedule_future = read_json(SCHEDULE_FUTURE_PATH)
    page_html = BLS_HTML_PATH.read_text(encoding="utf-8")
    seed_rows = [row for row in seeds.get("seeds", []) if isinstance(row, dict)]
    hidden_rows = [row for row in seeds.get("hidden_offers", []) if isinstance(row, dict)]
    selected = [row for row in seed_rows if is_august_aha_bls(row)]
    url_by_offer = {norm(row.get("source_offer_id")): row for row in urls.get("previews", []) if isinstance(row, dict)}

    candidate_rows = []
    selected_ids = {norm(row.get("source_offer_id")) for row in selected}
    hidden_by_id = {norm(row.get("source_offer_id")): row for row in hidden_rows}
    for offer in sellable.get("offers", []):
        if not isinstance(offer, dict) or not is_august_aha_bls(offer):
            continue
        offer_id = norm(offer.get("offer_id"))
        hidden = hidden_by_id.get(offer_id, {})
        candidate_rows.append({
            "offer_id": offer_id,
            "date": norm(offer.get("date")),
            "start_time": norm(offer.get("start_time")),
            "course_id": norm(offer.get("course_id")),
            "variant": COURSE_LABELS.get(norm(offer.get("course_id")), "UNKNOWN"),
            "course_title": norm(offer.get("course_title")),
            "selected": offer_id in selected_ids,
            "rejection_reason": norm(hidden.get("reason_code")) if offer_id not in selected_ids else "",
            "rejection_message": norm(hidden.get("message")) if offer_id not in selected_ids else "",
        })

    proof_rows = []
    for seed in selected:
        preview = url_by_offer.get(norm(seed.get("source_offer_id")), {})
        url = norm(preview.get("appointment_url_preview"))
        article = article_for_url(page_html, url)
        proof_rows.append({
            "date": norm(seed.get("date")),
            "start_time": norm(seed.get("start_time")),
            "course_id": norm(seed.get("course_id")),
            "variant": COURSE_LABELS.get(norm(seed.get("course_id")), "UNKNOWN"),
            "course_title": norm(seed.get("course_title")),
            "booking_url": url,
            "rendered": bool(article),
            "visible_date": visible(article, "slug-pill-title"),
            "visible_time": visible(article, "slug-pill-chip"),
            "visible_course_label": visible(article, "slug-pill-subtitle"),
            "row_source": attr(article, "data-render-source"),
            "url_occurrences": page_html.count(html_url(url)) if url else 0,
        })

    real_august = [
        {
            "session_id": norm(row.get("session_id")),
            "course_id": norm(row.get("course_id")),
            "variant": COURSE_LABELS.get(norm(row.get("course_id")), "UNKNOWN"),
            "start_at": norm(row.get("start_at")),
        }
        for row in schedule_future.get("sessions", [])
        if isinstance(row, dict) and norm(row.get("start_at")).startswith("2026-08") and norm(row.get("course_id")) in COURSE_LABELS
    ]
    before_counts = Counter(row["variant"] for row in BEFORE)
    after_counts = Counter(COURSE_LABELS.get(norm(row.get("course_id")), "UNKNOWN") for row in selected)
    duplicate_count = sum(max(0, row["url_occurrences"] - 1) for row in proof_rows)
    report = {
        "generated_at": datetime.now().isoformat(),
        "rule": {
            "recommendation": "C. Keep one BLS seed per date, but alternate course type by seed date.",
            "implemented": True,
            "policy_key": "bls_seed_variant_balance",
            "mode": "alternate_initial_renewal_by_bls_date",
        },
        "before": {"selected_count": len(BEFORE), "counts": dict(before_counts), "rows": BEFORE},
        "after": {"selected_count": len(selected), "counts": dict(after_counts), "rows": proof_rows},
        "candidate_trace_counts": dict(Counter(row["rejection_reason"] or "selected" for row in candidate_rows)),
        "rendered_rows": sum(1 for row in proof_rows if row["rendered"]),
        "duplicate_selected_seed_rows": duplicate_count,
        "real_august_bls_enrollware_rows": real_august,
        "plain_answer": "Initial won before because daily BLS family mix sorted by preferred start, then course_title_priority_terms; 'BLS Provider' ranked Initial before Renewal. Renewal rows were present as seed candidates and rejected mostly as family_mix_target_already_met.",
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    PROOF_JSON.write_text(json.dumps({"summary": {"rendered_rows": report["rendered_rows"], "duplicate_selected_seed_rows": duplicate_count}, "rows": proof_rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with CANDIDATE_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(candidate_rows[0].keys()))
        writer.writeheader()
        writer.writerows(candidate_rows)
    with BEFORE_AFTER_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["period", "date", "start_time", "course_id", "variant", "course_title"])
        writer.writeheader()
        for row in BEFORE:
            writer.writerow({"period": "before", "course_title": "", **row})
        for row in proof_rows:
            writer.writerow({key: row.get(key, "") for key in ["date", "start_time", "course_id", "variant", "course_title"]} | {"period": "after"})

    lines = [
        "# BLS Initial/Renewal seed balance report",
        "",
        "## Plain answer",
        report["plain_answer"],
        "",
        "## Rule",
        "Implemented recommendation C: keep one BLS seed per date, but alternate Initial and Renewal across eligible BLS seed dates.",
        "",
        f"- Before: {len(BEFORE)} selected, {dict(before_counts)}",
        f"- After: {len(selected)} selected, {dict(after_counts)}",
        f"- Rendered rows in docs/bls.html: {report['rendered_rows']}",
        f"- Duplicate selected seed rows: {duplicate_count}",
        "",
        "## After selected rows",
        "| Date | Time | CourseId | Variant | Course | Rendered |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in proof_rows:
        lines.append(f"| {row['date']} | {row['start_time']} | {row['course_id']} | {row['variant']} | {row['course_title']} | {row['rendered']} |")
    lines.extend([
        "",
        "## Existing real August BLS Enrollware rows",
        "| Session | Start | CourseId | Variant |",
        "| --- | --- | --- | --- |",
    ])
    for row in real_august:
        lines.append(f"| {row['session_id']} | {row['start_at']} | {row['course_id']} | {row['variant']} |")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    proof_lines = ["# BLS rendered seed proof after balance", ""]
    for row in proof_rows:
        proof_lines.extend([
            f"## {row['date']} {row['start_time']} {row['variant']}",
            f"- Rendered: {row['rendered']}",
            f"- Visible date: {row['visible_date']}",
            f"- Visible time: {row['visible_time']}",
            f"- Visible course label: {row['visible_course_label']}",
            f"- Booking URL: {row['booking_url']}",
            f"- Internal row_source: {row['row_source']}",
            f"- URL occurrences: {row['url_occurrences']}",
            "",
        ])
    PROOF_MD.write_text("\n".join(proof_lines), encoding="utf-8")
    print(f"Rendered BLS seeds after balance: {report['rendered_rows']}")
    print(f"Initial/Renewal/HeartCode: {dict(after_counts)}")
    print(f"Duplicate selected seed rows: {duplicate_count}")
    if report["rendered_rows"] != len(selected) or duplicate_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
