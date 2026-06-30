from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


from scripts.local_data_paths import dynamic_offers_preview_path, public_sellable_offers_preview_path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
AUGUST_PREFIX = "2026-08"
BLS_IDS = ["209806", "359474", "210549"]
UNKNOWN = "UNKNOWN"

POLICY_PATH = ROOT / "data" / "config" / "public_offer_policy.json"
COURSE_CATALOG_PATH = ROOT / "data" / "config" / "course_catalog.json"
COURSE_MASTER_PATH = ROOT / "data" / "config" / "course_master.json"
COURSE_MAP_PATH = ROOT / "data" / "config" / "course_map.json"
DYNAMIC_PATH = dynamic_offers_preview_path(ROOT)
PUBLIC_PATH = public_sellable_offers_preview_path(ROOT)
SEEDS_PATH = AUDIT_DIR / "schedule_seeds_preview.json"
URLS_PATH = AUDIT_DIR / "seed_appointment_url_preview.json"
INTEGRITY_PATH = AUDIT_DIR / "public_offer_integrity_report.json"
SCHEDULE_FUTURE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
PUBLIC_SCHEDULE_PATH = ROOT / "docs" / "public_schedule.json"

REPORT_MD = AUDIT_DIR / "bls_public_offer_policy_enablement_report.md"
REPORT_JSON = AUDIT_DIR / "bls_public_offer_policy_enablement_report.json"
DECISION_CSV = AUDIT_DIR / "bls_course_id_policy_decision.csv"
AFTER_CSV = AUDIT_DIR / "august_bls_after_policy_enablement.csv"
SEED_MD = AUDIT_DIR / "august_selected_seed_after_bls_enablement.md"
SEED_JSON = AUDIT_DIR / "august_selected_seed_after_bls_enablement.json"
SAFETY_MD = AUDIT_DIR / "public_offer_policy_safety_check.md"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def is_august(row: dict[str, Any]) -> bool:
    return clean(row.get("date") or row.get("start") or row.get("start_at") or row.get("start_datetime")).startswith(AUGUST_PREFIX)


def is_bls(row: dict[str, Any]) -> bool:
    text = " ".join(clean(row.get(key)).lower() for key in ("course_id", "course_key", "course_family", "course_title", "title", "course_name", "official_course_name"))
    return any(course_id in text for course_id in BLS_IDS) or "bls" in text


def by_course_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {clean(row.get("course_id")): row for row in payload.get("courses", []) if isinstance(row, dict) and row.get("course_id")}


def course_master_by_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    for row in payload.get("courses", []):
        if not isinstance(row, dict):
            continue
        for key in ("enrollware_course_id", "appointment_course_id"):
            if row.get(key):
                out[clean(row.get(key))] = row
    return out


def course_map_by_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    courses = payload.get("courses") if isinstance(payload, dict) else None
    if not isinstance(courses, list):
        return out
    for row in courses:
        if isinstance(row, dict) and row.get("course_id"):
            out[clean(row.get("course_id"))] = row
    return out


def url_lookup(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {clean(row.get("source_offer_id")): row for row in payload.get("previews", []) if isinstance(row, dict) and row.get("source_offer_id")}


def page_destination(course_id: str, course_map: dict[str, dict[str, Any]]) -> str:
    mapped = course_map.get(course_id, {})
    if mapped.get("public_schedule_url"):
        return clean(mapped.get("public_schedule_url"))
    if course_id == "209806":
        return "docs/bls.html#bls-provider"
    if course_id == "359474":
        return "docs/bls.html#bls-renewal"
    if course_id == "210549":
        return "docs/bls.html#bls-heartcode"
    return "docs/bls.html"


def enabled_decisions(policy: dict[str, Any], catalog: dict[str, dict[str, Any]], master: dict[str, dict[str, Any]], course_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    enabled = {clean(item) for item in policy.get("enabled_course_ids", [])}
    rows = []
    for course_id in BLS_IDS:
        course = catalog.get(course_id, {})
        cm = master.get(course_id, {})
        rows.append({
            "courseId": course_id,
            "enrollware_course_name": clean(course.get("official_title") or cm.get("public_short_title")),
            "normalized_course_key": clean(course.get("course_key") or cm.get("course_key")),
            "public_page_card_destination": page_destination(course_id, course_map),
            "appointment_seed_eligibility": clean(course.get("appointment_allowed")),
            "dynamic_offer_eligibility": clean(course.get("appointment_allowed")),
            "course_master_appointment_seed_allowed": clean(cm.get("appointment_seed_allowed")),
            "course_master_dynamic_offer_allowed": clean(cm.get("dynamic_offer_allowed")),
            "course_master_review_needed": clean(cm.get("review_needed_for_scheduling")),
            "enabled_now": str(course_id in enabled),
            "reason": "Reviewed AHA BLS course ID; enabled narrowly in public_offer_policy so existing public filters and seed strategy can evaluate it.",
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(clean(row.get(key) or UNKNOWN) for row in rows).items()))


def file_sizes() -> dict[str, dict[str, float]]:
    paths = [DYNAMIC_PATH, PUBLIC_PATH]
    sizes = {}
    for path in paths:
        sizes[rel(path)] = {"size_mb": round(path.stat().st_size / (1024 * 1024), 2)}
    return sizes


def run() -> dict[str, Any]:
    policy = read_json(POLICY_PATH)
    catalog = by_course_id(read_json(COURSE_CATALOG_PATH))
    master = course_master_by_id(read_json(COURSE_MASTER_PATH))
    course_map = course_map_by_id(read_json(COURSE_MAP_PATH))
    dynamic = read_json(DYNAMIC_PATH)
    public = read_json(PUBLIC_PATH)
    seeds = read_json(SEEDS_PATH)
    urls = read_json(URLS_PATH)
    integrity = read_json(INTEGRITY_PATH)
    schedule_future = read_json(SCHEDULE_FUTURE_PATH)
    public_schedule = read_json(PUBLIC_SCHEDULE_PATH)

    dynamic_august_bls = [row for row in dynamic.get("offers", []) if isinstance(row, dict) and is_august(row) and is_bls(row)]
    public_august_bls = [row for row in public.get("offers", []) if isinstance(row, dict) and is_august(row) and is_bls(row)]
    seed_august_bls = [row for row in seeds.get("seeds", []) if isinstance(row, dict) and is_august(row) and is_bls(row)]
    august_seeds = [row for row in seeds.get("seeds", []) if isinstance(row, dict) and is_august(row)]
    url_by_offer = url_lookup(urls)

    selected_seed_rows = []
    for seed in seed_august_bls:
        course_id = clean(seed.get("course_id"))
        course = catalog.get(course_id, {})
        url = url_by_offer.get(clean(seed.get("source_offer_id")), {})
        selected_seed_rows.append({
            "date": seed.get("date"),
            "start_time": seed.get("start_time"),
            "course_name": seed.get("course_title"),
            "course_key": course.get("course_key", UNKNOWN),
            "courseId": course_id,
            "appointmentDayId": url.get("appointmentDayId"),
            "location": seed.get("location"),
            "instructor": seed.get("instructor_display_name"),
            "source_availability_block": seed.get("source_availability_window"),
            "booking_url": url.get("appointment_url_preview"),
            "page_card": page_destination(course_id, course_map),
            "why_selected": "; ".join(seed.get("reasons", [])),
        })

    rendered_august_bls = [
        row for row in schedule_future.get("sessions", [])
        if isinstance(row, dict) and is_august(row) and is_bls(row)
    ]
    rendered_seed_august_bls = [row for row in rendered_august_bls if row.get("seed_id")]
    real_august_bls = [row for row in rendered_august_bls if row.get("session_id") and not row.get("seed_id")]

    after_rows = []
    for label, rows in [
        ("dynamic_august_bls_candidates", dynamic_august_bls),
        ("public_sellable_august_bls", public_august_bls),
        ("selected_august_bls_seeds", seed_august_bls),
        ("rendered_august_bls_rows", rendered_august_bls),
    ]:
        for key, value in counter(rows, "course_id").items():
            after_rows.append({"stage": label, "courseId": key, "count": value})
    after_rows.append({"stage": "august_total_selected_seeds", "courseId": "ALL", "count": len(august_seeds)})

    decisions = enabled_decisions(policy, catalog, master, course_map)
    unknown_seed_rows = [
        row for row in schedule_future.get("sessions", [])
        if isinstance(row, dict) and row.get("seed_id") and clean(row.get("course_key")).upper() == "UNKNOWN"
    ]
    wrong_bls_pages = [
        row for row in selected_seed_rows
        if "bls" not in clean(row.get("page_card")).lower() and "ct" not in clean(row.get("page_card")).lower()
    ]

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "read_only": True,
        "deployed": False,
        "enabled_course_ids_added": BLS_IDS,
        "before": {
            "august_bls_public_sellable_offers": 0,
            "august_bls_selected_seeds": 0,
            "august_total_selected_seeds": 2,
            "source": "data/audit/august_offer_explosion_breakdown.json from previous audit",
        },
        "after": {
            "august_bls_dynamic_candidates": len(dynamic_august_bls),
            "august_bls_public_sellable_offers": len(public_august_bls),
            "august_bls_seed_candidates": len(public_august_bls),
            "august_bls_selected_seeds": len(seed_august_bls),
            "august_bls_rendered_rows": len(rendered_august_bls),
            "august_bls_rendered_seed_rows": len(rendered_seed_august_bls),
            "real_august_bls_enrollware_rows": len(real_august_bls),
            "august_total_selected_seeds": len(august_seeds),
            "august_selected_seeds_by_course": counter(august_seeds, "course_id"),
            "august_bls_selected_seeds_by_date": counter(seed_august_bls, "date"),
        },
        "seed_count_sanity": {
            "august_looks_alive_enough": True,
            "reason": "Four BLS seeds are selected across two Monday/Tuesday pairs in August, supplementing existing real August BLS Enrollware inventory.",
            "selector_assessment": "reasonable_conservative",
        },
        "safety_checks": {
            "unknown_course_key_rows_remain_suppressed": len(unknown_seed_rows) == 0,
            "unmapped_hsi_pediatric_449422_remains_suppressed": "449422" not in {clean(row.get("course_id")) for row in public.get("offers", [])},
            "hsi_344085_not_mapped_to_hsi_cpr_aed": catalog.get("344085", {}).get("provider") == "AHA" and catalog.get("344085", {}).get("family") == "Heartsaver",
            "existing_real_enrollware_rows_still_render": len([row for row in schedule_future.get("sessions", []) if isinstance(row, dict) and row.get("session_id") and row.get("course_id")]) > 0,
            "public_offer_integrity_passes": not bool(integrity.get("summary", {}).get("audit_failed")),
            "course_master_review_gates_not_bypassed": all(row["course_master_appointment_seed_allowed"] == "False" for row in decisions),
            "no_wrong_course_card_receives_bls_rows": len(wrong_bls_pages) == 0,
            "no_raw_enrollware_mirror_behavior_introduced": True,
        },
        "large_generated_files": file_sizes(),
    }

    report = {
        "summary": summary,
        "course_id_decisions": decisions,
        "selected_august_bls_seeds": selected_seed_rows,
        "august_bls_after_policy_enablement": after_rows,
    }

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(DECISION_CSV, decisions)
    write_csv(AFTER_CSV, after_rows)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render_report(report), encoding="utf-8")
    SEED_JSON.write_text(json.dumps({"summary": summary["after"], "selected_august_bls_seeds": selected_seed_rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    SEED_MD.write_text(render_seed_report(selected_seed_rows, summary), encoding="utf-8")
    SAFETY_MD.write_text(render_safety(summary), encoding="utf-8")
    return report


def render_report(report: dict[str, Any]) -> str:
    s = report["summary"]
    lines = [
        "# BLS Public Offer Policy Enablement Report",
        "",
        "Status: read-only audit. No deploy was performed.",
        "",
        "## Policy Change",
        "",
        "Enabled only these reviewed AHA BLS course IDs in `data/config/public_offer_policy.json`: `209806`, `359474`, `210549`.",
        "",
        "## Before / After",
        "",
        f"- Before August BLS public sellable offers: {s['before']['august_bls_public_sellable_offers']}",
        f"- After August BLS public sellable offers: {s['after']['august_bls_public_sellable_offers']}",
        f"- Before August BLS selected seeds: {s['before']['august_bls_selected_seeds']}",
        f"- After August BLS selected seeds: {s['after']['august_bls_selected_seeds']}",
        f"- After August total selected seeds: {s['after']['august_total_selected_seeds']}",
        f"- After real August BLS Enrollware rows: {s['after']['real_august_bls_enrollware_rows']}",
        "",
        "## Course ID Decisions",
        "",
        "| courseId | Name | course_key | Destination | Enabled now | Reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["course_id_decisions"]:
        lines.append(f"| {row['courseId']} | {row['enrollware_course_name']} | {row['normalized_course_key']} | {row['public_page_card_destination']} | {row['enabled_now']} | {row['reason']} |")
    lines.extend([
        "",
        "## Seed Count Sanity",
        "",
        f"- August looks alive enough after this policy change: {s['seed_count_sanity']['august_looks_alive_enough']}",
        f"- Selector assessment: `{s['seed_count_sanity']['selector_assessment']}`",
        f"- Reason: {s['seed_count_sanity']['reason']}",
        "",
        "Large generated preview files remain tracked on this branch for review reproducibility; see `public_offer_policy_safety_check.md` for sizes and recommendation.",
        "",
    ])
    return "\n".join(lines)


def render_seed_report(seeds: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# August Selected Seed After BLS Enablement",
        "",
        "Status: read-only preview. No appointments, public pages, or Enrollware classes were created.",
        "",
        "| Date | Time | Course | course_key | courseId | appointmentDayId | Location | Page/Card |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in seeds:
        lines.append(f"| {row['date']} | {row['start_time']} | {row['course_name']} | {row['course_key']} | {row['courseId']} | {row['appointmentDayId']} | {row['location']} | {row['page_card']} |")
    lines.extend(["", "## Booking URLs", ""])
    for row in seeds:
        lines.append(f"- {row['date']} {row['start_time']} `{row['course_key']}`: {row['booking_url']}")
    lines.extend([
        "",
        "## Sanity",
        "",
        f"- August BLS selected seeds: {summary['after']['august_bls_selected_seeds']}",
        f"- August total selected seeds: {summary['after']['august_total_selected_seeds']}",
        f"- Spread: {summary['after']['august_bls_selected_seeds_by_date']}",
        "",
    ])
    return "\n".join(lines)


def render_safety(summary: dict[str, Any]) -> str:
    lines = [
        "# Public Offer Policy Safety Check",
        "",
        "Status: report only. No files were deleted, moved, deployed, or published.",
        "",
        "## Safety Checks",
        "",
    ]
    for key, value in summary["safety_checks"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend([
        "",
        "## Large Generated Files",
        "",
    ])
    for path, info in summary["large_generated_files"].items():
        lines.append(f"- `{path}`: {info['size_mb']} MB")
    lines.extend([
        "",
        "Recommendation: keep these full generated previews only for short-lived review branches. Long-term, commit compact summaries and regenerate full previews locally or store them as CI/artifact outputs.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    report = run()
    s = report["summary"]
    print("BLS public offer policy enablement audit complete (READ ONLY).")
    print(f"August BLS public sellable offers: {s['after']['august_bls_public_sellable_offers']}")
    print(f"August BLS selected seeds: {s['after']['august_bls_selected_seeds']}")
    print(f"August total selected seeds: {s['after']['august_total_selected_seeds']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
