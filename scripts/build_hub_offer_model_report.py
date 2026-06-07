#!/usr/bin/env python3
"""Build a report-only hub offer ingestion/display contract.

This script models how current Enrollware classes and future seed offers could
be displayed on hub pages. It intentionally does not write public output.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_instructor_availability_report import CONFIG_DIR, DEBUG_DIR, SOURCE_MODES, TZ, load_json, parse_dt
from scripts.build_proposed_seed_review import course_title, format_date, format_time
from scripts.build_publishable_seed_candidates import build_export


REPORT_JSON_PATH = DEBUG_DIR / "hub_offer_model_report.json"
REPORT_MD_PATH = DEBUG_DIR / "hub_offer_model_report.md"
SESSIONS_CURRENT_PATH = ROOT / "data" / "sessions_current.json"
SEO_HUBS_PATH = CONFIG_DIR / "seo_hubs.json"
SLUG_HUBS_PATH = CONFIG_DIR / "slug_hubs.json"
REGISTRATION_TARGETS_PATH = CONFIG_DIR / "registration_targets.json"
SEED_APPROVALS_PATH = ROOT / "data" / "state" / "seed_approvals.json"
HUB_EMPTY_STATES_PATH = CONFIG_DIR / "hub_empty_states.json"


def norm(value: Any) -> str:
    return str(value or "").strip()


def norm_upper(value: Any) -> str:
    return norm(value).upper()


def hub_path_from_slug(slug: str) -> str:
    return f"/{slug}.html" if slug else ""


def active_flag(row: dict[str, Any], default: bool = True) -> bool:
    value = row.get("active", default)
    return bool(value)


def load_registration_targets() -> dict[str, dict[str, Any]]:
    config = load_json(REGISTRATION_TARGETS_PATH)
    by_course: dict[str, dict[str, Any]] = {}
    for target in config.get("registration_targets", []):
        if not isinstance(target, dict):
            continue
        course_key = norm(target.get("course_key"))
        if course_key:
            by_course[course_key] = target
    return by_course


def load_seed_approval_count() -> int:
    if not SEED_APPROVALS_PATH.exists():
        return 0
    config = load_json(SEED_APPROVALS_PATH)
    return sum(1 for row in config.get("approvals", []) if isinstance(row, dict))


def load_empty_state_rules() -> dict[str, Any]:
    if not HUB_EMPTY_STATES_PATH.exists():
        return {
            "default_rules": {},
            "requestable_hub_keys": [],
            "hub_overrides": {},
        }
    return load_json(HUB_EMPTY_STATES_PATH)


def empty_state_rule(rules: dict[str, Any], rule_key: str) -> dict[str, Any]:
    default_rules = rules.get("default_rules") if isinstance(rules.get("default_rules"), dict) else {}
    rule = default_rules.get(rule_key) if isinstance(default_rules.get(rule_key), dict) else None
    if rule:
        return rule
    return {
        "empty_state_type": "needs_review",
        "headline": "Hub offer state needs review",
        "body": "The report could not determine a safe empty-state contract for this hub.",
        "recommended_cta_label": None,
        "recommended_cta_target": None,
    }


def decide_empty_state(
    hub: dict[str, Any],
    rules: dict[str, Any],
    current_count: int,
    approved_seed_count: int,
    needs_review_seed_count: int,
) -> dict[str, Any]:
    hub_key = norm(hub.get("hub_key"))
    overrides = rules.get("hub_overrides") if isinstance(rules.get("hub_overrides"), dict) else {}
    requestable = {
        norm(key)
        for key in rules.get("requestable_hub_keys", [])
        if norm(key)
    }
    caution_flags: list[str] = []
    if needs_review_seed_count:
        caution_flags.append("needs_review_seed_offers_exist")

    if current_count:
        rule = empty_state_rule(rules, "current_classes")
    elif approved_seed_count:
        rule = empty_state_rule(rules, "approved_seed_offers")
    elif isinstance(overrides.get(hub_key), dict):
        rule = overrides[hub_key]
        caution_flags.extend(str(flag) for flag in rule.get("caution_flags", []) if str(flag))
    elif hub_key in requestable:
        rule = empty_state_rule(rules, "requestable")
    elif not active_flag(hub, default=True):
        rule = empty_state_rule(rules, "suppress_hub_offer_block")
        caution_flags.append("inactive_hub")
    else:
        rule = empty_state_rule(rules, "needs_review")
        caution_flags.append("no_empty_state_rule")

    return {
        "has_current_enrollware_classes": current_count > 0,
        "has_approved_seed_offers": approved_seed_count > 0,
        "has_needs_review_seed_offers": needs_review_seed_count > 0,
        "empty_state_type": rule.get("empty_state_type") or "needs_review",
        "empty_state_headline": rule.get("headline") or "",
        "empty_state_body": rule.get("body") or "",
        "recommended_cta_label": rule.get("recommended_cta_label"),
        "recommended_cta_target": rule.get("recommended_cta_target"),
        "caution_flags": sorted(set(caution_flags)),
    }


def course_key_for_session(session: dict[str, Any], targets_by_course: dict[str, dict[str, Any]]) -> str | None:
    course = session.get("course") if isinstance(session.get("course"), dict) else {}
    course_id = norm(course.get("course_id") or course.get("course_number") or session.get("course_id"))
    code_hint = norm_upper(course.get("course_code_hint"))
    name = norm(course.get("mapped_clean_title") or course.get("course_name_primary_clean") or course.get("course_name_raw"))

    for course_key, target in targets_by_course.items():
        if course_id and course_id == norm(target.get("course_id")):
            return course_key

    code_map = {
        "AHA_BLS_IP_INITIAL": "aha_bls_initial",
        "AHA_BLS_IP_RENEWAL": "aha_bls_renewal",
        "AHA_BLS_BL_SKILLS": "aha_bls_heartcode_skills",
        "AHA_ACLS_BL_SKILLS": "aha_acls_heartcode_skills",
        "AHA_PALS_BL_SKILLS": "aha_pals_heartcode_skills",
        "AHA_HS_FA_CPR_AED": "aha_heartsaver_fa_cpr_aed",
    }
    if code_hint in code_map:
        return code_map[code_hint]

    lower_name = name.lower()
    if "bls" in lower_name and "renewal" in lower_name:
        return "aha_bls_renewal"
    if "bls" in lower_name and "heartcode" in lower_name:
        return "aha_bls_heartcode_skills"
    if "bls" in lower_name:
        return "aha_bls_initial"
    if "acls" in lower_name and "heartcode" in lower_name:
        return "aha_acls_heartcode_skills"
    if "pals" in lower_name and "heartcode" in lower_name:
        return "aha_pals_heartcode_skills"
    if "heartsaver" in lower_name or "first aid" in lower_name:
        return "aha_heartsaver_fa_cpr_aed"
    return None


def session_matches_tab(session: dict[str, Any], tab: dict[str, Any], targets_by_course: dict[str, dict[str, Any]]) -> bool:
    course = session.get("course") if isinstance(session.get("course"), dict) else {}
    session_code = norm_upper(course.get("course_code_hint"))
    session_course_id = norm(course.get("course_id") or course.get("course_number") or session.get("course_id"))
    session_name = norm(course.get("course_name_primary_clean") or course.get("course_name_raw") or course.get("mapped_clean_title"))
    session_name_lower = session_name.lower()

    tab_codes = {norm_upper(code) for code in tab.get("course_codes", []) if norm(code)}
    if session_code and session_code in tab_codes:
        return True

    for course_key, target in targets_by_course.items():
        if norm(target.get("course_id")) == session_course_id:
            if norm_upper(course_key) in tab_codes:
                return True

    includes = [norm(value).lower() for value in tab.get("name_contains", []) if norm(value)]
    excludes = [norm(value).lower() for value in tab.get("exclude_name_contains", []) if norm(value)]
    if includes and any(token in session_name_lower for token in includes):
        return not any(token in session_name_lower for token in excludes)
    return False


def load_hubs() -> list[dict[str, Any]]:
    hubs: list[dict[str, Any]] = []
    slug_config = load_json(SLUG_HUBS_PATH)
    for page in slug_config.get("pages", []):
        if not isinstance(page, dict):
            continue
        slug = norm(page.get("slug"))
        tabs = [tab for tab in page.get("tabs", []) if isinstance(tab, dict)]
        hubs.append(
            {
                "hub_key": slug,
                "hub_source": "slug_hubs",
                "title": page.get("title") or slug,
                "path": hub_path_from_slug(slug),
                "active": active_flag(page),
                "course_key": page.get("course_key"),
                "tabs": tabs,
                "fallback_message_if_empty": "No currently scheduled public offers are modeled for this hub yet. Students should use the current Enrollware-backed registration path.",
            }
        )

    seo_config = load_json(SEO_HUBS_PATH)
    for hub in seo_config.get("hubs", []):
        if not isinstance(hub, dict):
            continue
        hubs.append(
            {
                "hub_key": norm(hub.get("hub_key")),
                "hub_source": "seo_hubs",
                "title": hub.get("title") or hub.get("hub_key"),
                "path": hub.get("canonical_url"),
                "active": active_flag(hub, default=False),
                "course_key": hub.get("course_key"),
                "tabs": [],
                "fallback_message_if_empty": "This SEO hub would need either current Enrollware classes or approved hub-only seed offers before public display.",
            }
        )
    return hubs


def load_current_sessions(targets_by_course: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not SESSIONS_CURRENT_PATH.exists():
        return {
            "source_available": False,
            "source_path": str(SESSIONS_CURRENT_PATH),
            "generated_at": None,
            "sessions": [],
            "warning": "Current Enrollware source data is unavailable.",
        }
    config = load_json(SESSIONS_CURRENT_PATH)
    now = datetime.now(TZ)
    sessions: list[dict[str, Any]] = []
    for session in config.get("sessions", []):
        if not isinstance(session, dict):
            continue
        start_dt = parse_dt(session.get("start_datetime") or session.get("start"))
        if not start_dt or start_dt < now:
            continue
        course = session.get("course") if isinstance(session.get("course"), dict) else {}
        course_key = course_key_for_session(session, targets_by_course)
        sessions.append(
            {
                "display_item_type": "current_enrollware_class",
                "session_id": session.get("session_id"),
                "course_key": course_key,
                "course_title": course.get("mapped_clean_title") or course.get("course_name_primary_clean") or course.get("course_name_raw") or course_title(course_key or ""),
                "course_id": course.get("course_id") or course.get("course_number") or session.get("course_id"),
                "course_code_hint": course.get("course_code_hint"),
                "start_datetime": start_dt.isoformat(),
                "end_datetime": (parse_dt(session.get("end_datetime") or session.get("end")) or start_dt).isoformat(),
                "date": start_dt.date().isoformat(),
                "start_time": format_time(start_dt.isoformat()),
                "end_time": format_time((parse_dt(session.get("end_datetime") or session.get("end")) or start_dt).isoformat()),
                "location": session.get("location") or session.get("location_name") or session.get("location_key"),
                "instructor": session.get("instructor") or session.get("instructor_name"),
                "reason": "Current future session exists in data/sessions_current.json.",
            }
        )
    build = config.get("build") if isinstance(config.get("build"), dict) else {}
    return {
        "source_available": True,
        "source_path": str(SESSIONS_CURRENT_PATH),
        "generated_at": build.get("generated_at"),
        "sessions": sessions,
        "warning": None,
    }


def seed_display_classification(seed: dict[str, Any]) -> tuple[str, str]:
    if seed.get("registration_target_key") in (None, ""):
        return "suppressed_missing_registration_target", "Seed has no registration target key."
    if seed.get("approval_status") == "approved_for_public":
        if (
            seed.get("publishability_status") == "publishable_candidate"
            and seed.get("public_ready") is True
            and seed.get("enrollware_presence_status") == "present_in_enrollware"
        ):
            return "approved_seed_offer", "Approved for public hub-offer review; not a class lander."
        if seed.get("enrollware_presence_status") != "present_in_enrollware":
            return (
                "suppressed_approved_but_not_public_ready",
                "Approved but missing Enrollware presence; hub preview display is blocked.",
            )
        if seed.get("public_ready") is not True:
            return (
                "suppressed_approved_but_not_public_ready",
                "Approved but public_ready is false; hub preview display is blocked.",
            )
        return "suppressed_missing_registration_target", "Approved seed is not publishable because registration/publishability gate failed."
    if seed.get("approval_status") == "needs_review":
        return "needs_review_seed_offer", "Seed is publishable in config but still needs operator approval."
    return "suppressed_not_approved", f"Seed approval status is {seed.get('approval_status') or 'unknown'}."


def hub_matches_seed(hub: dict[str, Any], seed: dict[str, Any]) -> bool:
    seed_course_key = norm(seed.get("course_key"))
    if hub.get("course_key") and norm(hub.get("course_key")) == seed_course_key:
        return True
    path = norm(hub.get("path")).lower()
    title = norm(hub.get("title")).lower()
    course = seed_course_key.lower()
    if "bls" in course and ("bls" in path or "bls" in title):
        return True
    if "acls" in course and ("acls" in path or "acls" in title):
        return True
    if "pals" in course and ("pals" in path or "pals" in title):
        return True
    if "heartsaver" in course and ("heartsaver" in path or "heartsaver" in title or "first-aid" in path):
        return True
    return False


def hub_matches_session(hub: dict[str, Any], session: dict[str, Any], targets_by_course: dict[str, dict[str, Any]]) -> bool:
    if hub.get("course_key") and norm(hub.get("course_key")) == norm(session.get("course_key")):
        return True
    for tab in hub.get("tabs", []):
        if session_matches_tab({"course": {"course_code_hint": session.get("course_code_hint"), "course_id": session.get("course_id"), "course_name_primary_clean": session.get("course_title")}}, tab, targets_by_course):
            return True
    path = norm(hub.get("path")).lower()
    title = norm(hub.get("title")).lower()
    course_key = norm(session.get("course_key")).lower()
    if "bls" in course_key and ("bls" in path or "bls" in title):
        return True
    if "acls" in course_key and ("acls" in path or "acls" in title):
        return True
    if "pals" in course_key and ("pals" in path or "pals" in title):
        return True
    if "heartsaver" in course_key and ("heartsaver" in path or "heartsaver" in title):
        return True
    return False


def build_report(source_mode: str) -> dict[str, Any]:
    targets_by_course = load_registration_targets()
    empty_state_rules = load_empty_state_rules()
    hubs = load_hubs()
    sessions_source = load_current_sessions(targets_by_course)
    seed_export = build_export(source_mode)
    seeds = seed_export.get("publishable_seed_candidates", [])

    hub_reports: list[dict[str, Any]] = []
    suppressed_counter: Counter[str] = Counter()
    display_counter: Counter[str] = Counter()

    for hub in hubs:
        current_classes = [
            session
            for session in sessions_source["sessions"]
            if hub_matches_session(hub, session, targets_by_course)
        ]
        approved_seed_offers: list[dict[str, Any]] = []
        needs_review_seed_offers: list[dict[str, Any]] = []
        suppressed_seed_offers: list[dict[str, Any]] = []

        for seed in seeds:
            if not hub_matches_seed(hub, seed):
                continue
            classification, reason = seed_display_classification(seed)
            display_seed = {
                "display_item_type": classification,
                "seed_id": seed.get("seed_id"),
                "course_key": seed.get("course_key"),
                "course_title": seed.get("course_title"),
                "instructor_key": seed.get("instructor_key"),
                "start_datetime": seed.get("start_datetime"),
                "end_datetime": seed.get("end_datetime"),
                "date": seed.get("date"),
                "start_time": seed.get("start_time"),
                "end_time": seed.get("end_time"),
                "location_key": seed.get("location_key"),
                "registration_target_key": seed.get("registration_target_key"),
                "approval_status": seed.get("approval_status"),
                "publishability_status": seed.get("publishability_status"),
                "enrollware_presence_status": seed.get("enrollware_presence_status"),
                "public_ready": seed.get("public_ready"),
                "public_ready_block_reason": seed.get("public_ready_block_reason"),
                "reason": reason,
                "hub_display_note": "Hub offer only; do not create a standalone class lander from this seed.",
            }
            if classification == "approved_seed_offer":
                approved_seed_offers.append(display_seed)
            elif classification == "needs_review_seed_offer":
                needs_review_seed_offers.append(display_seed)
            else:
                suppressed_seed_offers.append(display_seed)
                suppressed_counter[classification] += 1
            display_counter[classification] += 1

        if not sessions_source["source_available"]:
            suppressed_counter["suppressed_missing_enrollware"] += 1

        empty_state = decide_empty_state(
            hub,
            empty_state_rules,
            len(current_classes),
            len(approved_seed_offers),
            len(needs_review_seed_offers),
        )
        hub_empty = not current_classes and not approved_seed_offers and not needs_review_seed_offers
        hub_reports.append(
            {
                "hub_key": hub["hub_key"],
                "hub_source": hub["hub_source"],
                "hub_path": hub.get("path"),
                "title": hub.get("title"),
                "active": hub.get("active"),
                "course_key": hub.get("course_key"),
                "current_enrollware_classes": current_classes[:25],
                "current_enrollware_class_count": len(current_classes),
                "approved_seed_offers": approved_seed_offers,
                "approved_seed_offer_count": len(approved_seed_offers),
                "needs_review_seed_offers": needs_review_seed_offers,
                "needs_review_seed_offer_count": len(needs_review_seed_offers),
                "blocked_suppressed_seed_offers": suppressed_seed_offers,
                "blocked_suppressed_seed_offer_count": len(suppressed_seed_offers),
                "would_appear_empty": hub_empty,
                "fallback_message_if_empty": hub["fallback_message_if_empty"] if hub_empty else None,
                **empty_state,
            }
        )

    empty_state_counts = Counter(str(hub.get("empty_state_type") or "needs_review") for hub in hub_reports)
    summary = {
        "hubs_checked": len(hub_reports),
        "hubs_with_current_enrollware_classes": sum(1 for hub in hub_reports if hub["current_enrollware_class_count"] > 0),
        "hubs_with_approved_seed_offers": sum(1 for hub in hub_reports if hub["approved_seed_offer_count"] > 0),
        "hubs_with_needs_review_seed_offers": sum(1 for hub in hub_reports if hub["needs_review_seed_offer_count"] > 0),
        "hubs_empty": sum(1 for hub in hub_reports if hub["would_appear_empty"]),
        "approved_but_not_public_ready": suppressed_counter.get("suppressed_approved_but_not_public_ready", 0),
        "suppressed_approved_but_not_public_ready": suppressed_counter.get("suppressed_approved_but_not_public_ready", 0),
        "hubs_using_current_classes": empty_state_counts.get("show_current_classes", 0),
        "hubs_using_approved_seed_offers": empty_state_counts.get("show_approved_seed_offers", 0),
        "hubs_using_request_cta": empty_state_counts.get("show_request_class_cta", 0),
        "hubs_using_call_to_schedule": empty_state_counts.get("show_call_to_schedule", 0),
        "hubs_needs_review": empty_state_counts.get("needs_review", 0),
        "hubs_suppressing_offer_block": empty_state_counts.get("suppress_hub_offer_block", 0),
        "empty_state_type_counts": dict(sorted(empty_state_counts.items())),
        "suppressed_offers_by_reason": dict(sorted(suppressed_counter.items())),
        "seed_display_item_counts": dict(sorted(display_counter.items())),
        "current_enrollware_classes_matched_to_hubs": sum(hub["current_enrollware_class_count"] for hub in hub_reports),
        "approved_seed_offers_matched_to_hubs": sum(hub["approved_seed_offer_count"] for hub in hub_reports),
        "needs_review_seed_offers_matched_to_hubs": sum(hub["needs_review_seed_offer_count"] for hub in hub_reports),
    }
    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "source_mode": source_mode,
        "inputs": {
            "current_enrollware_source": sessions_source["source_path"],
            "current_enrollware_source_available": sessions_source["source_available"],
            "current_enrollware_generated_at": sessions_source["generated_at"],
            "publishable_seed_pipeline": "scripts/build_publishable_seed_candidates.py",
            "seo_hubs": str(SEO_HUBS_PATH),
            "slug_hubs": str(SLUG_HUBS_PATH),
            "registration_targets": str(REGISTRATION_TARGETS_PATH),
            "seed_approvals": str(SEED_APPROVALS_PATH),
            "hub_empty_states": str(HUB_EMPTY_STATES_PATH),
            "seed_approval_count": load_seed_approval_count(),
        },
        "rules": {
            "current_enrollware_classes": "May appear as class/session offers when present in current Enrollware source data.",
            "approved_seed_offers": "May appear only as hub offers after approved_for_public; they do not create standalone class landers.",
            "unapproved_seed_offers": "Remain needs-review or suppressed and do not become public.",
            "report_only": "This report does not modify public pages, CTAs, Enrollware links, class landers, or schedule files.",
        },
        "summary": summary,
        "hubs": sorted(hub_reports, key=lambda hub: (str(hub.get("hub_source")), str(hub.get("hub_key")))),
        "seed_export_summary": seed_export.get("summary", {}),
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Hub Offer Model Report",
        "",
        "> REPORT ONLY - NO PUBLIC PAGES, CTAS, ENROLLWARE LINKS, OR CLASS LANDERS MODIFIED",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Source mode: {report['source_mode']}",
        f"- Current Enrollware source: {report['inputs']['current_enrollware_source']}",
        f"- Current Enrollware source available: {report['inputs']['current_enrollware_source_available']}",
        f"- Hubs checked: {report['summary']['hubs_checked']}",
        f"- Hubs with current Enrollware classes: {report['summary']['hubs_with_current_enrollware_classes']}",
        f"- Hubs with approved seed offers: {report['summary']['hubs_with_approved_seed_offers']}",
        f"- Hubs with needs-review seed offers: {report['summary']['hubs_with_needs_review_seed_offers']}",
        f"- Hubs empty: {report['summary']['hubs_empty']}",
        f"- Approved but not public ready: {report['summary']['approved_but_not_public_ready']}",
        f"- Hubs using current classes: {report['summary']['hubs_using_current_classes']}",
        f"- Hubs using approved seed offers: {report['summary']['hubs_using_approved_seed_offers']}",
        f"- Hubs using request CTA: {report['summary']['hubs_using_request_cta']}",
        f"- Hubs using call-to-schedule: {report['summary']['hubs_using_call_to_schedule']}",
        f"- Hubs needs review: {report['summary']['hubs_needs_review']}",
        f"- Hubs suppressing offer block: {report['summary']['hubs_suppressing_offer_block']}",
        f"- Empty-state type counts: {json.dumps(report['summary']['empty_state_type_counts'], sort_keys=True)}",
        f"- Suppressed offers by reason: {json.dumps(report['summary']['suppressed_offers_by_reason'], sort_keys=True)}",
        "",
        "## Display Contract",
        "",
        "- `current_enrollware_class`: real future Enrollware-backed class/session that can be modeled as a hub class offer.",
        "- `approved_seed_offer`: report-only generated availability approved for public hub display; hub offer only, not a class lander.",
        "- `needs_review_seed_offer`: generated availability with a valid publishable target but no public approval yet.",
        "- `suppressed_approved_but_not_public_ready`: seed is approved, but public_ready or current Enrollware presence blocks display.",
        "- `suppressed_missing_enrollware`: Enrollware source is unavailable for validation.",
        "- `suppressed_not_approved`: seed exists but approval state blocks public display.",
        "- `suppressed_missing_registration_target`: seed lacks a valid registration target/publishability gate.",
        "",
        "## Empty-State Contract",
        "",
        "- `show_current_classes`: current Enrollware-backed classes exist; show the normal class/session offer block.",
        "- `show_approved_seed_offers`: no current classes, but approved hub-only seed offers are available.",
        "- `show_request_class_cta`: no modeled offers; show a request-class path instead of fake dates.",
        "- `show_call_to_schedule`: professional available-by-request/contact message.",
        "- `show_check_back_soon`: neutral fallback when a public offer block is still appropriate.",
        "- `suppress_hub_offer_block`: hide the offer block until real/approved offers exist.",
        "- `needs_review`: no safe fallback rule was found.",
        "",
        "## Hubs",
        "",
    ]

    for hub in report["hubs"]:
        lines.append(f"### {hub['hub_key']} ({hub['hub_source']})")
        lines.append(f"- Path: {hub.get('hub_path')}")
        lines.append(f"- Course key: {hub.get('course_key')}")
        lines.append(f"- Current Enrollware classes: {hub['current_enrollware_class_count']}")
        lines.append(f"- Approved seed offers: {hub['approved_seed_offer_count']}")
        lines.append(f"- Needs-review seed offers: {hub['needs_review_seed_offer_count']}")
        lines.append(f"- Suppressed seed offers: {hub['blocked_suppressed_seed_offer_count']}")
        lines.append(f"- Would appear empty: {hub['would_appear_empty']}")
        lines.append(f"- Empty-state type: {hub['empty_state_type']}")
        lines.append(f"- Empty-state headline: {hub['empty_state_headline']}")
        lines.append(f"- Empty-state body: {hub['empty_state_body']}")
        lines.append(f"- Recommended CTA: {hub['recommended_cta_label']} -> {hub['recommended_cta_target']}")
        lines.append(f"- Caution flags: {', '.join(hub['caution_flags']) if hub['caution_flags'] else 'none'}")
        if hub["fallback_message_if_empty"]:
            lines.append(f"- Empty fallback message: {hub['fallback_message_if_empty']}")

        for item in hub["current_enrollware_classes"][:5]:
            lines.append(f"  - Current: {item.get('date')} {item.get('start_time')} - {item.get('course_title')} (session {item.get('session_id')})")
        for item in hub["approved_seed_offers"][:5]:
            lines.append(f"  - Approved seed: {item.get('date')} {item.get('start_time')} - {item.get('course_title')} ({item.get('seed_id')})")
        for item in hub["needs_review_seed_offers"][:5]:
            lines.append(f"  - Needs review seed: {item.get('date')} {item.get('start_time')} - {item.get('course_title')} ({item.get('seed_id')})")
        for item in hub["blocked_suppressed_seed_offers"][:5]:
            lines.append(f"  - Suppressed: {item.get('display_item_type')} - {item.get('course_title')} - {item.get('reason')}")
            if item.get("public_ready_block_reason"):
                lines.append(f"    - Public-ready block: {item.get('public_ready_block_reason')}")
        lines.append("")

    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build report-only hub offer ingestion/display contract.")
    parser.add_argument("--source", choices=sorted(SOURCE_MODES), default="auto", help="Seed calendar source mode.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.source)
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print("Hub offer model report generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
