from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
DEBUG_DIR = ROOT / "debug"

REPORT_MD = AUDIT_DIR / "august_seed_breakpoint_report.md"
REPORT_JSON = AUDIT_DIR / "august_seed_breakpoint_report.json"
BLS_CSV = AUDIT_DIR / "august_bls_seed_pipeline.csv"
HEARTSAVER_CSV = AUDIT_DIR / "august_heartsaver_seed_pipeline.csv"
COURSE_MASTER_CSV = AUDIT_DIR / "course_master_gate_blockers_for_august.csv"
MIN_FIX_MD = AUDIT_DIR / "minimum_fix_to_light_up_august.md"

AUGUST_PREFIX = "2026-08"
TARGET_LOCATION_KEYS = {"shipyard", "wilmington", "910cpr_s_office", "wilmington_shipyard"}
BLS_FAMILIES = {"aha_bls_initial", "aha_bls_renewal", "aha_bls_provider", "aha_bls_provider_renewal"}
HEARTSAVER_FAMILIES = {
    "aha_heartsaver_first_aid_cpr_aed",
    "aha_heartsaver_first_aid_cpr_aed_blended",
    "aha_heartsaver_cpr_aed",
    "aha_heartsaver_cpr_aed_online",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: Any) -> str:
    return str(value or "").strip()


def norm(value: Any) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "_", clean(value).lower()).strip("_")


def is_august(row: dict[str, Any]) -> bool:
    date_value = clean(row.get("date") or row.get("start_datetime") or row.get("candidate_start") or row.get("start"))
    return date_value.startswith(AUGUST_PREFIX)


def family(row: dict[str, Any]) -> str:
    return clean(row.get("course_family") or row.get("course_key") or row.get("counted_visible_offer_course_keys") or "")


def is_bls(row: dict[str, Any]) -> bool:
    text = f"{family(row)} {row.get('course_title', '')} {row.get('course_key', '')}".lower()
    return family(row) in BLS_FAMILIES or "bls" in text


def is_heartsaver(row: dict[str, Any]) -> bool:
    text = f"{family(row)} {row.get('course_title', '')} {row.get('course_key', '')}".lower()
    return family(row) in HEARTSAVER_FAMILIES or "heartsaver" in text or "first aid cpr aed" in text


def location_key(row: dict[str, Any]) -> str:
    return norm(row.get("location") or row.get("location_key") or row.get("location_name") or row.get("location_display"))


def is_target_location(row: dict[str, Any]) -> bool:
    key = location_key(row)
    return key in TARGET_LOCATION_KEYS or "shipyard" in key or "wilmington" in key


def by_offer_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {clean(row.get("offer_id") or row.get("source_offer_id")): row for row in rows if clean(row.get("offer_id") or row.get("source_offer_id"))}


def hidden_by_offer_id(hidden: list[dict[str, Any]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for item in hidden:
        offer = item.get("offer") if isinstance(item, dict) else None
        if not isinstance(offer, dict):
            continue
        offer_id = clean(offer.get("offer_id"))
        if offer_id:
            out[offer_id] = [clean(reason) for reason in item.get("reason_codes", [])]
    return out


def source_window_id(row: dict[str, Any]) -> str:
    return clean(row.get("source_availability_window") or row.get("horizon_key") or row.get("stack_group_key"))


def availability_rows(seed_simulation: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for instructor in seed_simulation.get("instructors", []):
        if not isinstance(instructor, dict):
            continue
        instructor_key = clean(instructor.get("instructor_key"))
        for window in instructor.get("final_usable_windows", []):
            if isinstance(window, dict):
                rows.append({"stage": "availability", "instructor_key": instructor_key, **window})
        for proposal in instructor.get("selected_seed_proposals", []):
            if isinstance(proposal, dict):
                rows.append({"stage": "seed_simulation_selected_proposal", "instructor_key": instructor_key, **proposal})
    return rows


def make_pipeline_rows(
    course_group: str,
    dynamic: dict[str, Any],
    public_sellable: dict[str, Any],
    seeds: dict[str, Any],
    urls: dict[str, Any],
    seed_simulation: dict[str, Any],
    public_schedule: dict[str, Any],
    schedule_future: dict[str, Any],
) -> list[dict[str, Any]]:
    predicate = is_bls if course_group == "bls" else is_heartsaver
    hidden_lookup = hidden_by_offer_id(public_sellable.get("hidden_offers", []))
    sellable_lookup = by_offer_id(public_sellable.get("offers", []))
    seed_lookup = {clean(row.get("source_offer_id")): row for row in seeds.get("seeds", []) if clean(row.get("source_offer_id"))}
    url_lookup = {clean(row.get("source_offer_id")): row for row in urls.get("previews", []) if clean(row.get("source_offer_id"))}
    rows: list[dict[str, Any]] = []

    for row in availability_rows(seed_simulation):
        if not is_august(row) or not is_target_location(row) or not predicate(row):
            continue
        rows.append({
            "stage": row.get("stage"),
            "status": "present",
            "date": clean(row.get("date") or clean(row.get("candidate_start") or row.get("start"))[:10]),
            "start_time": clean(row.get("start_time") or clean(row.get("candidate_start") or row.get("start"))[11:16]),
            "course_family": family(row),
            "course_title": clean(row.get("course_title")),
            "location": clean(row.get("location") or row.get("location_key")),
            "instructor": clean(row.get("instructor_display_name") or row.get("instructor_key")),
            "offer_id": clean(row.get("offer_id")),
            "seed_id": clean(row.get("seed_id")),
            "appointmentDayId": clean(row.get("appointmentDayId")),
            "course_id": clean(row.get("course_id")),
            "appointment_url": clean(row.get("appointment_url_preview") or row.get("appointment_registration_url")),
            "filter_reasons": clean(row.get("skipped_reason") or row.get("selection_reason") or row.get("rule_reason")),
            "source_window": source_window_id(row),
        })

    dynamic_august = [
        row for row in dynamic.get("offers", [])
        if isinstance(row, dict) and is_august(row) and is_target_location(row) and predicate(row)
    ]
    for row in dynamic_august:
        offer_id = clean(row.get("offer_id"))
        reasons = hidden_lookup.get(offer_id, [])
        sellable = offer_id in sellable_lookup
        seed = seed_lookup.get(offer_id)
        url = url_lookup.get(offer_id)
        rows.append({
            "stage": "dynamic_offer",
            "status": "generated",
            "date": clean(row.get("date")),
            "start_time": clean(row.get("start_time")),
            "course_family": family(row),
            "course_title": clean(row.get("course_title")),
            "location": clean(row.get("location")),
            "instructor": clean(row.get("instructor_display_name")),
            "offer_id": offer_id,
            "seed_id": clean((seed or {}).get("seed_id")),
            "appointmentDayId": clean((url or {}).get("appointmentDayId")),
            "course_id": clean(row.get("course_id")),
            "appointment_url": clean((url or {}).get("appointment_url_preview")),
            "filter_reasons": "passed_public_sellable_filter" if sellable else ";".join(reasons or ["not_in_public_sellable_output"]),
            "source_window": source_window_id(row),
        })

    for stage_name, payload, key in [
        ("selected_seed", seeds, "seeds"),
        ("appointment_url_preview", urls, "previews"),
    ]:
        for row in payload.get(key, []):
            if isinstance(row, dict) and is_august(row) and is_target_location(row) and predicate(row):
                rows.append({
                    "stage": stage_name,
                    "status": "present",
                    "date": clean(row.get("date")),
                    "start_time": clean(row.get("start_time")),
                    "course_family": family(row),
                    "course_title": clean(row.get("course_title")),
                    "location": clean(row.get("location")),
                    "instructor": clean(row.get("instructor_display_name")),
                    "offer_id": clean(row.get("source_offer_id")),
                    "seed_id": clean(row.get("seed_id")),
                    "appointmentDayId": clean(row.get("appointmentDayId")),
                    "course_id": clean(row.get("course_id")),
                    "appointment_url": clean(row.get("appointment_url_preview")),
                    "filter_reasons": clean(row.get("blocking_reason") or ",".join(row.get("reasons", []))),
                    "source_window": source_window_id(row),
                })

    for source_name, payload, key in [
        ("docs_public_schedule", public_schedule, "sessions"),
        ("docs_data_schedule_future", schedule_future, "sessions"),
    ]:
        for row in payload.get(key, []):
            if not isinstance(row, dict):
                continue
            row_date = clean(row.get("date") or row.get("start") or row.get("start_at"))[:7]
            text = f"{row.get('course_key', '')} {row.get('title', '')} {row.get('course_name', '')} {row.get('official_course_name', '')}".lower()
            if row_date == AUGUST_PREFIX and is_target_location(row) and (("bls" in text) if course_group == "bls" else ("heartsaver" in text or "first aid" in text)):
                rows.append({
                    "stage": source_name,
                    "status": "render_inventory_row",
                    "date": clean(row.get("date") or row.get("start") or row.get("start_at"))[:10],
                    "start_time": clean(row.get("start") or row.get("start_at"))[11:16],
                    "course_family": clean(row.get("course_key")),
                    "course_title": clean(row.get("title") or row.get("course_name") or row.get("official_course_name")),
                    "location": clean(row.get("location") or row.get("location_name") or row.get("location_display")),
                    "instructor": clean(row.get("instructor") or row.get("lead_instructor_name")),
                    "offer_id": clean(row.get("session_id") or row.get("class_id")),
                    "seed_id": clean(row.get("seed_id")),
                    "appointmentDayId": clean(row.get("appointmentDayId")),
                    "course_id": clean(row.get("course_id") or row.get("course_number")),
                    "appointment_url": clean(row.get("register_url") or row.get("registration_url")),
                    "filter_reasons": "real_enrollware_or_rendered_inventory",
                    "source_window": "",
                })

    rows.sort(key=lambda item: (item["date"], item["start_time"], item["stage"], item["course_family"]))
    return rows


def course_master_gate_rows(course_master: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for course in course_master.get("courses", []):
        if not isinstance(course, dict):
            continue
        if not (is_bls(course) or is_heartsaver(course)):
            continue
        blockers = []
        for field in ["course_key", "appointment_seed_allowed", "review_needed_for_scheduling", "dynamic_offer_allowed", "appointment_course_id", "appointment_day_id_strategy"]:
            value = course.get(field)
            if field == "course_key" and clean(value).lower() in {"", "unknown"}:
                blockers.append("course_key_unknown")
            if field == "appointment_seed_allowed" and value is not True:
                blockers.append("appointment_seed_allowed_false")
            if field == "review_needed_for_scheduling" and value is True:
                blockers.append("review_needed_for_scheduling_true")
            if field == "dynamic_offer_allowed" and value is not True:
                blockers.append("dynamic_offer_allowed_false")
            if field in {"appointment_course_id", "appointment_day_id_strategy"} and clean(value).lower() in {"", "unknown"}:
                blockers.append(f"{field}_unknown")
        rows.append({
            "course_key": clean(course.get("course_key")),
            "enrollware_course_id": clean(course.get("enrollware_course_id")),
            "public_short_title": clean(course.get("public_short_title")),
            "appointment_seed_allowed": clean(course.get("appointment_seed_allowed")),
            "review_needed_for_scheduling": clean(course.get("review_needed_for_scheduling")),
            "dynamic_offer_allowed": clean(course.get("dynamic_offer_allowed")),
            "appointment_course_id": clean(course.get("appointment_course_id")),
            "appointment_day_id_strategy": clean(course.get("appointment_day_id_strategy")),
            "blockers": ";".join(blockers) or "none",
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0].keys()) if rows else [
        "stage", "status", "date", "start_time", "course_family", "course_title", "location",
        "instructor", "offer_id", "seed_id", "appointmentDayId", "course_id", "appointment_url",
        "filter_reasons", "source_window",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def summarize_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "by_stage": dict(Counter(row["stage"] for row in rows)),
        "by_filter_reason": dict(Counter(row["filter_reasons"] for row in rows if row.get("filter_reasons"))),
    }


def run() -> dict[str, Any]:
    dynamic = read_json(AUDIT_DIR / "dynamic_offers_preview.json")
    public_sellable = read_json(AUDIT_DIR / "public_sellable_offers_preview.json")
    seeds = read_json(AUDIT_DIR / "schedule_seeds_preview.json")
    urls = read_json(AUDIT_DIR / "seed_appointment_url_preview.json")
    course_master = read_json(ROOT / "data" / "config" / "course_master.json")
    seed_simulation = read_json(DEBUG_DIR / "seed_simulation_report.json")
    public_schedule = read_json(ROOT / "docs" / "public_schedule.json")
    schedule_future = read_json(ROOT / "docs" / "data" / "schedule_future.json")

    bls_rows = make_pipeline_rows("bls", dynamic, public_sellable, seeds, urls, seed_simulation, public_schedule, schedule_future)
    heartsaver_rows = make_pipeline_rows("heartsaver", dynamic, public_sellable, seeds, urls, seed_simulation, public_schedule, schedule_future)
    gate_rows = course_master_gate_rows(course_master)

    dynamic_august_total = sum(1 for row in dynamic.get("offers", []) if isinstance(row, dict) and is_august(row))
    seed_sim_august_bls = [row for row in bls_rows if row["stage"] == "seed_simulation_selected_proposal"]
    seed_sim_august_heartsaver = [row for row in heartsaver_rows if row["stage"] == "seed_simulation_selected_proposal"]
    url_august_total = sum(1 for row in urls.get("previews", []) if isinstance(row, dict) and is_august(row))
    public_august_seed_rows = [
        row for row in [*bls_rows, *heartsaver_rows]
        if row["stage"] in {"docs_public_schedule", "docs_data_schedule_future"} and row.get("seed_id")
    ]

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "read_only": True,
        "deployed": False,
        "first_breakpoint": "data/audit/dynamic_offers_preview.json",
        "first_breakpoint_reason": "August report-only base-horizon availability exists in debug/seed_simulation_report.json, but dynamic_offers_preview uses live_availability_snapshot and contains zero August offers.",
        "cause_category": "availability_source_horizon",
        "dynamic_offers_generated_total": len(dynamic.get("offers", [])),
        "dynamic_offers_generated_august_total": dynamic_august_total,
        "public_sellable_offers_total": len(public_sellable.get("offers", [])),
        "public_sellable_august_total": sum(1 for row in public_sellable.get("offers", []) if isinstance(row, dict) and is_august(row)),
        "selected_seeds_total": len(seeds.get("seeds", [])),
        "selected_august_seeds_total": sum(1 for row in seeds.get("seeds", []) if isinstance(row, dict) and is_august(row)),
        "appointment_url_previews_total": len(urls.get("previews", [])),
        "appointment_url_previews_august_total": url_august_total,
        "august_bls_seed_simulation_selected_proposals": len(seed_sim_august_bls),
        "august_heartsaver_seed_simulation_selected_proposals": len(seed_sim_august_heartsaver),
        "august_public_seed_rows_rendered": len(public_august_seed_rows),
        "dynamic_offer_stats": dynamic.get("stats", {}),
        "public_filter_stats": public_sellable.get("stats", {}),
        "seed_selection_stats": seeds.get("stats", {}),
        "url_preview_stats": urls.get("stats", {}),
        "bls_pipeline": summarize_counts(bls_rows),
        "heartsaver_pipeline": summarize_counts(heartsaver_rows),
        "course_master_gate_blockers": dict(Counter(row["blockers"] for row in gate_rows)),
        "would_appear_after_minimum_fix": seed_sim_august_bls[:8] + seed_sim_august_heartsaver[:8],
        "risks": [
            "Base-horizon August availability is report-only and must be promoted or regenerated into the active live availability source before public use.",
            "Only courses with reviewed Course Master rows, valid appointment containers, valid course IDs, and public sellable policy support should render.",
            "Existing Enrollware sessions and occupied scheduler windows must remain conflict blockers.",
        ],
    }

    report = {
        "summary": summary,
        "artifacts": {
            "august_bls_seed_pipeline": str(BLS_CSV.relative_to(ROOT)).replace("\\", "/"),
            "august_heartsaver_seed_pipeline": str(HEARTSAVER_CSV.relative_to(ROOT)).replace("\\", "/"),
            "course_master_gate_blockers_for_august": str(COURSE_MASTER_CSV.relative_to(ROOT)).replace("\\", "/"),
            "minimum_fix_to_light_up_august": str(MIN_FIX_MD.relative_to(ROOT)).replace("\\", "/"),
        },
        "bls_pipeline_rows": bls_rows,
        "heartsaver_pipeline_rows": heartsaver_rows,
        "course_master_gate_rows": gate_rows,
    }

    write_csv(BLS_CSV, bls_rows)
    write_csv(HEARTSAVER_CSV, heartsaver_rows)
    write_csv(COURSE_MASTER_CSV, gate_rows)
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render_report(report), encoding="utf-8")
    MIN_FIX_MD.write_text(render_minimum_fix(report), encoding="utf-8")
    return report


def render_report(report: dict[str, Any]) -> str:
    s = report["summary"]
    lines = [
        "# August Seed Breakpoint Report",
        "",
        "Status: blocked before public rendering. No deploy was performed.",
        "",
        "## Plain Answers",
        "",
        f"A. First disappearance: `{s['first_breakpoint']}`. August exists in `debug/seed_simulation_report.json`, but active dynamic offers contain `{s['dynamic_offers_generated_august_total']}` August rows.",
        "B. Cause: availability source/horizon. The active dynamic generator is reading live availability blocks that stop at July 4, not the August report-only base-horizon availability. Course Master gates are not the first blocker.",
        "C. Smallest fix: promote/regenerate reviewed August Wilmington availability into the active availability source consumed by dynamic offer generation, then rerun the existing public filter, seed selection, URL preview, public inventory, and hub rendering steps.",
        "D. Rows after fix: BLS Wilmington rows should come from the August Brian selected proposals listed in `august_bls_seed_pipeline.csv`; no Heartsaver August Wilmington selected proposals currently exist in the seed simulation.",
        "E. Risks: report-only availability must not bypass conflict checks, appointment container/date bounds, Course Master review gates, UNKNOWN course suppression, public sellable limits, or rendered-page verification.",
        "",
        "## Stage Counts",
        "",
        f"- Dynamic offers total: {s['dynamic_offers_generated_total']}",
        f"- Dynamic offers in August: {s['dynamic_offers_generated_august_total']}",
        f"- Public sellable offers total: {s['public_sellable_offers_total']}",
        f"- Public sellable offers in August: {s['public_sellable_august_total']}",
        f"- Selected seeds total: {s['selected_seeds_total']}",
        f"- Selected August seeds: {s['selected_august_seeds_total']}",
        f"- Appointment URL previews total: {s['appointment_url_previews_total']}",
        f"- Appointment URL previews in August: {s['appointment_url_previews_august_total']}",
        f"- August BLS selected proposals in seed simulation: {s['august_bls_seed_simulation_selected_proposals']}",
        f"- August Heartsaver selected proposals in seed simulation: {s['august_heartsaver_seed_simulation_selected_proposals']}",
        f"- August public seed rows rendered: {s['august_public_seed_rows_rendered']}",
        "",
        "## Filter Reasons",
        "",
        "No August dynamic offers reach public filtering, so there are no August public-filter rejection reasons yet. Current overall public filter reasons are:",
    ]
    hidden = s["public_filter_stats"].get("hidden_offers_by_reason", {})
    lines.extend(f"- `{reason}`: {count}" for reason, count in hidden.items()) if hidden else lines.append("- None")
    lines.extend([
        "",
        "## Course Master Gate Finding",
        "",
        "Course Master has conservative gates, but those gates are downstream of the first August break. They must stay in place for UNKNOWN/unreviewed rows. If Course Master is promoted into this path, the AHA BLS/Heartsaver appointment-seed flags are currently too conservative/stale for rows already proven elsewhere in the seed pipeline. See `course_master_gate_blockers_for_august.csv` for exact rows.",
        "",
        "## Emergency manual fallback",
        "",
        "If the seed fix is not approved fast enough, Brian would need to manually create only the minimum August Enrollware classes that cover the currently selected BLS August proposals in `august_bls_seed_pipeline.csv`. This is an emergency safety net, not the primary solution.",
        "",
    ])
    return "\n".join(lines)


def render_minimum_fix(report: dict[str, Any]) -> str:
    rows = report["summary"]["would_appear_after_minimum_fix"]
    lines = [
        "# Minimum Fix To Light Up August",
        "",
        "Do not deploy from this audit branch.",
        "",
        "## Smallest Change",
        "",
        "Feed reviewed August Wilmington base-horizon availability into the active availability source used by `data/audit/dynamic_offers_preview.json`, or extend `live_availability_snapshot` so it contains those August blocks. Then rerun the existing pipeline without bypassing public filters.",
        "",
        "The current first break is not page rendering and not Course Master gating. August BLS proposals exist before the active dynamic-offer source, then vanish because active dynamic offers have zero August rows.",
        "",
        "## Rows Expected After Fix",
        "",
    ]
    if rows:
        for row in rows:
            lines.append(f"- {row['date']} {row['start_time']} {row['course_family']} at {row['location']} with {row['instructor']}")
    else:
        lines.append("- None identified from current seed simulation.")
    lines.extend([
        "",
        "## Required Rerun And Checks",
        "",
        "1. Regenerate dynamic offers.",
        "2. Regenerate public sellable offers.",
        "3. Regenerate selected seeds.",
        "4. Regenerate appointment URL preview.",
        "5. Regenerate public inventory and hubs.",
        "6. Run public offer integrity checks and render verification.",
        "",
        "## Risks If Enabled",
        "",
        "- Report-only base-horizon availability may be too broad unless reviewed.",
        "- Appointment containers must still provide valid August `appointmentDayId` values.",
        "- Course ID mappings must remain exact.",
        "- UNKNOWN or unreviewed Course Master rows must remain suppressed.",
        "- Existing Enrollware classes and occupied scheduler windows must remain blockers.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    report = run()
    summary = report["summary"]
    print(f"First breakpoint: {summary['first_breakpoint']}")
    print(f"Cause: {summary['cause_category']}")
    print(f"August dynamic offers: {summary['dynamic_offers_generated_august_total']}")
    print(f"August BLS selected proposals before break: {summary['august_bls_seed_simulation_selected_proposals']}")
    print(f"Wrote {REPORT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
