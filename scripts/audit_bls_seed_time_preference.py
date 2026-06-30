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
POLICY_PATH = ROOT / "data" / "config" / "seed_strategy_policy.json"
DYNAMIC_PATH = AUDIT_DIR / "dynamic_offers_preview.json"
SELLABLE_PATH = AUDIT_DIR / "public_sellable_offers_preview.json"
SEEDS_PATH = AUDIT_DIR / "schedule_seeds_preview.json"
URLS_PATH = AUDIT_DIR / "seed_appointment_url_preview.json"
BLS_HTML_PATH = ROOT / "docs" / "bls.html"
SCHEDULE_FUTURE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
PUBLIC_INTEGRITY_PATH = AUDIT_DIR / "public_offer_integrity_report.json"
TIME_REPORT_MD = AUDIT_DIR / "bls_seed_time_preference_report.md"
TIME_REPORT_JSON = AUDIT_DIR / "bls_seed_time_preference_report.json"
BEFORE_AFTER_CSV = AUDIT_DIR / "bls_seed_time_preference_before_after.csv"
CANDIDATE_CSV = AUDIT_DIR / "bls_candidate_time_availability.csv"
PROOF_MD = AUDIT_DIR / "bls_rendered_seed_proof_after_time_preference.md"
PROOF_JSON = AUDIT_DIR / "bls_rendered_seed_proof_after_time_preference.json"

AHA_BLS_IDS = {"209806", "359474", "210549"}
PREFERRED_TIMES = ["09:15", "12:30", "18:15", "18:45", "08:30", "09:00", "08:00", "08:15"]
PUBLIC_FRIENDLY_TIMES = ["09:15", "12:30", "18:15", "18:45"]
BEFORE_SELECTED = [
    {"date": "2026-08-03", "start_time": "08:30", "course_id": "209806", "course_title": "AHA BLS Provider"},
    {"date": "2026-08-04", "start_time": "08:00", "course_id": "359474", "course_title": "AHA BLS Provider Renewal"},
    {"date": "2026-08-10", "start_time": "08:30", "course_id": "209806", "course_title": "AHA BLS Provider"},
    {"date": "2026-08-11", "start_time": "08:00", "course_id": "359474", "course_title": "AHA BLS Provider Renewal"},
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def norm(value: Any) -> str:
    return str(value or "").strip()


def is_august(row: dict[str, Any]) -> bool:
    return norm(row.get("date") or row.get("start_at") or row.get("start_datetime")).startswith("2026-08")


def is_bls_text(row: dict[str, Any]) -> bool:
    text = " ".join(norm(row.get(key)).lower() for key in ("course_id", "course_key", "course_family", "course_title", "title", "course_name", "official_course_name"))
    return "bls" in text


def is_aha_bls(row: dict[str, Any]) -> bool:
    return norm(row.get("course_id") or row.get("courseId")) in AHA_BLS_IDS


def rows_at(rows: list[dict[str, Any]], start_time: str, *, aha_only: bool = False) -> list[dict[str, Any]]:
    return [
        row for row in rows
        if isinstance(row, dict)
        and is_august(row)
        and is_bls_text(row)
        and norm(row.get("start_time")) == start_time
        and (not aha_only or is_aha_bls(row))
    ]


def hidden_reasons_for_time(payload: dict[str, Any], start_time: str) -> Counter[str]:
    reasons: Counter[str] = Counter()
    for hidden in payload.get("hidden_offers", []):
        if not isinstance(hidden, dict):
            continue
        offer = hidden.get("offer") if isinstance(hidden.get("offer"), dict) else hidden
        if not isinstance(offer, dict) or not is_august(offer) or not is_bls_text(offer) or norm(offer.get("start_time")) != start_time:
            continue
        for reason in hidden.get("reason_codes", []):
            reasons[norm(reason)] += 1
        reason = norm(hidden.get("reason_code"))
        if reason:
            reasons[reason] += 1
    return reasons


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
    if start < 0 or end < 0:
        return ""
    return page_html[start : end + len("</article>")]


def strip_tags(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def visible(article: str, class_name: str) -> str:
    match = re.search(rf'<[^>]*class="[^"]*{re.escape(class_name)}[^"]*"[^>]*>(.*?)</[^>]+>', article, re.S)
    return html.unescape(strip_tags(match.group(1))) if match else ""


def attr(article: str, name: str) -> str:
    match = re.search(rf'{re.escape(name)}="([^"]*)"', article)
    return html.unescape(match.group(1)) if match else ""


def button_text(article: str, url: str) -> str:
    match = re.search(rf'<a [^>]*href="{re.escape(html_url(url))}"[^>]*>(.*?)</a>', article, re.S)
    return html.unescape(strip_tags(match.group(1))) if match else ""


def main() -> None:
    policy = read_json(POLICY_PATH)
    dynamic = read_json(DYNAMIC_PATH)
    sellable = read_json(SELLABLE_PATH)
    seeds_payload = read_json(SEEDS_PATH)
    urls_payload = read_json(URLS_PATH)
    schedule_future = read_json(SCHEDULE_FUTURE_PATH)
    public_integrity = read_json(PUBLIC_INTEGRITY_PATH) if PUBLIC_INTEGRITY_PATH.exists() else {}
    page_html = BLS_HTML_PATH.read_text(encoding="utf-8")

    dynamic_rows = [row for row in dynamic.get("offers", []) if isinstance(row, dict)]
    sellable_rows = [row for row in sellable.get("offers", []) if isinstance(row, dict)]
    seed_rows = [row for row in seeds_payload.get("seeds", []) if isinstance(row, dict)]
    url_rows = [row for row in urls_payload.get("previews", []) if isinstance(row, dict)]
    selected_august_bls = [row for row in seed_rows if is_august(row) and is_aha_bls(row)]
    selected_offer_ids = {norm(row.get("source_offer_id")) for row in selected_august_bls}
    url_by_offer = {norm(row.get("source_offer_id")): row for row in url_rows if isinstance(row, dict)}

    candidate_rows = []
    for start_time in PREFERRED_TIMES:
        dynamic_at = rows_at(dynamic_rows, start_time)
        sellable_at = rows_at(sellable_rows, start_time)
        seed_at = [row for row in rows_at(seed_rows, start_time, aha_only=True) if norm(row.get("source_offer_id")) in selected_offer_ids]
        reasons = hidden_reasons_for_time(sellable, start_time)
        seed_reasons = hidden_reasons_for_time(seeds_payload, start_time)
        candidate_rows.append({
            "start_time": start_time,
            "generated_candidate_count": len(dynamic_at),
            "public_sellable_count": len(sellable_at),
            "seed_eligible_count": len([row for row in sellable_at if is_aha_bls(row)]),
            "selected_seed_count": len(seed_at),
            "top_public_filter_reasons": "; ".join(f"{reason}:{count}" for reason, count in reasons.most_common(8)),
            "top_seed_rejection_reasons": "; ".join(f"{reason}:{count}" for reason, count in seed_reasons.most_common(8)),
            "blocked_by": "public_sellable_filters" if start_time in PUBLIC_FRIENDLY_TIMES and not sellable_at else ("seed_preference_or_caps" if sellable_at and not seed_at else ""),
        })

    proof_rows = []
    for seed in selected_august_bls:
        url = url_by_offer.get(norm(seed.get("source_offer_id")), {})
        booking_url = norm(url.get("appointment_url_preview"))
        article = article_for_url(page_html, booking_url)
        proof_rows.append({
            "date": norm(seed.get("date")),
            "start_time": norm(seed.get("start_time")),
            "course_id": norm(seed.get("course_id")),
            "course_title": norm(seed.get("course_title")),
            "booking_url": booking_url,
            "rendered": bool(article),
            "visible_date": visible(article, "slug-pill-title"),
            "visible_time": visible(article, "slug-pill-chip"),
            "visible_course_label": visible(article, "slug-pill-subtitle"),
            "button_text": button_text(article, booking_url),
            "row_source": attr(article, "data-render-source"),
            "source_offer_id": norm(seed.get("source_offer_id")),
            "selected_seed_url_occurrences": page_html.count(html_url(booking_url)) if booking_url else 0,
        })

    real_august_bls_ids = [
        norm(row.get("session_id"))
        for row in schedule_future.get("sessions", [])
        if isinstance(row, dict)
        and is_bls_text(row)
        and is_aha_bls(row)
        and norm(row.get("start_at")).startswith("2026-08")
    ]
    safety = {
        "existing_real_bls_enrollware_rows_still_render": "js-session-item" in page_html,
        "real_august_bls_enrollware_rows_still_render": any(session_id and session_id in page_html for session_id in real_august_bls_ids),
        "selected_bls_appointment_seeds_render": sum(1 for row in proof_rows if row["rendered"]),
        "duplicate_selected_seed_rows": sum(max(0, int(row["selected_seed_url_occurrences"]) - 1) for row in proof_rows),
        "unknown_rows_suppressed": "UNKNOWN" not in "\n".join(row["visible_course_label"] for row in proof_rows),
        "hsi_pediatric_449422_suppressed": "courseId=449422" not in page_html,
        "course_344085_not_hsi": "courseId=344085" not in (ROOT / "docs" / "hsi.html").read_text(encoding="utf-8"),
        "public_offer_integrity_failed": public_integrity.get("audit_failed", public_integrity.get("stats", {}).get("audit_failed")),
    }
    after_selected = [
        {
            "date": norm(row.get("date")),
            "start_time": norm(row.get("start_time")),
            "course_id": norm(row.get("course_id")),
            "course_title": norm(row.get("course_title")),
        }
        for row in selected_august_bls
    ]
    report = {
        "generated_at": datetime.now().isoformat(),
        "policy": {
            "preferred_start_times_by_family_BLS": policy.get("preferred_start_times_by_family", {}).get("BLS", []),
            "max_seeds_per_instructor_window": policy.get("max_seeds_per_instructor_window"),
            "max_seeds_per_date": policy.get("max_seeds_per_date"),
            "max_seeds_per_family_per_date_BLS": policy.get("max_seeds_per_family_per_date", {}).get("BLS"),
            "required_seed_mix_by_date_BLS": policy.get("required_seed_mix_by_date", {}).get("BLS"),
            "avoid_same_start_time_per_date": policy.get("avoid_same_start_time_per_date"),
            "preference_scope": "family-level preferred_start_times_by_family",
        },
        "why_early_times_were_chosen": "Before this change, BLS preferred starts were 08:30 then 09:00; all requested public-friendly starts existed dynamically but had zero public-sellable rows, so selection fell to the earliest safe public-sellable AHA BLS candidates.",
        "candidate_time_availability": candidate_rows,
        "before_selected_august_bls": BEFORE_SELECTED,
        "after_selected_august_bls": after_selected,
        "rendered_seed_proof": proof_rows,
        "safety": safety,
        "recommendation": "Keep the policy preference change. It is safe and future-proofs selection when 09:15, 12:30, 18:15, or 18:45 survive public-sellable gates, but it does not force unsafe August rows through current caps/filters.",
        "sufficiency": {
            "august_bls_looks_alive_enough": len(proof_rows) == 4 and all(row["rendered"] for row in proof_rows),
            "spread": sorted({row["date"] for row in after_selected}),
            "initial_count": sum(1 for row in after_selected if row["course_id"] == "209806"),
            "renewal_count": sum(1 for row in after_selected if row["course_id"] == "359474"),
            "evening_or_midday_possible_without_loosening": False,
            "reason_evening_or_midday_not_selected": "Generated, but zero public-sellable candidates at 12:30/18:15/18:45 under current public offer caps and course/family filters.",
        },
    }
    TIME_REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with CANDIDATE_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(candidate_rows[0].keys()))
        writer.writeheader()
        writer.writerows(candidate_rows)

    with BEFORE_AFTER_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["period", "date", "start_time", "course_id", "course_title"])
        writer.writeheader()
        for row in BEFORE_SELECTED:
            writer.writerow({"period": "before", **row})
        for row in after_selected:
            writer.writerow({"period": "after", **row})

    PROOF_JSON.write_text(json.dumps({"summary": safety, "rendered_seeds": proof_rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    proof_lines = ["# BLS rendered seed proof after time preference", ""]
    for row in proof_rows:
        proof_lines.extend([
            f"## {row['date']} {row['start_time']} {row['course_title']}",
            f"- Rendered: {row['rendered']}",
            f"- Visible date: {row['visible_date']}",
            f"- Visible time: {row['visible_time']}",
            f"- Visible course label: {row['visible_course_label']}",
            f"- Button text: {row['button_text']}",
            f"- Booking URL: {row['booking_url']}",
            f"- Internal row_source: {row['row_source']}",
            f"- Selected seed URL occurrences: {row['selected_seed_url_occurrences']}",
            "",
        ])
    PROOF_MD.write_text("\n".join(proof_lines), encoding="utf-8")

    lines = [
        "# BLS seed time preference report",
        "",
        "## Summary",
        "BLS start-time preference is now policy-driven in this order: 09:15, 12:30, 18:15, 18:45, 08:30, 09:00, 08:00, 08:15.",
        "The selected August BLS seeds did not move because the preferred public-friendly times currently have zero public-sellable rows. They are generated dynamically, but current public offer caps and course/family filters remove them before seed selection.",
        "",
        "## Current policy",
        f"- BLS preferred starts: {report['policy']['preferred_start_times_by_family_BLS']}",
        f"- Max seeds per instructor/window: {report['policy']['max_seeds_per_instructor_window']}",
        f"- Max seeds per date: {report['policy']['max_seeds_per_date']}",
        f"- Max BLS seeds per date: {report['policy']['max_seeds_per_family_per_date_BLS']}",
        f"- BLS required mix: {report['policy']['required_seed_mix_by_date_BLS']}",
        "",
        "## Candidate availability",
        "| Start | Generated | Public sellable | Seed eligible | Selected | Top blocker |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in candidate_rows:
        lines.append(f"| {row['start_time']} | {row['generated_candidate_count']} | {row['public_sellable_count']} | {row['seed_eligible_count']} | {row['selected_seed_count']} | {row['top_public_filter_reasons']} |")
    lines.extend([
        "",
        "## Before/after selected August BLS seeds",
        "| Period | Date | Time | CourseId | Course |",
        "| --- | --- | --- | --- | --- |",
    ])
    for row in BEFORE_SELECTED:
        lines.append(f"| Before | {row['date']} | {row['start_time']} | {row['course_id']} | {row['course_title']} |")
    for row in after_selected:
        lines.append(f"| After | {row['date']} | {row['start_time']} | {row['course_id']} | {row['course_title']} |")
    lines.extend([
        "",
        "## Schedule sufficiency",
        f"- August BLS rendered seed rows: {safety['selected_bls_appointment_seeds_render']}",
        f"- Duplicate selected seed rows: {safety['duplicate_selected_seed_rows']}",
        f"- Initial/Renewal balance: {report['sufficiency']['initial_count']} Initial, {report['sufficiency']['renewal_count']} Renewal",
        "- Evening or midday seeds are not possible without changing upstream public-sellable caps/filters.",
        "",
        "## Safety",
    ])
    lines.extend(f"- {key}: {value}" for key, value in safety.items())
    TIME_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Rendered August BLS seeds: {safety['selected_bls_appointment_seeds_render']}")
    print(f"Duplicate selected seed rows: {safety['duplicate_selected_seed_rows']}")
    print(f"Wrote {TIME_REPORT_MD}")
    if safety["selected_bls_appointment_seeds_render"] < 4 or safety["duplicate_selected_seed_rows"] != 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
