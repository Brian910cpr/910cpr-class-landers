from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
RUNTIME_DIR = ROOT / "data" / "runtime" / "calendar_snapshots"

REPORT_MD = AUDIT_DIR / "rrule_expansion_fix_report.md"
REPORT_JSON = AUDIT_DIR / "rrule_expansion_fix_report.json"
BEFORE_AFTER_CSV = AUDIT_DIR / "live_snapshot_rrule_before_after_counts.csv"
AUGUST_COUNTS_CSV = AUDIT_DIR / "august_after_rrule_expansion_counts.csv"
DYNAMIC_AUGUST_CSV = AUDIT_DIR / "dynamic_offers_august_after_rrule_expansion.csv"
RENDERED_MD = AUDIT_DIR / "rendered_august_visibility_after_rrule_expansion.md"
RENDERED_JSON = AUDIT_DIR / "rendered_august_visibility_after_rrule_expansion.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: Any) -> str:
    return str(value or "").strip()


def is_august(row: dict[str, Any]) -> bool:
    return clean(row.get("date") or row.get("start") or row.get("start_at") or row.get("start_datetime")).startswith("2026-08")


def date_range(rows: list[dict[str, Any]]) -> dict[str, str | None]:
    dates = sorted(clean(row.get("date") or row.get("start") or row.get("start_at") or row.get("start_datetime"))[:10] for row in rows)
    dates = [date for date in dates if len(date) == 10]
    return {"start": dates[0] if dates else None, "end": dates[-1] if dates else None}


def is_bls(row: dict[str, Any]) -> bool:
    text = " ".join(clean(row.get(key)).lower() for key in ("course_family", "course_key", "course_title", "title", "course_name", "allowed_course_families"))
    return "bls" in text


def runtime_events() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(RUNTIME_DIR.glob("*.json")):
        payload = read_json(path)
        for event in payload.get("events", []):
            if isinstance(event, dict):
                rows.append({"source_file": str(path.relative_to(ROOT)).replace("\\", "/"), **event})
    return rows


def load_current() -> dict[str, Any]:
    return {
        "runtime_events": runtime_events(),
        "live": read_json(AUDIT_DIR / "live_availability_snapshot_preview.json"),
        "dynamic": read_json(AUDIT_DIR / "dynamic_offers_preview.json"),
        "public_sellable": read_json(AUDIT_DIR / "public_sellable_offers_preview.json"),
        "seeds": read_json(AUDIT_DIR / "schedule_seeds_preview.json"),
        "urls": read_json(AUDIT_DIR / "seed_appointment_url_preview.json"),
        "public_schedule": read_json(ROOT / "docs" / "public_schedule.json"),
        "schedule_future": read_json(ROOT / "docs" / "data" / "schedule_future.json"),
    }


def before_counts() -> dict[str, Any]:
    trace = read_json(AUDIT_DIR / "forward_seeding_limiter_trace.json")
    summary = trace["summary"]
    return {
        "runtime_snapshot_start": summary["path_b_live_snapshot"]["runtime_event_date_range"]["start"],
        "runtime_snapshot_end": summary["path_b_live_snapshot"]["runtime_event_date_range"]["end"],
        "live_snapshot_start": summary["path_b_live_snapshot"]["date_range"]["start"],
        "live_snapshot_end": summary["path_b_live_snapshot"]["date_range"]["end"],
        "live_august_blocks": summary["path_b_live_snapshot"]["august_rows"],
        "dynamic_august_offers": summary["path_b_live_snapshot"]["dynamic_august_offers"],
        "dynamic_august_bls_offers": 0,
        "selected_august_seeds": 0,
    }


def after_counts(current: dict[str, Any]) -> dict[str, Any]:
    live_blocks = [row for row in current["live"].get("availability_blocks", []) if isinstance(row, dict)]
    dynamic = [row for row in current["dynamic"].get("offers", []) if isinstance(row, dict)]
    public_sellable = [row for row in current["public_sellable"].get("offers", []) if isinstance(row, dict)]
    seeds = [row for row in current["seeds"].get("seeds", []) if isinstance(row, dict)]
    urls = [row for row in current["urls"].get("previews", []) if isinstance(row, dict)]
    runtime = current["runtime_events"]
    return {
        "runtime_snapshot_start": date_range(runtime)["start"],
        "runtime_snapshot_end": date_range(runtime)["end"],
        "runtime_events": len(runtime),
        "runtime_expanded_instances": sum(1 for row in runtime if row.get("recurrence_source") == "recurring_expanded_instance"),
        "live_snapshot_start": date_range(live_blocks)["start"],
        "live_snapshot_end": date_range(live_blocks)["end"],
        "live_blocks": len(live_blocks),
        "live_august_blocks": sum(1 for row in live_blocks if is_august(row)),
        "live_august_bls_blocks": sum(1 for row in live_blocks if is_august(row) and is_bls(row)),
        "dynamic_offers": len(dynamic),
        "dynamic_august_offers": sum(1 for row in dynamic if is_august(row)),
        "dynamic_august_bls_offers": sum(1 for row in dynamic if is_august(row) and is_bls(row)),
        "public_sellable_offers": len(public_sellable),
        "public_sellable_august_offers": sum(1 for row in public_sellable if is_august(row)),
        "public_sellable_august_bls_offers": sum(1 for row in public_sellable if is_august(row) and is_bls(row)),
        "selected_seeds": len(seeds),
        "selected_august_seeds": sum(1 for row in seeds if is_august(row)),
        "selected_august_bls_seeds": sum(1 for row in seeds if is_august(row) and is_bls(row)),
        "url_previews": len(urls),
        "august_url_previews": sum(1 for row in urls if is_august(row)),
    }


def rendered_counts(current: dict[str, Any]) -> dict[str, Any]:
    public_rows = [row for row in current["public_schedule"].get("sessions", []) if isinstance(row, dict)]
    future_rows = [row for row in current["schedule_future"].get("sessions", []) if isinstance(row, dict)]
    return {
        "render_regenerated": False,
        "reason": "No public page/render build was run for this RRULE fix branch. The task was kept to snapshot, dynamic, public-filter, seed, URL-preview, and audit generation.",
        "public_schedule_august_rows_current": sum(1 for row in public_rows if is_august(row)),
        "schedule_future_august_rows_current": sum(1 for row in future_rows if is_august(row)),
        "public_schedule_august_seed_rows_current": sum(1 for row in public_rows if is_august(row) and row.get("seed_id")),
        "schedule_future_august_seed_rows_current": sum(1 for row in future_rows if is_august(row) and row.get("seed_id")),
    }


def write_counts_csv(path: Path, before: dict[str, Any], after: dict[str, Any]) -> None:
    keys = sorted(set(before) | set(after))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "before", "after"])
        writer.writeheader()
        for key in keys:
            writer.writerow({"metric": key, "before": before.get(key, ""), "after": after.get(key, "")})


def write_august_counts_csv(path: Path, after: dict[str, Any]) -> None:
    keys = [
        "live_august_blocks",
        "live_august_bls_blocks",
        "dynamic_august_offers",
        "dynamic_august_bls_offers",
        "public_sellable_august_offers",
        "public_sellable_august_bls_offers",
        "selected_august_seeds",
        "selected_august_bls_seeds",
        "august_url_previews",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "after"])
        writer.writeheader()
        for key in keys:
            writer.writerow({"metric": key, "after": after.get(key, 0)})


def write_dynamic_august_csv(path: Path, current: dict[str, Any]) -> None:
    rows = [
        row for row in current["dynamic"].get("offers", [])
        if isinstance(row, dict) and is_august(row) and is_bls(row)
    ]
    fields = [
        "offer_id", "date", "start_time", "end_time", "course_id", "course_title", "course_family",
        "instructor_display_name", "location", "source_availability_window", "appointmentDayId",
        "appointment_registration_url",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def render_markdown(report: dict[str, Any]) -> str:
    before = report["before"]
    after = report["after"]
    return "\n".join([
        "# RRULE Expansion Fix Report",
        "",
        "Status: implemented and regenerated locally. No deploy was performed.",
        "",
        "## What Changed",
        "",
        "`scripts/export_calendar_snapshots.py::parse_ics_events` now expands bounded RRULE/RDATE instances inside the requested snapshot range, preserves duration, supports UNTIL/COUNT/BYDAY/INTERVAL through python-dateutil, applies EXDATE, and suppresses generated occurrences when a RECURRENCE-ID override exists.",
        "",
        "## Before / After",
        "",
        f"- Live snapshot range before: {before['live_snapshot_start']} to {before['live_snapshot_end']}",
        f"- Live snapshot range after: {after['live_snapshot_start']} to {after['live_snapshot_end']}",
        f"- August live availability blocks before: {before['live_august_blocks']}",
        f"- August live availability blocks after: {after['live_august_blocks']}",
        f"- August dynamic BLS offers before: {before['dynamic_august_bls_offers']}",
        f"- August dynamic BLS offers after: {after['dynamic_august_bls_offers']}",
        f"- August selected seeds before: {before['selected_august_seeds']}",
        f"- August selected seeds after: {after['selected_august_seeds']}",
        "",
        "## Safety Gates",
        "",
        "Expanded recurrence creates availability candidates only. Downstream occupancy checks, duration/buffer checks, public sellable filtering, Course Master-related suppression, appointmentDayId/courseId URL preview, UNKNOWN course suppression, and public offer integrity remain separate downstream gates.",
        "",
        "## Render Scope",
        "",
        report["rendered"]["reason"],
        "",
    ])


def run() -> dict[str, Any]:
    current = load_current()
    before = before_counts()
    after = after_counts(current)
    rendered = rendered_counts(current)
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "read_only": True,
        "deployed": False,
        "before": before,
        "after": after,
        "rendered": rendered,
    }
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render_markdown(report), encoding="utf-8")
    write_counts_csv(BEFORE_AFTER_CSV, before, after)
    write_august_counts_csv(AUGUST_COUNTS_CSV, after)
    write_dynamic_august_csv(DYNAMIC_AUGUST_CSV, current)
    RENDERED_JSON.write_text(json.dumps(rendered, indent=2) + "\n", encoding="utf-8")
    RENDERED_MD.write_text(
        "# Rendered August Visibility After RRULE Expansion\n\n"
        f"{rendered['reason']}\n\n"
        f"- Current `docs/public_schedule.json` August rows: {rendered['public_schedule_august_rows_current']}\n"
        f"- Current `docs/data/schedule_future.json` August rows: {rendered['schedule_future_august_rows_current']}\n"
        f"- Current August seed rows in rendered/public inventory: {rendered['public_schedule_august_seed_rows_current'] + rendered['schedule_future_august_seed_rows_current']}\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    report = run()
    after = report["after"]
    print("RRULE expansion fix audit complete (READ ONLY).")
    print(f"August live blocks after: {after['live_august_blocks']}")
    print(f"August dynamic BLS offers after: {after['dynamic_august_bls_offers']}")
    print(f"August selected seeds after: {after['selected_august_seeds']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
