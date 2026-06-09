#!/usr/bin/env python3
"""Build report-only appointment offer inventory and calendar preview.

This script models Lander-generated appointment seed offers separately from
real Enrollware classes. It writes debug reports only and does not modify
public schedules, hub pages, class landers, CTAs, or Enrollware data.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_hub_offer_model_report import build_report as build_hub_offer_model_report
from scripts.build_hub_offer_model_report import load_public_visibility_rules, public_visibility_for_start
from scripts.build_instructor_availability_report import CONFIG_DIR, DEBUG_DIR, SOURCE_MODES, TZ, load_json, parse_dt
from scripts.build_proposed_seed_review import format_date
from scripts.build_publishable_seed_candidates import build_export


REPORT_JSON_PATH = DEBUG_DIR / "appointment_offer_inventory.json"
REPORT_MD_PATH = DEBUG_DIR / "appointment_offer_inventory.md"
REPORT_HTML_PATH = DEBUG_DIR / "appointment_offer_calendar.html"
REGISTRATION_TARGETS_PATH = CONFIG_DIR / "registration_targets.json"
CALENDAR_SOURCES_PATH = CONFIG_DIR / "calendar_sources.json"
APPOINTMENT_CONTAINER_PATH = ROOT / "data" / "inventory" / "appointment_containers.json"
SESSIONS_CURRENT_PATH = ROOT / "data" / "sessions_current.json"


def norm(value: Any) -> str:
    return str(value or "").strip()


def clean_text(value: Any) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = text.replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()


def normalize_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean_text(value).lower())


def instructor_key(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    parts = re.findall(r"[A-Za-z]+", text)
    if not parts:
        return normalize_key(text)
    if len(parts) == 1:
        return normalize_key(parts[0])
    return normalize_key(parts[0][0] + parts[-1])


def location_key(value: Any) -> str:
    text = clean_text(value).lower()
    replacements = {
        "nc - wilmington": "wilmington",
        "910cpr's office": "shipyard",
        "4018 shipyard blvd": "shipyard",
        "wilmington; shipyard blvd": "shipyard",
        "wilmington shipyard": "shipyard",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    key = normalize_key(text)
    if "shipyard" in key:
        return "shipyard"
    return key


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def parse_time_label(value: Any) -> str:
    dt = parse_dt(value)
    if not dt:
        return norm(value)
    return dt.strftime("%I:%M %p").lstrip("0")


def month_key(value: Any) -> str:
    day = parse_date(value)
    return day.strftime("%Y-%m") if day else "unknown"


def course_family(course_key: Any, course_title: Any) -> str:
    text = f"{course_key} {clean_text(course_title)}".lower()
    if "acls" in text:
        return "acls"
    if "pals" in text:
        return "pals"
    if "bls" in text:
        return "bls"
    if "heartsaver" in text or "first aid" in text or "cpr aed" in text:
        return "heartsaver"
    if "arc" in text:
        return "arc"
    if "hsi" in text:
        return "hsi"
    return "other"


def load_registration_targets() -> dict[str, dict[str, Any]]:
    config = load_json(REGISTRATION_TARGETS_PATH)
    targets: dict[str, dict[str, Any]] = {}
    for target in config.get("registration_targets", []):
        if not isinstance(target, dict):
            continue
        key = norm(target.get("registration_target_key"))
        if key:
            targets[key] = target
    return targets


def load_calendar_modes() -> dict[str, dict[str, Any]]:
    config = load_json(CALENDAR_SOURCES_PATH)
    modes: dict[str, dict[str, Any]] = {}
    for source in config.get("calendar_sources", []):
        if not isinstance(source, dict):
            continue
        instructor = norm(source.get("instructor_key"))
        if instructor:
            modes[instructor] = {
                "calendar_source_key": source.get("calendar_source_key"),
                "calendar_source_mode": source.get("calendar_mode"),
                "default_location_key": source.get("default_location_key"),
                "active": source.get("active"),
            }
    return modes


def load_appointment_ranges(warnings: list[str]) -> list[dict[str, Any]]:
    if not APPOINTMENT_CONTAINER_PATH.exists():
        warnings.append(f"{rel(APPOINTMENT_CONTAINER_PATH)} missing; appointment URLs cannot be verified.")
        return []
    config = load_json(APPOINTMENT_CONTAINER_PATH)
    ranges: list[dict[str, Any]] = []
    for item in config.get("containers", []):
        if not isinstance(item, dict):
            continue
        ranges.append(
            {
                "range_id": item.get("container_id"),
                "owner": item.get("instructor_name"),
                "location": item.get("location_name"),
                "verified_date": item.get("base_date") or item.get("first_valid_date"),
                "verified_appointmentDayId": item.get("base_appointmentDayId") or item.get("first_valid_appointmentDayId"),
                "last_valid_date": item.get("last_valid_date"),
                "last_valid_appointmentDayId": item.get("last_valid_appointmentDayId"),
                "generation_mode": "daily_contiguous",
                "status": item.get("status"),
                "source": "appointment_containers",
            }
        )
    return ranges


def appointment_mapping_for(offer: dict[str, Any], ranges: list[dict[str, Any]]) -> dict[str, Any]:
    offer_day = parse_date(offer.get("date"))
    offer_instructor = instructor_key(offer.get("instructor_key") or offer.get("instructor_display_name"))
    offer_location = location_key(offer.get("location_key"))
    if not offer_day:
        return {
            "appointment_url_status": "blocked_missing_date",
            "appointment_registration_url": None,
            "appointmentDayId": None,
            "appointment_range_id": None,
        }

    for row in ranges:
        owner_key = instructor_key(row.get("owner"))
        if owner_key and offer_instructor and owner_key != offer_instructor:
            continue
        range_location = location_key(row.get("location"))
        if range_location and offer_location and range_location != offer_location:
            continue

        verified_day = parse_date(row.get("verified_date"))
        last_day = parse_date(row.get("last_valid_date"))
        verified_id = row.get("verified_appointmentDayId")
        if not verified_day or not last_day or verified_id is None:
            continue
        if not (verified_day <= offer_day <= last_day):
            continue
        if row.get("generation_mode") != "daily_contiguous":
            return {
                "appointment_url_status": "blocked_non_contiguous_range",
                "appointment_registration_url": None,
                "appointmentDayId": None,
                "appointment_range_id": row.get("range_id"),
            }
        appointment_day_id = int(verified_id) + (offer_day - verified_day).days
        status = "verified_url" if row.get("status") == "active" else "predicted_url"
        return {
            "appointment_url_status": status,
            "appointment_registration_url": f"https://coastalcprtraining.enrollware.com/enroll?appointmentDayId={appointment_day_id}",
            "appointmentDayId": appointment_day_id,
            "appointment_range_id": row.get("range_id"),
        }

    return {
        "appointment_url_status": "blocked_no_appointment_mapping",
        "appointment_registration_url": None,
        "appointmentDayId": None,
        "appointment_range_id": None,
    }


def load_current_sessions(warnings: list[str]) -> list[dict[str, Any]]:
    if not SESSIONS_CURRENT_PATH.exists():
        warnings.append(f"{rel(SESSIONS_CURRENT_PATH)} missing; conflict checks are source_unavailable.")
        return []
    config = load_json(SESSIONS_CURRENT_PATH)
    sessions = config.get("sessions", []) if isinstance(config, dict) else []
    return [row for row in sessions if isinstance(row, dict)]


def session_start_end(session: dict[str, Any]) -> tuple[datetime | None, datetime | None]:
    start = parse_dt(session.get("start_datetime") or session.get("start") or session.get("start_at"))
    end = parse_dt(session.get("end_datetime") or session.get("end") or session.get("end_at"))
    return start, end


def session_instructor_key(session: dict[str, Any]) -> str:
    return instructor_key(
        session.get("instructor")
        or session.get("lead_instructor")
        or session.get("lead_instructor_name")
        or session.get("instructor_name")
    )


def session_location_key(session: dict[str, Any]) -> str:
    return location_key(session.get("location") or session.get("location_name") or session.get("location_display"))


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def conflict_check_for_offer(offer: dict[str, Any], sessions: list[dict[str, Any]], source_available: bool) -> dict[str, Any]:
    if not source_available:
        return {
            "conflict_check_status": "source_unavailable",
            "conflict_count": 0,
            "conflicts": [],
        }
    start = parse_dt(offer.get("start_datetime"))
    end = parse_dt(offer.get("end_datetime"))
    if not start or not end:
        return {
            "conflict_check_status": "not_checked",
            "conflict_count": 0,
            "conflicts": [],
        }
    offer_instructor = instructor_key(offer.get("instructor_key") or offer.get("instructor_display_name"))
    offer_location = location_key(offer.get("location_key"))
    conflicts: list[dict[str, Any]] = []
    for session in sessions:
        session_start, session_end = session_start_end(session)
        if not session_start or not session_end or not overlaps(start, end, session_start, session_end):
            continue
        reasons: list[str] = []
        if offer_instructor and session_instructor_key(session) and offer_instructor == session_instructor_key(session):
            reasons.append("same_instructor")
        if offer_location and session_location_key(session) and offer_location == session_location_key(session):
            reasons.append("same_location")
        if not reasons:
            continue
        course = session.get("course") if isinstance(session.get("course"), dict) else {}
        conflicts.append(
            {
                "session_id": session.get("session_id") or session.get("id"),
                "course_title": clean_text(course.get("course_name_primary_clean") or course.get("course_name_raw") or session.get("course_name")),
                "start_datetime": session_start.isoformat(),
                "end_datetime": session_end.isoformat(),
                "reasons": reasons,
            }
        )
    return {
        "conflict_check_status": "conflict_found" if conflicts else "no_conflict_found",
        "conflict_count": len(conflicts),
        "conflicts": conflicts[:10],
    }


def calendar_availability_status(seed: dict[str, Any]) -> str:
    source_type = norm(seed.get("source_type"))
    if source_type in {"HARD", "SOFT-supported", "Brian horizon"}:
        return "calendar_window_reported"
    if source_type:
        return "calendar_window_other"
    return "not_checked"


def display_mode_for_offer(offer: dict[str, Any]) -> str:
    if offer.get("public_ready_status") == "public_ready" and offer.get("public_visibility_status") == "visible_publicly":
        return "appointment_seed_offer"
    if offer.get("approval_status") in {"needs_review", "approved_for_preview"}:
        return "needs_review"
    return "blocked"


def block_reason_for_offer(offer: dict[str, Any]) -> str | None:
    reasons: list[str] = []
    if offer.get("public_ready_status") != "public_ready":
        reasons.append(norm(offer.get("public_ready_block_reason")) or "not public ready")
    if offer.get("public_visibility_status") == "suppressed_cutoff_window":
        reasons.append("inside public display cutoff window")
    if offer.get("appointment_url_status") not in {"verified_url", "predicted_url"}:
        reasons.append(norm(offer.get("appointment_url_status")) or "missing appointment URL")
    if offer.get("conflict_check_status") == "conflict_found":
        reasons.append("conflict found against current Enrollware source")
    return "; ".join(reason for reason in reasons if reason) or None


def build_inventory(source_mode: str) -> dict[str, Any]:
    warnings: list[str] = []
    seed_export = build_export(source_mode)
    hub_offer_model = build_hub_offer_model_report(source_mode)
    visibility_rules = load_public_visibility_rules()
    targets = load_registration_targets()
    calendar_modes = load_calendar_modes()
    appointment_ranges = load_appointment_ranges(warnings)
    current_sessions = load_current_sessions(warnings)
    current_sessions_available = SESSIONS_CURRENT_PATH.exists()

    offers: list[dict[str, Any]] = []
    for seed in seed_export.get("publishable_seed_candidates", []):
        target = targets.get(norm(seed.get("registration_target_key")), {})
        appointment = appointment_mapping_for(seed, appointment_ranges)
        visibility = public_visibility_for_start(seed.get("start_datetime"), visibility_rules)
        conflict = conflict_check_for_offer(seed, current_sessions, current_sessions_available)
        instructor = norm(seed.get("instructor_key"))
        calendar = calendar_modes.get(instructor, {})
        public_ready_status = "public_ready" if seed.get("public_ready") is True else "blocked_not_public_ready"
        offer = {
            "offer_id": seed.get("seed_id"),
            "seed_id": seed.get("seed_id"),
            "course_key": seed.get("course_key"),
            "course_title": seed.get("course_title"),
            "course_family": course_family(seed.get("course_key"), seed.get("course_title")),
            "instructor_key": seed.get("instructor_key"),
            "instructor_display_name": seed.get("instructor_display_name"),
            "location_key": seed.get("location_key"),
            "date": seed.get("date"),
            "start_time": seed.get("start_time"),
            "end_time": seed.get("end_time"),
            "start_datetime": seed.get("start_datetime"),
            "end_datetime": seed.get("end_datetime"),
            "appointmentDayId": appointment.get("appointmentDayId"),
            "courseId": target.get("course_id") or seed.get("enrollware_course_id"),
            "registration_target_key": seed.get("registration_target_key"),
            "registration_backend": target.get("provider") or seed.get("registration_backend") or "enrollware",
            "appointment_registration_url": appointment.get("appointment_registration_url"),
            "appointment_url_status": appointment.get("appointment_url_status"),
            "appointment_range_id": appointment.get("appointment_range_id"),
            "calendar_source_key": calendar.get("calendar_source_key"),
            "calendar_source_mode": calendar.get("calendar_source_mode"),
            "calendar_availability_status": calendar_availability_status(seed),
            "conflict_check_status": conflict.get("conflict_check_status"),
            "conflict_count": conflict.get("conflict_count"),
            "conflicts": conflict.get("conflicts"),
            "public_visibility_status": visibility.get("public_visibility_status"),
            "public_visibility_note": visibility.get("public_visibility_note"),
            "cutoff_hours": visibility.get("cutoff_hours"),
            "hours_until_start": visibility.get("hours_until_start"),
            "public_ready_status": public_ready_status,
            "public_ready": seed.get("public_ready"),
            "public_ready_block_reason": seed.get("public_ready_block_reason"),
            "enrollware_presence_status": seed.get("enrollware_presence_status"),
            "approval_status": seed.get("approval_status"),
            "publishability_status": seed.get("publishability_status"),
            "rule_reason": seed.get("rule_reason"),
            "caution_flags": seed.get("caution_flags", []),
            "standalone_class_lander_allowed": False,
        }
        offer["block_reason"] = block_reason_for_offer(offer)
        offer["display_mode"] = display_mode_for_offer(offer)
        offers.append(offer)

    offers.sort(key=lambda item: (norm(item.get("date")), norm(item.get("start_time")), norm(item.get("instructor_key")), norm(item.get("course_key"))))
    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for offer in offers:
        by_date[norm(offer.get("date")) or "unknown"].append(offer)

    display_counts = Counter(norm(offer.get("display_mode")) for offer in offers)
    visibility_counts = Counter(norm(offer.get("public_visibility_status")) for offer in offers)
    public_ready_count = sum(1 for offer in offers if offer.get("public_ready_status") == "public_ready")
    august_count = sum(1 for offer in offers if month_key(offer.get("date")) == "2026-08")

    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "standalone_class_landers_created": False,
        "source_mode": source_mode,
        "inputs": {
            "publishable_seed_candidates": "scripts/build_publishable_seed_candidates.py",
            "hub_offer_model_report": "scripts/build_hub_offer_model_report.py",
            "registration_targets": rel(REGISTRATION_TARGETS_PATH),
            "calendar_sources": rel(CALENDAR_SOURCES_PATH),
            "appointment_containers": rel(APPOINTMENT_CONTAINER_PATH),
            "public_offer_visibility_rules": rel(CONFIG_DIR / "public_offer_visibility_rules.json"),
            "enrollware_presence_source": rel(SESSIONS_CURRENT_PATH),
        },
        "hub_offer_model_summary": hub_offer_model.get("summary", {}),
        "summary": {
            "total_appointment_offers": len(offers),
            "august_appointment_offers": august_count,
            "public_ready_appointment_offers": public_ready_count,
            "blocked_or_needs_review": sum(1 for offer in offers if offer.get("display_mode") in {"blocked", "needs_review"}),
            "with_appointment_urls": sum(1 for offer in offers if offer.get("appointment_registration_url")),
            "display_mode_counts": dict(sorted(display_counts.items())),
            "public_visibility_status_counts": dict(sorted(visibility_counts.items())),
            "by_instructor": dict(sorted(Counter(norm(offer.get("instructor_key")) for offer in offers).items())),
            "by_course_family": dict(sorted(Counter(norm(offer.get("course_family")) for offer in offers).items())),
            "warnings": warnings,
        },
        "calendar": {
            "dates": [
                {
                    "date": day,
                    "date_label": format_date(f"{day}T00:00:00"),
                    "offers": rows,
                }
                for day, rows in sorted(by_date.items())
            ]
        },
        "appointment_offers": offers,
    }


def write_json_report(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")


def write_markdown_report(report: dict[str, Any]) -> None:
    summary = report["summary"]
    lines = [
        "# Appointment Offer Inventory",
        "",
        "> REPORT ONLY - appointment seed offers are separate from real Enrollware classes. No public schedule files, class landers, CTAs, or Enrollware records were changed.",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Source mode: {report['source_mode']}",
        f"- Total appointment offers: {summary['total_appointment_offers']}",
        f"- August appointment offers: {summary['august_appointment_offers']}",
        f"- Public-ready appointment offers: {summary['public_ready_appointment_offers']}",
        f"- Blocked or needs review: {summary['blocked_or_needs_review']}",
        f"- With appointment URLs: {summary['with_appointment_urls']}",
        f"- Display modes: {json.dumps(summary['display_mode_counts'], sort_keys=True)}",
        f"- Public visibility: {json.dumps(summary['public_visibility_status_counts'], sort_keys=True)}",
        "",
        "## Notes",
        "",
        "- `standalone_class_lander_allowed` is false for every appointment seed offer.",
        "- Appointment URLs are review/admin inventory only and are not emitted to public pages by this script.",
        "- Public-ready requires the existing seed public-ready gate; appointment URL availability alone is not enough.",
        "",
    ]
    if summary["warnings"]:
        lines.append("## Warnings")
        lines.append("")
        for warning in summary["warnings"]:
            lines.append(f"- {warning}")
        lines.append("")

    lines.append("## Calendar Preview")
    lines.append("")
    for group in report["calendar"]["dates"]:
        lines.append(f"### {group['date_label']}")
        for offer in group["offers"]:
            url = offer.get("appointment_registration_url") or "no appointment URL"
            lines.append(
                f"- {offer.get('start_time')} - {offer.get('end_time')} - "
                f"{offer.get('instructor_key')} - {offer.get('course_title')} "
                f"[{offer.get('display_mode')}]"
            )
            lines.append(f"  - Seed: {offer.get('seed_id')}")
            lines.append(f"  - URL: {url}")
            lines.append(f"  - Public ready: {offer.get('public_ready_status')}")
            lines.append(f"  - Visibility: {offer.get('public_visibility_status')}")
            if offer.get("block_reason"):
                lines.append(f"  - Block reason: {offer.get('block_reason')}")
        lines.append("")

    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def badge(text: Any) -> str:
    value = html.escape(norm(text) or "unknown")
    return f'<span class="badge badge-{html.escape(normalize_key(value) or "unknown")}">{value}</span>'


def write_html_report(report: dict[str, Any]) -> None:
    options = {
        "instructors": sorted({norm(offer.get("instructor_key")) for offer in report["appointment_offers"] if norm(offer.get("instructor_key"))}),
        "families": sorted({norm(offer.get("course_family")) for offer in report["appointment_offers"] if norm(offer.get("course_family"))}),
        "locations": sorted({norm(offer.get("location_key")) for offer in report["appointment_offers"] if norm(offer.get("location_key"))}),
        "statuses": sorted({norm(offer.get("display_mode")) for offer in report["appointment_offers"] if norm(offer.get("display_mode"))}),
    }
    cards: list[str] = []
    for group in report["calendar"]["dates"]:
        offer_cards: list[str] = []
        for offer in group["offers"]:
            attrs = {
                "data-instructor": norm(offer.get("instructor_key")),
                "data-family": norm(offer.get("course_family")),
                "data-location": norm(offer.get("location_key")),
                "data-status": norm(offer.get("display_mode")),
            }
            attr_text = " ".join(f'{key}="{html.escape(value)}"' for key, value in attrs.items())
            url = offer.get("appointment_registration_url")
            url_html = f'<a href="{html.escape(url)}">{html.escape(url)}</a>' if url else "<span>No appointment URL</span>"
            offer_cards.append(
                f"""
                <article class="offer" {attr_text}>
                  <div class="offer-time">{html.escape(norm(offer.get('start_time')))} - {html.escape(norm(offer.get('end_time')))}</div>
                  <h3>{html.escape(norm(offer.get('course_title')))}</h3>
                  <div class="meta">{badge(offer.get('instructor_key'))} {badge(offer.get('course_family'))} {badge(offer.get('location_key'))} {badge(offer.get('display_mode'))}</div>
                  <dl>
                    <dt>Seed</dt><dd>{html.escape(norm(offer.get('seed_id')))}</dd>
                    <dt>AppointmentDayId</dt><dd>{html.escape(norm(offer.get('appointmentDayId')) or 'unknown')}</dd>
                    <dt>Course ID</dt><dd>{html.escape(norm(offer.get('courseId')) or 'unknown')}</dd>
                    <dt>Registration</dt><dd>{url_html}</dd>
                    <dt>Calendar</dt><dd>{html.escape(norm(offer.get('calendar_source_mode')))} / {html.escape(norm(offer.get('calendar_availability_status')))}</dd>
                    <dt>Conflict</dt><dd>{html.escape(norm(offer.get('conflict_check_status')))}</dd>
                    <dt>Visibility</dt><dd>{html.escape(norm(offer.get('public_visibility_status')))}</dd>
                    <dt>Public ready</dt><dd>{html.escape(norm(offer.get('public_ready_status')))}</dd>
                    <dt>Block reason</dt><dd>{html.escape(norm(offer.get('block_reason')) or 'none')}</dd>
                  </dl>
                </article>
                """
            )
        cards.append(
            f"""
            <section class="day">
              <h2>{html.escape(group['date_label'])}</h2>
              <div class="offers">{''.join(offer_cards)}</div>
            </section>
            """
        )

    def select_control(name: str, values: list[str]) -> str:
        opts = ['<option value="">All</option>'] + [f'<option value="{html.escape(value)}">{html.escape(value)}</option>' for value in values]
        return f'<label>{html.escape(name.title())}<select id="filter-{html.escape(name)}">{"".join(opts)}</select></label>'

    body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="robots" content="noindex,nofollow">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Appointment Offer Calendar Preview</title>
  <style>
    :root {{ color-scheme: light; --line: #d8dee4; --ink: #1f2933; --muted: #637083; --panel: #f7f9fb; --accent: #0f766e; }}
    body {{ margin: 0; font-family: Arial, sans-serif; color: var(--ink); background: white; }}
    header {{ padding: 24px; border-bottom: 1px solid var(--line); background: var(--panel); }}
    h1 {{ margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }}
    h2 {{ margin: 0 0 12px; font-size: 20px; }}
    h3 {{ margin: 4px 0 8px; font-size: 16px; }}
    .summary {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }}
    .summary span, .badge {{ display: inline-block; border: 1px solid var(--line); border-radius: 4px; padding: 3px 7px; background: white; font-size: 12px; }}
    .filters {{ display: flex; flex-wrap: wrap; gap: 12px; padding: 16px 24px; border-bottom: 1px solid var(--line); }}
    label {{ display: grid; gap: 4px; font-size: 12px; color: var(--muted); }}
    select {{ min-width: 160px; padding: 6px; border: 1px solid var(--line); border-radius: 4px; background: white; }}
    main {{ padding: 24px; display: grid; gap: 20px; }}
    .day {{ border-top: 3px solid var(--accent); padding-top: 12px; }}
    .offers {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }}
    .offer {{ border: 1px solid var(--line); border-radius: 6px; padding: 12px; background: #fff; }}
    .offer-time {{ color: var(--accent); font-weight: 700; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }}
    dl {{ display: grid; grid-template-columns: 112px 1fr; gap: 4px 8px; font-size: 12px; }}
    dt {{ color: var(--muted); }}
    dd {{ margin: 0; overflow-wrap: anywhere; }}
    .hidden {{ display: none; }}
  </style>
</head>
<body>
  <header>
    <h1>Appointment Offer Calendar Preview</h1>
    <p>REPORT ONLY - no public schedule files, class landers, CTAs, or Enrollware records were changed.</p>
    <div class="summary">
      <span>Total: {report['summary']['total_appointment_offers']}</span>
      <span>August: {report['summary']['august_appointment_offers']}</span>
      <span>Public ready: {report['summary']['public_ready_appointment_offers']}</span>
      <span>Blocked/needs review: {report['summary']['blocked_or_needs_review']}</span>
      <span>With URLs: {report['summary']['with_appointment_urls']}</span>
    </div>
  </header>
  <nav class="filters">
    {select_control('instructor', options['instructors'])}
    {select_control('family', options['families'])}
    {select_control('location', options['locations'])}
    {select_control('status', options['statuses'])}
  </nav>
  <main>{''.join(cards)}</main>
  <script>
    const filters = ['instructor', 'family', 'location', 'status'];
    function applyFilters() {{
      const selected = Object.fromEntries(filters.map(name => [name, document.getElementById(`filter-${{name}}`).value]));
      document.querySelectorAll('.offer').forEach(card => {{
        const visible = filters.every(name => !selected[name] || card.dataset[name] === selected[name]);
        card.classList.toggle('hidden', !visible);
      }});
    }}
    filters.forEach(name => document.getElementById(`filter-${{name}}`).addEventListener('change', applyFilters));
  </script>
</body>
</html>"""
    REPORT_HTML_PATH.write_text(body, encoding="utf-8")


def write_reports(report: dict[str, Any]) -> None:
    write_json_report(report)
    write_markdown_report(report)
    write_html_report(report)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build report-only appointment offer inventory.")
    parser.add_argument("--source", choices=sorted(SOURCE_MODES), default="auto", help="Seed calendar source mode.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_inventory(args.source)
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print(f"Wrote {REPORT_HTML_PATH}")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
