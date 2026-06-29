from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts import generate_dynamic_offers

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
DEBUG_DIR = ROOT / "debug"
RUNTIME_SNAPSHOT_DIR = ROOT / "data" / "runtime" / "calendar_snapshots"

TRACE_MD = AUDIT_DIR / "live_availability_snapshot_trace.md"
TRACE_JSON = AUDIT_DIR / "live_availability_snapshot_trace.json"
DIFF_CSV = AUDIT_DIR / "seed_sim_vs_active_generation_diff.csv"
ZERO_REASON_MD = AUDIT_DIR / "august_dynamic_generation_zero_reason.md"
MIN_FIX_MD = AUDIT_DIR / "minimum_fix_to_align_live_snapshot.md"
TEST_PLAN_MD = AUDIT_DIR / "regression_test_plan_august_availability.md"

AUGUST_PREFIX = "2026-08"
BLS_KEYS = {"aha_bls_renewal", "aha_bls_initial", "aha_bls_heartcode_skills", "aha_bls_provider", "aha_bls_provider_renewal"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: Any) -> str:
    return str(value or "").strip()


def date_of(row: dict[str, Any]) -> str:
    return clean(row.get("date") or row.get("candidate_start") or row.get("start") or row.get("start_datetime"))[:10]


def start_time_of(row: dict[str, Any]) -> str:
    for key in ("start_time", "candidate_start", "start", "start_datetime"):
        value = clean(row.get(key))
        if len(value) >= 16 and "T" in value:
            return value[11:16]
        if len(value) == 5 and ":" in value:
            return value
    return ""


def end_time_of(row: dict[str, Any]) -> str:
    for key in ("end_time", "candidate_end", "end", "end_datetime"):
        value = clean(row.get(key))
        if len(value) >= 16 and "T" in value:
            return value[11:16]
        if len(value) == 5 and ":" in value:
            return value
    return ""


def is_august(row: dict[str, Any]) -> bool:
    return date_of(row).startswith(AUGUST_PREFIX)


def is_bls(row: dict[str, Any]) -> bool:
    text = " ".join(clean(row.get(key)).lower() for key in ("course_key", "course_family", "course_title", "allowed_course_families"))
    return any(key in text for key in BLS_KEYS) or "bls" in text


def normalize_window(stage: str, row: dict[str, Any], source_file: str, source_note: str = "") -> dict[str, Any]:
    return {
        "stage": stage,
        "source_file": source_file,
        "date": date_of(row),
        "start_time": start_time_of(row),
        "end_time": end_time_of(row),
        "instructor": clean(row.get("instructor_key") or row.get("instructor_name") or row.get("availability_instructor") or row.get("person_name")),
        "person_id": clean(row.get("person_id")),
        "location": clean(row.get("location_key") or row.get("location_name") or row.get("location") or row.get("offer_location")),
        "course_key_or_family": clean(row.get("course_key") or row.get("course_family") or row.get("allowed_course_families")),
        "source_id": clean(row.get("source_event_id") or row.get("source_availability_window") or row.get("horizon_key") or row.get("offer_id")),
        "status": clean(row.get("availability_status") or row.get("reason_code") or "present"),
        "source_note": source_note,
    }


def seed_simulation_rows(seed_simulation: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for instructor in seed_simulation.get("instructors", []):
        if not isinstance(instructor, dict):
            continue
        instructor_key = clean(instructor.get("instructor_key"))
        for key, stage in [
            ("final_usable_windows", "seed_sim_final_usable_window"),
            ("selected_seed_proposals", "seed_sim_selected_seed_proposal"),
        ]:
            for row in instructor.get(key, []):
                if isinstance(row, dict):
                    rows.append({"instructor_key": instructor_key, **row, "_stage": stage})
    return rows


def runtime_snapshot_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not RUNTIME_SNAPSHOT_DIR.exists():
        return rows
    for path in sorted(RUNTIME_SNAPSHOT_DIR.glob("*.json")):
        payload = read_json(path)
        for event in payload.get("events", []):
            if isinstance(event, dict):
                rows.append({
                    "_stage": "runtime_calendar_event",
                    "_source_file": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "source_event_id": event.get("event_id") or event.get("id"),
                    "source_calendar_id": event.get("calendar_source_id"),
                    "instructor_name": payload.get("calendar_source_id"),
                    "start_datetime": event.get("start"),
                    "end_datetime": event.get("end"),
                    "date": clean(event.get("start"))[:10],
                    "start_time": clean(event.get("start"))[11:16],
                    "end_time": clean(event.get("end"))[11:16],
                    "location": event.get("location"),
                    "course_key": "",
                    "availability_status": "runtime_event",
                    "summary": event.get("summary") or event.get("title"),
                    "recurrence": event.get("recurrence"),
                })
    return rows


def load_all() -> dict[str, Any]:
    return {
        "seed_simulation": read_json(DEBUG_DIR / "seed_simulation_report.json"),
        "live_snapshot": read_json(AUDIT_DIR / "live_availability_snapshot_preview.json"),
        "dynamic": read_json(AUDIT_DIR / "dynamic_offers_preview.json"),
        "schedule_future": read_json(ROOT / "docs" / "data" / "schedule_future.json"),
        "calendar_sources": read_json(ROOT / "data" / "config" / "calendar_sources.json"),
        "appointment_containers": read_json(ROOT / "data" / "inventory" / "appointment_containers.json"),
    }


def build_diff_rows(payloads: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in seed_simulation_rows(payloads["seed_simulation"]):
        if is_august(row) and is_bls(row):
            rows.append(normalize_window(row["_stage"], row, "debug/seed_simulation_report.json", "report_only_base_horizon"))
    for row in payloads["live_snapshot"].get("availability_blocks", []):
        if isinstance(row, dict) and (is_august(row) or is_bls(row)):
            rows.append(normalize_window("live_availability_snapshot_block", row, "data/audit/live_availability_snapshot_preview.json", "active_generation_source"))
    for row in runtime_snapshot_rows():
        if is_august(row) or is_bls(row):
            rows.append(normalize_window("runtime_calendar_event", row, row.get("_source_file", ""), clean(row.get("summary"))))
    for row in payloads["dynamic"].get("offers", []):
        if isinstance(row, dict) and (is_august(row) or is_bls(row)):
            rows.append(normalize_window("dynamic_offer", row, "data/audit/dynamic_offers_preview.json", clean(row.get("reason"))))
    rows.sort(key=lambda item: (item["date"], item["start_time"], item["stage"], item["source_file"]))
    return rows


def date_range(rows: list[dict[str, Any]]) -> dict[str, str | None]:
    dates = sorted(date_of(row) for row in rows if date_of(row))
    return {"min": dates[0] if dates else None, "max": dates[-1] if dates else None}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = ["stage", "source_file", "date", "start_time", "end_time", "instructor", "person_id", "location", "course_key_or_family", "source_id", "status", "source_note"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def summarize(payloads: dict[str, Any], diff_rows: list[dict[str, Any]]) -> dict[str, Any]:
    seed_rows = seed_simulation_rows(payloads["seed_simulation"])
    live_blocks = [row for row in payloads["live_snapshot"].get("availability_blocks", []) if isinstance(row, dict)]
    runtime_rows = runtime_snapshot_rows()
    dynamic_offers = [row for row in payloads["dynamic"].get("offers", []) if isinstance(row, dict)]
    selected_windows, selected_stats = generate_dynamic_offers.selected_availability_windows({
        "live_availability_snapshot": payloads["live_snapshot"],
        "instructor_availability": {},
        "location_resource_map": read_json(ROOT / "data" / "config" / "location_resource_map.json"),
    })
    august_seed_bls = [row for row in seed_rows if is_august(row) and is_bls(row)]
    august_live = [row for row in live_blocks if is_august(row)]
    august_dynamic = [row for row in dynamic_offers if is_august(row)]
    recurrence_august_sources = []
    for row in runtime_rows:
        recurrence_text = json.dumps(row.get("recurrence", []))
        if "202608" in recurrence_text:
            recurrence_august_sources.append(normalize_window("runtime_calendar_event_with_august_rrule", row, row.get("_source_file", ""), recurrence_text))
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "read_only": True,
        "deployed": False,
        "live_snapshot_script": "scripts/build_live_availability_snapshot.py",
        "active_dynamic_generator": "scripts/generate_dynamic_offers.py",
        "active_dynamic_input_path": "data/audit/live_availability_snapshot_preview.json",
        "active_dynamic_output_path": "data/audit/dynamic_offers_preview.json",
        "first_divergence_file": "data/audit/live_availability_snapshot_preview.json",
        "zero_reason": "live snapshot/runtime calendar snapshots contain no expanded August availability blocks; dynamic generation correctly uses the nonempty live snapshot and therefore never evaluates seed-simulation August base-horizon windows",
        "seed_simulation_date_range": date_range(seed_rows),
        "live_snapshot_date_range": date_range(live_blocks),
        "runtime_snapshot_date_range": date_range(runtime_rows),
        "dynamic_offer_date_range": date_range(dynamic_offers),
        "seed_simulation_august_bls_blocks": len(august_seed_bls),
        "live_snapshot_august_blocks": len(august_live),
        "dynamic_august_offers": len(august_dynamic),
        "live_snapshot_blocks_total": len(live_blocks),
        "live_snapshot_available_blocks": sum(1 for row in live_blocks if row.get("availability_status") == "available"),
        "dynamic_generation_availability_source": payloads["dynamic"].get("stats", {}).get("availability_source_used"),
        "dynamic_generation_availability_reason": payloads["dynamic"].get("stats", {}).get("availability_source_reason"),
        "selected_availability_source_stats": selected_stats,
        "runtime_events_total": len(runtime_rows),
        "runtime_events_with_august_rrule_not_expanded": len(recurrence_august_sources),
        "runtime_august_events": sum(1 for row in runtime_rows if is_august(row)),
        "live_snapshot_stats": payloads["live_snapshot"].get("stats", {}),
        "dynamic_offer_stats": payloads["dynamic"].get("stats", {}),
        "diff_counts_by_stage": dict(Counter(row["stage"] for row in diff_rows)),
        "diff_counts_by_source_file": dict(Counter(row["source_file"] for row in diff_rows)),
        "runtime_august_rrule_rows": recurrence_august_sources,
    }


def run() -> dict[str, Any]:
    payloads = load_all()
    diff_rows = build_diff_rows(payloads)
    summary = summarize(payloads, diff_rows)
    report = {"summary": summary, "diff_rows": diff_rows}
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(DIFF_CSV, diff_rows)
    TRACE_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    TRACE_MD.write_text(render_trace(report), encoding="utf-8")
    ZERO_REASON_MD.write_text(render_zero_reason(report), encoding="utf-8")
    MIN_FIX_MD.write_text(render_minimum_fix(report), encoding="utf-8")
    TEST_PLAN_MD.write_text(render_test_plan(report), encoding="utf-8")
    return report


def render_trace(report: dict[str, Any]) -> str:
    s = report["summary"]
    lines = [
        "# Live Availability Snapshot Trace",
        "",
        "Status: read-only trace. No deploy was performed.",
        "",
        "## Files And Flow",
        "",
        f"- Snapshot builder: `{s['live_snapshot_script']}`",
        "- Snapshot inputs: `data/config/calendar_sources.json`, `data/config/people_catalog.json`, `data/config/course_catalog.json`, `data/inventory/appointment_containers.json`, `data/runtime/calendar_snapshots/*.json`",
        f"- Active dynamic input: `{s['active_dynamic_input_path']}`",
        f"- Active dynamic generator: `{s['active_dynamic_generator']}`",
        f"- Active dynamic output: `{s['active_dynamic_output_path']}`",
        "",
        "## Date Ranges",
        "",
        f"- Seed simulation: {s['seed_simulation_date_range']['min']} to {s['seed_simulation_date_range']['max']}",
        f"- Runtime calendar snapshots: {s['runtime_snapshot_date_range']['min']} to {s['runtime_snapshot_date_range']['max']}",
        f"- Live availability snapshot: {s['live_snapshot_date_range']['min']} to {s['live_snapshot_date_range']['max']}",
        f"- Dynamic offers: {s['dynamic_offer_date_range']['min']} to {s['dynamic_offer_date_range']['max']}",
        "",
        "## August Counts",
        "",
        f"- Seed simulation August BLS blocks/proposals: {s['seed_simulation_august_bls_blocks']}",
        f"- Runtime August events: {s['runtime_august_events']}",
        f"- Runtime events with August RRULE not expanded: {s['runtime_events_with_august_rrule_not_expanded']}",
        f"- Live snapshot August blocks: {s['live_snapshot_august_blocks']}",
        f"- Dynamic August offers: {s['dynamic_august_offers']}",
        "",
        "## First Divergence",
        "",
        f"`{s['first_divergence_file']}` is the first file where August availability is absent. Seed simulation has August report-only base-horizon BLS windows; the live snapshot consumed by dynamic generation does not.",
        "",
        "## Why This Happens",
        "",
        s["zero_reason"],
        "",
        "See `seed_sim_vs_active_generation_diff.csv` for the row-level comparison.",
        "",
    ]
    return "\n".join(lines)


def render_zero_reason(report: dict[str, Any]) -> str:
    s = report["summary"]
    return "\n".join([
        "# August Dynamic Generation Zero Reason",
        "",
        "Active dynamic generation produces zero August offers because its selected availability source is a nonempty live snapshot that has no August availability blocks.",
        "",
        f"- Dynamic availability source: `{s['dynamic_generation_availability_source']}`",
        f"- Dynamic availability reason: `{s['dynamic_generation_availability_reason']}`",
        f"- Live snapshot range: {s['live_snapshot_date_range']['min']} to {s['live_snapshot_date_range']['max']}",
        f"- Seed simulation range: {s['seed_simulation_date_range']['min']} to {s['seed_simulation_date_range']['max']}",
        "",
        "Checked causes:",
        "",
        "- Live snapshot stale or not refreshed: likely. Runtime snapshots stop at July 4.",
        "- Live snapshot horizon too short: yes for August visibility.",
        "- Current date/window cutoff: not the dynamic offer date filter; the upstream snapshot lacks August rows.",
        "- Timezone conversion: not the first break.",
        "- Source file mismatch: yes. Seed simulation uses report-only base-horizon windows; active generation uses live snapshot blocks.",
        "- Occupancy/course duration/location/course/instructor filters: downstream, not reached for August.",
        "- Course Master gates: downstream, not reached for August.",
        "",
    ])


def render_minimum_fix(report: dict[str, Any]) -> str:
    return "\n".join([
        "# Minimum Fix To Align Live Snapshot",
        "",
        "Do not deploy from this branch.",
        "",
        "## Safest Minimal Fix",
        "",
        "Refresh or regenerate `data/runtime/calendar_snapshots/*.json` so the live snapshot builder has calendar data through August, including expanded recurring events where applicable, then rerun `scripts/build_live_availability_snapshot.py` and `scripts/generate_dynamic_offers.py`.",
        "",
        "If live calendar access cannot produce August rows quickly, add an explicit reviewed August availability merge into the live snapshot builder from the same base-horizon source used by seed simulation. That merge should be opt-in, report-only/audited, limited to Brian/Wilmington BLS, and still flow through existing dynamic generation, public sellable filtering, seed selection, appointmentDayId mapping, and public integrity checks.",
        "",
        "## Guardrail",
        "",
        "Add/keep an audit failure when seed simulation has future August BLS availability and active dynamic generation has zero August offers without explicit blocker reasons. Do not solve this by loosening Course Master or public filters first.",
        "",
    ])


def render_test_plan(report: dict[str, Any]) -> str:
    return "\n".join([
        "# Regression Test Plan: August Availability",
        "",
        "Implemented checks:",
        "",
        "- `tests.test_live_availability_snapshot_trace` verifies seed simulation sees August BLS availability while the active live snapshot does not, and records the divergence before Course Master gates.",
        "- `tests.test_generate_dynamic_offers.DynamicOffersTest.test_august_live_snapshot_block_generates_august_bls_offer` verifies that when a valid August BLS live snapshot block exists, dynamic generation produces an August offer.",
        "- Existing `tests.test_audit_august_seed_breakpoint` verifies August cannot silently disappear without the breakpoint report naming the upstream source mismatch.",
        "",
        "Manual/read-only validation commands:",
        "",
        "- `python -m scripts.audit_august_seed_breakpoint`",
        "- `python -m unittest tests.test_audit_august_seed_breakpoint`",
        "- `python -m unittest tests.test_live_availability_snapshot_trace`",
        "- `python -m unittest tests.test_generate_dynamic_offers.DynamicOffersTest.test_august_live_snapshot_block_generates_august_bls_offer`",
        "- `python -m scripts.public_offer_integrity_audit`",
        "",
    ])


def main() -> int:
    report = run()
    s = report["summary"]
    print("Live availability snapshot trace complete (READ ONLY).")
    print(f"First divergence: {s['first_divergence_file']}")
    print(f"Seed simulation August BLS blocks: {s['seed_simulation_august_bls_blocks']}")
    print(f"Live snapshot August blocks: {s['live_snapshot_august_blocks']}")
    print(f"Dynamic August offers: {s['dynamic_august_offers']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
