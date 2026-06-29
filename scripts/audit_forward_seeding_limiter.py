from __future__ import annotations

import csv
import inspect
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts import build_candidate_slot_report, build_live_availability_snapshot, build_seed_simulation_report, export_calendar_snapshots

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
DATA_CONFIG_DIR = ROOT / "data" / "config"
RUNTIME_SNAPSHOT_DIR = ROOT / "data" / "runtime" / "calendar_snapshots"

TRACE_MD = AUDIT_DIR / "forward_seeding_limiter_trace.md"
TRACE_JSON = AUDIT_DIR / "forward_seeding_limiter_trace.json"
CODEPATH_MD = AUDIT_DIR / "seed_simulation_vs_live_snapshot_codepath.md"
HORIZON_CSV = AUDIT_DIR / "horizon_config_candidates.csv"
MIN_FIX_MD = AUDIT_DIR / "minimum_safe_forward_horizon_fix.md"

SEARCH_TERMS = [
    "horizon", "preview", "live_snapshot", "snapshot", "availability_window", "lookahead", "look_ahead",
    "days_out", "max_days", "min_days", "date_to", "date_from", "until", "end_date", "start_date",
    "14", "30", "60", "90", "120", "public_window", "seed_window", "base_horizon",
    "dynamic_offer", "availability_snapshot",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: Any) -> str:
    return str(value or "").strip()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def date_range_from_rows(rows: list[dict[str, Any]]) -> dict[str, str | None]:
    dates = sorted(clean(row.get("date") or row.get("candidate_start") or row.get("start") or row.get("start_datetime"))[:10] for row in rows)
    dates = [date for date in dates if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date)]
    return {"start": dates[0] if dates else None, "end": dates[-1] if dates else None}


def line_number_for_function(fn: Any) -> int:
    return inspect.getsourcelines(fn)[1]


def runtime_snapshot_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not RUNTIME_SNAPSHOT_DIR.exists():
        return rows
    for path in sorted(RUNTIME_SNAPSHOT_DIR.glob("*.json")):
        payload = read_json(path)
        for event in payload.get("events", []):
            if isinstance(event, dict):
                rows.append({
                    "source_file": rel(path),
                    "calendar_source_id": payload.get("calendar_source_id"),
                    "event_id": event.get("event_id") or event.get("id"),
                    "date": clean(event.get("start"))[:10],
                    "start": event.get("start"),
                    "end": event.get("end"),
                    "summary": event.get("summary") or event.get("title"),
                    "recurrence": event.get("recurrence", []),
                    "raw_rrule": (event.get("raw_properties") or {}).get("RRULE"),
                })
    return rows


def seed_sim_rows(seed_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for instructor in seed_payload.get("instructors", []):
        if not isinstance(instructor, dict):
            continue
        instructor_key = instructor.get("instructor_key")
        for key in ("base_candidate_windows", "final_usable_windows", "selected_seed_proposals"):
            for row in instructor.get(key, []):
                if isinstance(row, dict):
                    rows.append({"stage": key, "instructor_key": instructor_key, **row})
    return rows


def horizon_candidates() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    files = [
        DATA_CONFIG_DIR / "candidate_horizons.json",
        DATA_CONFIG_DIR / "seed_selection_rules.json",
        DATA_CONFIG_DIR / "calendar_sources.json",
        DATA_CONFIG_DIR / "public_offer_policy.json",
        ROOT / "scripts" / "export_calendar_snapshots.py",
        ROOT / "scripts" / "build_live_availability_snapshot.py",
        ROOT / "scripts" / "build_candidate_slot_report.py",
        ROOT / "scripts" / "build_seed_simulation_report.py",
    ]
    pattern = re.compile("|".join(re.escape(term) for term in SEARCH_TERMS), re.IGNORECASE)
    for path in files:
        if not path.exists():
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if pattern.search(line):
                rows.append({
                    "file": rel(path),
                    "line": line_no,
                    "term_matches": ";".join(term for term in SEARCH_TERMS if re.search(re.escape(term), line, re.IGNORECASE)),
                    "text": line.strip(),
                    "relevance": classify_candidate(path, line),
                })
    return rows


def classify_candidate(path: Path, line: str) -> str:
    text = line.lower()
    if path.name == "export_calendar_snapshots.py" and "export_days" in text:
        return "active_runtime_snapshot_export_window"
    if path.name == "export_calendar_snapshots.py" and "recurrence" in text:
        return "recurrence_recorded_not_expanded"
    if path.name == "calendar_sources.json" and "inverse_expansion_horizon_days" in text:
        return "live_snapshot_inverse_gap_horizon_after_runtime_events_loaded"
    if path.name == "candidate_horizons.json" and "lookahead_days" in text:
        return "seed_simulation_report_only_base_horizon"
    if path.name == "seed_selection_rules.json" and "window_days" in text:
        return "seed_selection_thinning_window_not_snapshot_limiter"
    if path.name == "public_offer_policy.json" and "maximum_days_out" in text:
        return "public_filter_downstream_not_snapshot_limiter"
    return "context"


def summarize() -> dict[str, Any]:
    seed_payload = read_json(ROOT / "debug" / "seed_simulation_report.json")
    live_payload = read_json(AUDIT_DIR / "live_availability_snapshot_preview.json")
    dynamic_payload = read_json(AUDIT_DIR / "dynamic_offers_preview.json")
    candidate_horizons = read_json(DATA_CONFIG_DIR / "candidate_horizons.json")
    seed_rules = read_json(DATA_CONFIG_DIR / "seed_selection_rules.json")
    calendar_sources = read_json(DATA_CONFIG_DIR / "calendar_sources.json")
    runtime_rows = runtime_snapshot_rows()
    seed_rows = seed_sim_rows(seed_payload)
    live_rows = [row for row in live_payload.get("availability_blocks", []) if isinstance(row, dict)]
    dynamic_rows = [row for row in dynamic_payload.get("offers", []) if isinstance(row, dict)]
    rrule_rows = [row for row in runtime_rows if row.get("raw_rrule") or row.get("recurrence")]

    brian_horizon = next(
        (row for row in candidate_horizons.get("candidate_horizons", []) if row.get("instructor_key") == "brian"),
        {},
    )
    brian_seed_rule = next(
        (row for row in seed_rules.get("seed_selection_rules", []) if row.get("instructor_key") == "brian"),
        {},
    )
    brian_calendar_source = next(
        (row for row in calendar_sources.get("calendar_sources", []) if row.get("calendar_source_key") == "brian_do_not_schedule"),
        {},
    )
    runtime_brian_path = RUNTIME_SNAPSHOT_DIR / "brian_do_not_schedule.json"
    runtime_brian = read_json(runtime_brian_path)

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "read_only": True,
        "deployed": False,
        "plain_answer": "The live snapshot stops at July 4 because scripts/export_calendar_snapshots.py::parse_ics_events records RRULE text but does not expand recurring VEVENT instances; the runtime Brian snapshot requested a 60-day window through 2026-08-18, but only explicit VEVENT master DTSTART rows through 2026-07-04 were exported, and scripts/build_live_availability_snapshot.py then built availability only from those exported runtime events.",
        "limiter": {
            "file": "scripts/export_calendar_snapshots.py",
            "function": "parse_ics_events",
            "function_line": line_number_for_function(export_calendar_snapshots.parse_ics_events),
            "specific_behavior": "VEVENT is appended only when DTSTART is inside window; RRULE/RDATE/EXDATE are stored in recurrence but no future occurrences are materialized.",
            "export_days_constant": export_calendar_snapshots.EXPORT_DAYS,
            "export_days_line": next(row["line"] for row in horizon_candidates() if row["file"] == "scripts/export_calendar_snapshots.py" and "EXPORT_DAYS = 60" in row["text"]),
            "not_caused_by": [
                "14-day seed selection window",
                "appointmentDayId range",
                "Course Master",
                "public sellable maximum_days_out",
                "dynamic generation occupancy filters",
            ],
        },
        "path_a_seed_simulation": {
            "entry_script": "scripts/build_seed_simulation_report.py",
            "candidate_source_script": "scripts/build_candidate_slot_report.py",
            "candidate_horizon_file": "data/config/candidate_horizons.json",
            "horizon_start_date": brian_horizon.get("horizon_start_date"),
            "lookahead_days": brian_horizon.get("lookahead_days"),
            "seed_selection_window_days": brian_seed_rule.get("window_days"),
            "date_range": date_range_from_rows(seed_rows),
            "august_rows": sum(1 for row in seed_rows if clean(row.get("candidate_start") or row.get("start")).startswith("2026-08")),
        },
        "path_b_live_snapshot": {
            "runtime_export_script": "scripts/export_calendar_snapshots.py",
            "runtime_export_function": "export_calendar_snapshots",
            "runtime_parse_function": "parse_ics_events",
            "runtime_snapshot_file": "data/runtime/calendar_snapshots/brian_do_not_schedule.json",
            "runtime_snapshot_declared_start": runtime_brian.get("date_range", {}).get("start"),
            "runtime_snapshot_declared_end": runtime_brian.get("date_range", {}).get("end"),
            "runtime_snapshot_declared_days": runtime_brian.get("date_range", {}).get("days"),
            "runtime_event_date_range": date_range_from_rows(runtime_rows),
            "runtime_rrule_event_count": len(rrule_rows),
            "live_snapshot_script": "scripts/build_live_availability_snapshot.py",
            "live_snapshot_function": "build_snapshot",
            "live_inverse_horizon_function": "inverse_expansion_horizon",
            "live_inverse_horizon_line": line_number_for_function(build_live_availability_snapshot.inverse_expansion_horizon),
            "calendar_source_inverse_expansion_horizon_days": brian_calendar_source.get("inverse_expansion_horizon_days"),
            "date_range": date_range_from_rows(live_rows),
            "august_rows": sum(1 for row in live_rows if clean(row.get("date")).startswith("2026-08")),
            "dynamic_offer_date_range": date_range_from_rows(dynamic_rows),
            "dynamic_august_offers": sum(1 for row in dynamic_rows if clean(row.get("date")).startswith("2026-08")),
        },
        "first_divergence": {
            "file": "data/runtime/calendar_snapshots/brian_do_not_schedule.json",
            "producer": "scripts/export_calendar_snapshots.py::parse_ics_events",
            "reason": "The runtime snapshot contains an RRULE with UNTIL=20260801 but no expanded July/August occurrences for that recurring event.",
        },
        "counts": {
            "runtime_events_by_source": dict(Counter(row["calendar_source_id"] for row in runtime_rows)),
            "runtime_rrule_events": len(rrule_rows),
            "live_snapshot_blocks": len(live_rows),
            "dynamic_offers": len(dynamic_rows),
        },
        "rrule_rows": rrule_rows,
    }


def write_horizon_csv(rows: list[dict[str, Any]]) -> None:
    fields = ["file", "line", "term_matches", "text", "relevance"]
    with HORIZON_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def render_trace(summary: dict[str, Any]) -> str:
    limiter = summary["limiter"]
    path_a = summary["path_a_seed_simulation"]
    path_b = summary["path_b_live_snapshot"]
    lines = [
        "# Forward Seeding Limiter Trace",
        "",
        "Status: read-only trace. No deploy was performed.",
        "",
        "## Plain-English Answer",
        "",
        summary["plain_answer"],
        "",
        "## Exact Limiter",
        "",
        f"- File: `{limiter['file']}`",
        f"- Function: `{limiter['function']}` starting near line {limiter['function_line']}",
        f"- Constant: `EXPORT_DAYS = {limiter['export_days_constant']}` near line {limiter['export_days_line']}",
        f"- Behavior: {limiter['specific_behavior']}",
        "",
        "## Why July 4",
        "",
        f"- Runtime Brian snapshot declared range: {path_b['runtime_snapshot_declared_start']} through {path_b['runtime_snapshot_declared_end']} ({path_b['runtime_snapshot_declared_days']} days)",
        f"- Runtime event rows actually exported: {path_b['runtime_event_date_range']['start']} through {path_b['runtime_event_date_range']['end']}",
        f"- Live availability snapshot built from runtime events: {path_b['date_range']['start']} through {path_b['date_range']['end']}",
        f"- Dynamic offers built from live snapshot: {path_b['dynamic_offer_date_range']['start']} through {path_b['dynamic_offer_date_range']['end']}",
        "",
        "July 4 is the latest explicit exported runtime event, not the configured export horizon and not an appointmentDayId boundary.",
        "",
        "## Seed Simulation Path",
        "",
        f"- Candidate horizon file: `{path_a['candidate_horizon_file']}`",
        f"- `horizon_start_date`: `{path_a['horizon_start_date']}`",
        f"- `lookahead_days`: `{path_a['lookahead_days']}`",
        f"- seed selection `window_days`: `{path_a['seed_selection_window_days']}`",
        f"- Seed simulation date range: {path_a['date_range']['start']} through {path_a['date_range']['end']}",
        f"- August rows: {path_a['august_rows']}",
        "",
        "## Live Snapshot Path",
        "",
        f"- Runtime export script: `{path_b['runtime_export_script']}`",
        f"- Runtime parse function: `{path_b['runtime_parse_function']}`",
        f"- Runtime snapshot file: `{path_b['runtime_snapshot_file']}`",
        f"- Live snapshot script: `{path_b['live_snapshot_script']}`",
        f"- Live inverse horizon function: `{path_b['live_inverse_horizon_function']}` near line {path_b['live_inverse_horizon_line']}",
        f"- `calendar_sources.json` `inverse_expansion_horizon_days`: `{path_b['calendar_source_inverse_expansion_horizon_days']}`",
        f"- Live snapshot August rows: {path_b['august_rows']}",
        f"- Dynamic August offers: {path_b['dynamic_august_offers']}",
        "",
        "## Not The Limiter",
        "",
    ]
    lines.extend(f"- {item}" for item in limiter["not_caused_by"])
    lines.extend(["", "See `horizon_config_candidates.csv` for all searched horizon/window candidates."])
    return "\n".join(lines) + "\n"


def render_codepath(summary: dict[str, Any]) -> str:
    a = summary["path_a_seed_simulation"]
    b = summary["path_b_live_snapshot"]
    return "\n".join([
        "# Seed Simulation vs Live Snapshot Codepath",
        "",
        "## Path A: Seed Simulation",
        "",
        "1. `scripts/build_seed_simulation_report.py::run` calls `build_candidate_report_payload`.",
        "2. `scripts/build_candidate_slot_report.py::build_inverse_blocking_candidates` loads `data/config/candidate_horizons.json`.",
        f"3. Brian's report-only horizon starts `{a['horizon_start_date']}` and uses `lookahead_days={a['lookahead_days']}`.",
        f"4. `data/config/seed_selection_rules.json` then thins the first `window_days={a['seed_selection_window_days']}` days into selected proposals.",
        f"5. Resulting seed simulation range: {a['date_range']['start']} through {a['date_range']['end']}.",
        "",
        "## Path B: Active Live Snapshot",
        "",
        "1. `scripts/export_calendar_snapshots.py::export_calendar_snapshots` fetches ICS data and sets a 60-day export window.",
        "2. `scripts/export_calendar_snapshots.py::parse_ics_events` keeps VEVENT records whose master `DTSTART` falls inside the window.",
        "3. `parse_ics_events` stores `RRULE`, `RDATE`, and `EXDATE` in `event['recurrence']`, but does not expand recurring occurrences.",
        f"4. `data/runtime/calendar_snapshots/brian_do_not_schedule.json` therefore contains explicit rows only through {b['runtime_event_date_range']['end']}.",
        "5. `scripts/build_live_availability_snapshot.py::load_runtime_snapshots` prefers `data/runtime/calendar_snapshots/*.json`.",
        "6. `scripts/build_live_availability_snapshot.py::build_snapshot` and `expand_inverse_availability` can only subtract/expand from the event rows available in that runtime snapshot.",
        f"7. Resulting live snapshot range: {b['date_range']['start']} through {b['date_range']['end']}.",
        "",
        "## First Divergence",
        "",
        "`scripts/export_calendar_snapshots.py::parse_ics_events` is the first function where the live path stops matching the seed-simulation path. The seed path invents report-only base-horizon windows from config; the live path requires exported runtime calendar events and does not materialize RRULE occurrences.",
        "",
    ])


def render_minimum_fix(summary: dict[str, Any]) -> str:
    return "\n".join([
        "# Minimum Safe Forward Horizon Fix",
        "",
        "Do not deploy from this branch.",
        "",
        "## Smallest Safe Fix",
        "",
        "Add RRULE/RDATE expansion to `scripts/export_calendar_snapshots.py::parse_ics_events` for occurrences inside the existing `EXPORT_DAYS` window, then regenerate runtime calendar snapshots and `live_availability_snapshot_preview.json`.",
        "",
        "Do not solve this by changing Course Master, public sellable filters, or appointment URL generation. The active path already declares a 60-day window; the missing piece is materializing recurring event occurrences before the live snapshot builder reads runtime events.",
        "",
        "## Horizon",
        "",
        "The current runtime export horizon is `EXPORT_DAYS = 60`. That is enough to reach mid-August from the June 19 snapshot generation date and is not the July 4 limiter. If the approved business forward-seeding horizon is longer than 60 days, make that a named config value rather than another hardcoded constant.",
        "",
        "## Guardrail",
        "",
        "Keep the audit/test that fails loudly when seed simulation sees August BLS availability but live snapshot/dynamic generation has zero August rows without explicit blocker reasons.",
        "",
    ])


def run() -> dict[str, Any]:
    summary = summarize()
    candidates = horizon_candidates()
    report = {
        "summary": summary,
        "horizon_config_candidates": candidates,
    }
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    write_horizon_csv(candidates)
    TRACE_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    TRACE_MD.write_text(render_trace(summary), encoding="utf-8")
    CODEPATH_MD.write_text(render_codepath(summary), encoding="utf-8")
    MIN_FIX_MD.write_text(render_minimum_fix(summary), encoding="utf-8")
    return report


def main() -> int:
    report = run()
    summary = report["summary"]
    print("Forward seeding limiter trace complete (READ ONLY).")
    print(summary["plain_answer"])
    print(f"First divergence: {summary['first_divergence']['file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
