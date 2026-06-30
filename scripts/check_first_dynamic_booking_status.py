from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


from scripts.local_data_paths import dynamic_offers_preview_path, public_sellable_offers_preview_path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
STATUS_PATH = AUDIT_DIR / "first_dynamic_booking_status.json"
REPORT_PATH = AUDIT_DIR / "first_dynamic_booking_status_report.md"
UNKNOWN = "UNKNOWN"


def load_json(path: Path) -> tuple[Any | None, str | None]:
    if not path.exists():
        return None, "missing_file"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"invalid_json: {exc}"


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def stats(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict) and isinstance(payload.get("stats"), dict):
        return payload["stats"]
    return {}


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def normalize_key(value: Any) -> str:
    return clean_text(value).lower()


def is_shipyard(value: Any) -> bool:
    text = normalize_key(value)
    return "shipyard" in text or "4018" in text


def is_brian(value: Any) -> bool:
    text = normalize_key(value)
    return "brian" in text or "ennis" in text or text in {"b ennis", "b. ennis"}


def find_brian_shipyard_availability(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    blocks = as_list(payload.get("availability_blocks"))
    matches: list[dict[str, Any]] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if clean_text(block.get("availability_status")).lower() != "available":
            continue
        instructor = block.get("instructor_name") or block.get("display_name") or block.get("person_name")
        location = block.get("location_name") or block.get("location") or block.get("resource")
        location_mode = clean_text(block.get("availability_location_mode")).lower()
        if is_brian(instructor) and (is_shipyard(location) or location_mode == "instructor_time_only"):
            matches.append(block)
    return matches


def find_brian_shipyard_offers(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    matches: list[dict[str, Any]] = []
    for offer in as_list(payload.get("offers")):
        if not isinstance(offer, dict):
            continue
        instructor = offer.get("instructor_display_name") or offer.get("instructor_name")
        location = offer.get("location") or offer.get("location_name") or offer.get("resource")
        if is_brian(instructor) and is_shipyard(location):
            matches.append(offer)
    return matches


@dataclass
class Stage:
    number: int
    name: str
    passed: bool
    current_value: Any
    requirement: str
    blocker: str | None
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "name": self.name,
            "passed": self.passed,
            "current_value": self.current_value,
            "requirement": self.requirement,
            "blocker": self.blocker,
            "next_action": self.next_action,
        }


def build_status() -> dict[str, Any]:
    paths = {
        "live_availability": AUDIT_DIR / "live_availability_snapshot_preview.json",
        "dynamic_offers": dynamic_offers_preview_path(ROOT),
        "public_sellable_offers": public_sellable_offers_preview_path(ROOT),
        "schedule_seeds": AUDIT_DIR / "schedule_seeds_preview.json",
        "seed_url_preview": AUDIT_DIR / "seed_appointment_url_preview.json",
        "internal_dynamic_seed_preview": AUDIT_DIR / "internal_dynamic_seed_preview.json",
        "appointment_seed_registration_matches": AUDIT_DIR / "appointment_seed_registration_matches.json",
        "sessions_current": ROOT / "data" / "sessions_current.json",
        "schedule_future": ROOT / "docs" / "data" / "schedule_future.json",
        "class_report_ingest": AUDIT_DIR / "class_report_ingest_summary.json",
    }
    loaded: dict[str, Any | None] = {}
    load_errors: dict[str, str] = {}
    for key, path in paths.items():
        payload, error = load_json(path)
        loaded[key] = payload
        if error:
            load_errors[key] = error

    live_blocks = find_brian_shipyard_availability(loaded["live_availability"])
    dynamic_stats = stats(loaded["dynamic_offers"])
    dynamic_brian_shipyard = find_brian_shipyard_offers(loaded["dynamic_offers"])
    public_stats = stats(loaded["public_sellable_offers"])
    public_offers = as_list(loaded["public_sellable_offers"].get("offers")) if isinstance(loaded["public_sellable_offers"], dict) else []
    seed_stats = stats(loaded["schedule_seeds"])
    selected_seeds = as_list(loaded["schedule_seeds"].get("selected_seeds")) if isinstance(loaded["schedule_seeds"], dict) else []
    url_stats = stats(loaded["seed_url_preview"])
    url_previews = as_list(loaded["seed_url_preview"].get("previews")) if isinstance(loaded["seed_url_preview"], dict) else []
    internal_preview_stats = stats(loaded["internal_dynamic_seed_preview"])
    internal_preview_rows = as_list(loaded["internal_dynamic_seed_preview"].get("rows")) if isinstance(loaded["internal_dynamic_seed_preview"], dict) else []
    registration_matches = (
        as_list(loaded["appointment_seed_registration_matches"].get("matched_seed_records"))
        if isinstance(loaded["appointment_seed_registration_matches"], dict)
        else []
    )
    booked_pending_matches = [
        match for match in registration_matches
        if isinstance(match, dict) and match.get("registration_status") == "booked_pending_class_report"
    ]
    sessions_current = as_list(loaded["sessions_current"].get("sessions")) if isinstance(loaded["sessions_current"], dict) else []
    schedule_future = as_list(loaded["schedule_future"].get("sessions")) if isinstance(loaded["schedule_future"], dict) else []
    class_report = loaded["class_report_ingest"] if isinstance(loaded["class_report_ingest"], dict) else {}
    dynamic_offers = as_list(loaded["dynamic_offers"].get("offers")) if isinstance(loaded["dynamic_offers"], dict) else []
    dynamic_offers_generated = int(dynamic_stats.get("offers_generated") or len(dynamic_offers) or 0)
    dynamic_offers_from_live = dynamic_stats.get("availability_source_used") == "live_availability_snapshot"
    dynamic_stage_passed = dynamic_offers_from_live and dynamic_offers_generated > 0

    stages = [
        Stage(
            1,
            "Live calendar availability produces at least one Brian offerable-time block",
            bool(live_blocks),
            len(live_blocks),
            ">= 1 available Brian block, including instructor_time_only availability that can later target confirmed containers",
            None if live_blocks else "No available Brian offerable-time block found in live availability snapshot.",
            "Create or expose a valid Brian availability window in the live calendar snapshot, then rerun the read-only pipeline.",
        ),
        Stage(
            2,
            "Dynamic offers are generated from live availability",
            dynamic_stage_passed,
            {
                "availability_source_used": dynamic_stats.get("availability_source_used"),
                "offers_generated": dynamic_offers_generated,
                "brian_shipyard_offers": len(dynamic_brian_shipyard),
            },
            "live_availability_snapshot source and at least one generated offer",
            None if dynamic_stage_passed else "Dynamic offers are missing or are not using live availability.",
            "Rerun live snapshot and dynamic offer generation; fix source selection only if it stops using live availability.",
        ),
        Stage(
            3,
            "Confirmed-container public filter keeps at least one offer",
            len(public_offers) > 0,
            {
                "public_sellable_offers_kept": public_stats.get("public_sellable_offers_kept", len(public_offers)),
                "container_hidden_reasons": public_stats.get("offers_hidden_by_container_reason", {}),
            },
            ">= 1 public sellable offer after confirmed-container filtering",
            None if public_offers else "Confirmed-container policy kept zero public sellable offers.",
            "Add/confirm container coverage or align Brian + Shipyard availability/location matching so at least one offer survives confirmed-container filtering.",
        ),
        Stage(
            4,
            "Seed selection selects at least one seed",
            len(selected_seeds) > 0 or int(seed_stats.get("seeds_selected") or 0) > 0,
            {
                "seeds_selected": seed_stats.get("seeds_selected", len(selected_seeds)),
                "input_offers_read": seed_stats.get("input_offers_read"),
            },
            ">= 1 selected schedule seed",
            None if len(selected_seeds) > 0 or int(seed_stats.get("seeds_selected") or 0) > 0 else "No schedule seeds selected.",
            "Review seed strategy policy after at least one public sellable offer exists.",
        ),
        Stage(
            5,
            "Deterministic appointment URL preview generates at least one URL",
            len(url_previews) > 0 or int(url_stats.get("urls_previewed") or 0) > 0,
            {
                "urls_previewed": url_stats.get("urls_previewed", len(url_previews)),
                "seeds_blocked": url_stats.get("seeds_blocked"),
                "blocked_by_reason": url_stats.get("blocked_by_reason", {}),
            },
            ">= 1 appointment URL preview",
            None if len(url_previews) > 0 or int(url_stats.get("urls_previewed") or 0) > 0 else "No deterministic appointment URL previews generated.",
            "Run URL preview after seeds exist; fix container/date/range mismatches if seeds block.",
        ),
        Stage(
            6,
            "Internal/admin preview shows the customer-facing button",
            len(internal_preview_rows) > 0 or int(internal_preview_stats.get("preview_rows_rendered") or 0) > 0,
            {
                "preview_rows_rendered": internal_preview_stats.get("preview_rows_rendered", len(internal_preview_rows)),
                "urls_matched": internal_preview_stats.get("urls_matched"),
                "missing_urls": internal_preview_stats.get("missing_urls"),
            },
            "Internal/admin preview exists and renders a button for the selected seed",
            None if len(internal_preview_rows) > 0 or int(internal_preview_stats.get("preview_rows_rendered") or 0) > 0 else "No internal/admin dynamic seed preview artifact is currently recorded.",
            "Build an internal preview surface that renders selected seed details and a disabled/review-only customer-facing button.",
        ),
        Stage(
            7,
            "Manual click/registration creates class in Enrollware",
            bool(booked_pending_matches),
            {
                "matched_registration_signals": len(booked_pending_matches),
                "matched_seed_ids": [match.get("seed_id", UNKNOWN) for match in booked_pending_matches],
                "courseSchedIds": sorted({str(match.get("courseSchedId", UNKNOWN)) for match in booked_pending_matches}),
            },
            "Zapier/Sheet registration event is normalized and matched to an appointment seed",
            None if booked_pending_matches else "No matched Zapier/Sheet registration signal has been imported for a seed.",
            "Import the Zapier-backed registration sheet CSV with scripts.import_enrollware_registration_events, then rerun this status check.",
        ),
        Stage(
            8,
            "Routine public Enrollware scrape/hot-sync sees the created class",
            False,
            "manual_not_confirmed",
            "Existing read-only scrape/hot-sync detects the new Enrollware class",
            "No created dynamic class has been observed in local sessions yet.",
            "Run existing read-only hot-sync/scrape after a manual test booking exists.",
        ),
        Stage(
            9,
            "Lander treats that class as real occupancy and recalculates around it",
            False,
            {
                "sessions_current_count": len(sessions_current),
                "schedule_future_count": len(schedule_future),
            },
            "New dynamic booking appears in occupancy and blocks overlapping offers",
            "No dynamic test class marker is present to verify recalculation around it.",
            "After hot-sync sees the class, rerun sessions/current schedule and dynamic offer generation; verify overlap rejections.",
        ),
        Stage(
            10,
            "Class Report later confirms roster details",
            bool(class_report.get("rows_read")) and False,
            {
                "class_report_rows_read": class_report.get("rows_read", UNKNOWN),
                "sessions_current_written": class_report.get("sessions_current_written", UNKNOWN),
            },
            "Updated Class Report includes the created dynamic class and roster details",
            "Current Class Report ingest exists, but no dynamic test booking can be identified yet.",
            "After the manual booking is real, import the next Class Report and confirm the class/roster appears.",
        ),
    ]

    first_failing = next((stage for stage in stages if not stage.passed), None)
    status = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "read_only": True,
        "public_site_affected": False,
        "enrollware_called": False,
        "appointments_created": False,
        "appointment_urls_changed": False,
        "worker_routes_enabled": False,
        "files_read": {key: str(path) for key, path in paths.items()},
        "load_errors": load_errors,
        "stages": [stage.to_dict() for stage in stages],
        "first_failing_link": first_failing.number if first_failing else None,
        "first_failing_name": first_failing.name if first_failing else None,
        "current_blocker": first_failing.blocker if first_failing else None,
        "next_single_action": first_failing.next_action if first_failing else "Proceed to controlled manual proof and record the result.",
    }
    return status


def write_report(status: dict[str, Any]) -> None:
    lines = [
        "# First Successful Dynamic Booking Status",
        "",
        "Status: read-only diagnostic. This runner does not modify public pages, call Enrollware, create appointments, change appointment URLs, enable Worker routes, deploy, or commit.",
        "",
        "## Summary",
        "",
        f"- First failing link: {status.get('first_failing_link') or 'none'}",
        f"- Current blocker: {status.get('current_blocker') or 'none'}",
        f"- Next single action: {status.get('next_single_action')}",
        "",
        "## Success Chain",
        "",
        "| # | Stage | Status | Current value | Blocker |",
        "|---:|---|---|---|---|",
    ]
    for stage in status["stages"]:
        result = "PASS" if stage["passed"] else "FAIL"
        current_value = json.dumps(stage["current_value"], ensure_ascii=False)
        if len(current_value) > 220:
            current_value = current_value[:217] + "..."
        lines.append(
            f"| {stage['number']} | {stage['name']} | {result} | `{current_value}` | {stage.get('blocker') or ''} |"
        )
    lines.extend([
        "",
        "## Files Read",
        "",
    ])
    for name, path in status["files_read"].items():
        lines.append(f"- {name}: `{path}`")
    if status.get("load_errors"):
        lines.extend(["", "## Load Errors", ""])
        for name, error in status["load_errors"].items():
            lines.append(f"- {name}: {error}")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    status = build_status()
    STATUS_PATH.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(status)
    print("First dynamic booking status check complete (READ ONLY).")
    print("No public pages, Enrollware calls, appointments, appointment URL changes, Worker routes, deploys, or commits were performed.")
    print("")
    print(f"First failing link: {status.get('first_failing_link')}")
    print(f"Current blocker: {status.get('current_blocker')}")
    print(f"Next single action: {status.get('next_single_action')}")
    print("")
    print("Output files:")
    print(f"- {STATUS_PATH}")
    print(f"- {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
