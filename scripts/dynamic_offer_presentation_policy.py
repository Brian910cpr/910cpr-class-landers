from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


from scripts.local_data_paths import public_sellable_offers_preview_path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
PUBLIC_SELLABLE_OFFERS_PATH = public_sellable_offers_preview_path(ROOT)
SCHEDULE_FUTURE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
PRESENTATION_JSON_PATH = AUDIT_DIR / "dynamic_offer_presentation_policy_report.json"
PRESENTATION_MD_PATH = AUDIT_DIR / "dynamic_offer_presentation_policy_report.md"
UNKNOWN = "UNKNOWN"
DEFAULT_FLEXIBLE_START_BUTTON_TEXT = "When would YOU like to start?"


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", clean_text(value).lower()).strip("_")


def parse_dt(value: Any) -> datetime | None:
    text = clean_text(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def offer_start(offer: dict[str, Any]) -> datetime | None:
    return parse_dt(offer.get("appointment_display_start") or offer.get("start_datetime"))


def offer_end(offer: dict[str, Any]) -> datetime | None:
    return parse_dt(offer.get("appointment_display_end") or offer.get("end_datetime"))


def offer_consumption_start(offer: dict[str, Any]) -> datetime | None:
    return parse_dt(offer.get("scheduler_consumption_start") or offer.get("appointment_display_start") or offer.get("start_datetime"))


def offer_consumption_end(offer: dict[str, Any]) -> datetime | None:
    return parse_dt(offer.get("scheduler_consumption_end") or offer.get("appointment_display_end") or offer.get("end_datetime"))


def iso(dt: datetime | None) -> str:
    return dt.isoformat() if dt else UNKNOWN


def compact_time(dt: datetime | None) -> str:
    return dt.strftime("%H:%M") if dt else UNKNOWN


def availability_group_key(offer: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        clean_text(offer.get("source_availability_window") or UNKNOWN),
        clean_text(offer.get("date") or UNKNOWN),
        normalize_key(offer.get("instructor_person_id") or offer.get("instructor_display_name") or UNKNOWN),
        normalize_key(offer.get("offer_location") or offer.get("location") or UNKNOWN),
    )


def course_window_key(offer: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (*availability_group_key(offer), clean_text(offer.get("course_id") or UNKNOWN))


def normalize_location(value: Any) -> str:
    text = clean_text(value).lower()
    text = text.replace(";", " ")
    text = re.sub(r"\broom\s+[a-z0-9]+\b", "", text)
    return normalize_key(text)


def session_blocks(schedule_payload: Any) -> list[dict[str, Any]]:
    sessions = schedule_payload.get("sessions", []) if isinstance(schedule_payload, dict) else []
    blocks = []
    for session in sessions:
        if not isinstance(session, dict):
            continue
        start = parse_dt(session.get("start_at") or session.get("start") or session.get("start_datetime"))
        end = parse_dt(session.get("end_at") or session.get("end") or session.get("end_datetime"))
        if not start or not end:
            continue
        blocks.append({
            "session_id": clean_text(session.get("session_id") or session.get("class_id") or UNKNOWN),
            "course_id": clean_text(session.get("course_id") or session.get("course_number") or UNKNOWN),
            "course_title": clean_text(session.get("official_course_name") or session.get("course_name") or session.get("raw_course_name") or UNKNOWN),
            "start": start,
            "end": end,
            "instructor": clean_text(session.get("lead_instructor_name") or session.get("instructor") or UNKNOWN),
            "location": clean_text(session.get("location_name") or session.get("location_display") or session.get("location") or UNKNOWN),
            "source": "docs/data/schedule_future.json",
        })
    return blocks


def matching_anchors(group_offers: list[dict[str, Any]], anchors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    starts = [offer_consumption_start(offer) for offer in group_offers]
    ends = [offer_consumption_end(offer) for offer in group_offers]
    starts = [value for value in starts if value]
    ends = [value for value in ends if value]
    if not starts or not ends:
        return []
    sample = group_offers[0]
    instructor_name = normalize_key(sample.get("instructor_display_name"))
    location = normalize_location(sample.get("offer_location") or sample.get("location"))
    offer_dates = {clean_text(offer.get("date")) for offer in group_offers if clean_text(offer.get("date"))}
    matched = []
    for anchor in anchors:
        same_instructor = instructor_name and normalize_key(anchor.get("instructor")) == instructor_name
        same_location = location and normalize_location(anchor.get("location")) == location
        same_date = anchor["start"].date().isoformat() in offer_dates or anchor["end"].date().isoformat() in offer_dates
        if same_instructor and same_location and same_date:
            matched.append(anchor)
    return sorted(matched, key=lambda item: item["start"])


def anchor_summary(anchor: dict[str, Any] | None) -> dict[str, Any] | None:
    if not anchor:
        return None
    return {
        "session_id": anchor.get("session_id", UNKNOWN),
        "course_id": anchor.get("course_id", UNKNOWN),
        "course_title": anchor.get("course_title", UNKNOWN),
        "start": iso(anchor.get("start")),
        "end": iso(anchor.get("end")),
        "instructor": anchor.get("instructor", UNKNOWN),
        "location": anchor.get("location", UNKNOWN),
        "source": anchor.get("source", UNKNOWN),
    }


def choose_anchor_stack_offer(offers: list[dict[str, Any]], anchors: list[dict[str, Any]]) -> tuple[str, dict[str, Any] | None, dict[str, Any] | None, str]:
    candidates: list[tuple[int, int, datetime, dict[str, Any], dict[str, Any], str]] = []
    for offer in offers:
        start = offer_consumption_start(offer)
        end = offer_consumption_end(offer)
        if not start or not end or end <= start:
            continue
        try:
            reset_after_anchor_minutes = int(offer.get("setup_buffer_minutes", 15) or 15)
        except (TypeError, ValueError):
            reset_after_anchor_minutes = 15
        for anchor in anchors:
            gap_before = int((anchor["start"] - end).total_seconds() // 60)
            if gap_before >= 0:
                candidates.append((gap_before, 0, start, offer, anchor, "anchor_stack_before"))
            gap_after = int((start - anchor["end"]).total_seconds() // 60)
            if gap_after >= reset_after_anchor_minutes:
                candidates.append((gap_after, 1, start, offer, anchor, "anchor_stack_after"))
    if not candidates:
        return "suppressed_invalid", None, anchors[0] if anchors else None, "No candidate fits before or after the anchor with its scheduler consumption window."
    _gap, _side_rank, _start, offer, anchor, mode = sorted(candidates, key=lambda item: (item[0], item[1], item[2], clean_text(item[3].get("offer_id"))))[0]
    return mode, offer, anchor, "Selected closest non-overlapping stack fit next to anchor."


def choice_from_offer(offer: dict[str, Any]) -> dict[str, Any]:
    return {
        "offer_id": offer.get("offer_id", UNKNOWN),
        "start_time": offer.get("start_time", compact_time(offer_start(offer))),
        "end_time": offer.get("end_time", compact_time(offer_end(offer))),
        "appointment_display_start": iso(offer_start(offer)),
        "appointment_display_end": iso(offer_end(offer)),
        "scheduler_consumption_start": iso(offer_consumption_start(offer)),
        "scheduler_consumption_end": iso(offer_consumption_end(offer)),
        "appointmentDayId": offer.get("appointmentDayId"),
    }


def audit_row(
    offer: dict[str, Any],
    *,
    group_start: datetime | None,
    group_end: datetime | None,
    anchor_exists: bool,
    nearest_anchor: dict[str, Any] | None,
    presentation_mode: str,
    public_render_decision: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "offer_id": offer.get("offer_id", UNKNOWN),
        "course_key": offer.get("course_key", UNKNOWN),
        "courseId": offer.get("course_id", UNKNOWN),
        "instructor_id": offer.get("instructor_person_id", UNKNOWN),
        "instructor_name": offer.get("instructor_display_name", UNKNOWN),
        "location": offer.get("offer_location") or offer.get("location") or UNKNOWN,
        "availability_block_start": iso(group_start),
        "availability_block_end": iso(group_end),
        "candidate_start": iso(offer_start(offer)),
        "candidate_end": iso(offer_end(offer)),
        "scheduler_consumption_start": iso(offer_consumption_start(offer)),
        "scheduler_consumption_end": iso(offer_consumption_end(offer)),
        "anchor_class_exists_in_window": anchor_exists,
        "nearest_anchor_class": anchor_summary(nearest_anchor),
        "presentation_mode": presentation_mode,
        "public_render_decision": public_render_decision,
        "reason": reason,
    }


def apply_presentation_policy(public_offers: list[dict[str, Any]], anchors: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    offers = [offer for offer in public_offers if isinstance(offer, dict)]
    by_window: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for offer in offers:
        by_window[availability_group_key(offer)].append(offer)

    window_anchors = {key: matching_anchors(group, anchors) for key, group in by_window.items()}
    by_course_window: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for offer in offers:
        by_course_window[course_window_key(offer)].append(offer)

    audit_rows: list[dict[str, Any]] = []
    render_offers: list[dict[str, Any]] = []
    for key, group in sorted(by_course_window.items()):
        sorted_group = sorted(group, key=lambda item: (offer_start(item) or datetime.max, clean_text(item.get("offer_id"))))
        starts = [offer_consumption_start(offer) for offer in sorted_group]
        ends = [offer_consumption_end(offer) for offer in sorted_group]
        starts = [value for value in starts if value]
        ends = [value for value in ends if value]
        group_start = min(starts) if starts else None
        group_end = max(ends) if ends else None
        anchors_for_window = window_anchors.get(key[:4], [])
        anchor_exists = bool(anchors_for_window)
        if anchor_exists:
            selected_mode, selected, nearest_anchor, reason = choose_anchor_stack_offer(sorted_group, anchors_for_window)
            if selected is None:
                for offer in sorted_group:
                    audit_rows.append(audit_row(
                        offer,
                        group_start=group_start,
                        group_end=group_end,
                        anchor_exists=True,
                        nearest_anchor=nearest_anchor,
                        presentation_mode="suppressed_invalid",
                        public_render_decision="suppress_invalid",
                        reason=reason,
                    ))
                continue
            selected_id = selected.get("offer_id")
            render_offers.append({
                **selected,
                "presentation_mode": selected_mode,
                "public_render_decision": "render_single_stack_offer",
                "nearest_anchor_class": anchor_summary(nearest_anchor),
                "suppressed_adjacent_offer_ids": [
                    offer.get("offer_id", UNKNOWN)
                    for offer in sorted_group
                    if offer.get("offer_id") != selected_id
                ],
                "render_source": "dynamic_offer_presentation_policy",
            })
            for offer in sorted_group:
                if offer.get("offer_id") == selected_id:
                    audit_rows.append(audit_row(
                        offer,
                        group_start=group_start,
                        group_end=group_end,
                        anchor_exists=True,
                        nearest_anchor=nearest_anchor,
                        presentation_mode=selected_mode,
                        public_render_decision="render_single_stack_offer",
                        reason=reason,
                    ))
                else:
                    audit_rows.append(audit_row(
                        offer,
                        group_start=group_start,
                        group_end=group_end,
                        anchor_exists=True,
                        nearest_anchor=nearest_anchor,
                        presentation_mode="suppressed_adjacent_candidate",
                        public_render_decision="suppress_as_duplicate_adjacent_start",
                        reason="Suppressed because another candidate in this course/window fits the anchor more tightly.",
                    ))
            continue

        valid_choices = [
            offer for offer in sorted_group
            if offer_consumption_start(offer) and offer_consumption_end(offer) and offer_consumption_end(offer) > offer_consumption_start(offer)
        ]
        if not valid_choices:
            for offer in sorted_group:
                audit_rows.append(audit_row(
                    offer,
                    group_start=group_start,
                    group_end=group_end,
                    anchor_exists=False,
                    nearest_anchor=None,
                    presentation_mode="suppressed_invalid",
                    public_render_decision="suppress_invalid",
                    reason="Candidate has invalid or missing scheduler consumption times.",
                ))
            continue
        representative = valid_choices[0]
        latest_start = max((offer_consumption_start(offer) for offer in valid_choices if offer_consumption_start(offer)), default=None)
        render_offers.append({
            **representative,
            "presentation_mode": "flexible_start_window",
            "public_render_decision": "render_flexible_start_button",
            "flexible_start_button_text": DEFAULT_FLEXIBLE_START_BUTTON_TEXT,
            "flexible_start_choices": [choice_from_offer(offer) for offer in valid_choices],
            "latest_flexible_start": iso(latest_start),
            "suppressed_adjacent_offer_ids": [
                offer.get("offer_id", UNKNOWN)
                for offer in sorted_group
                if offer.get("offer_id") != representative.get("offer_id")
            ],
            "render_source": "dynamic_offer_presentation_policy",
        })
        for offer in sorted_group:
            if offer.get("offer_id") == representative.get("offer_id"):
                audit_rows.append(audit_row(
                    offer,
                    group_start=group_start,
                    group_end=group_end,
                    anchor_exists=False,
                    nearest_anchor=None,
                    presentation_mode="flexible_start_window",
                    public_render_decision="render_flexible_start_button",
                    reason="Open availability window compacted to one flexible-start public offer.",
                ))
            else:
                audit_rows.append(audit_row(
                    offer,
                    group_start=group_start,
                    group_end=group_end,
                    anchor_exists=False,
                    nearest_anchor=None,
                    presentation_mode="suppressed_adjacent_candidate",
                    public_render_decision="suppress_as_duplicate_adjacent_start",
                    reason="Suppressed because this course/window is represented by a flexible-start offer.",
                ))

    stats = {
        "public_sellable_dynamic_candidates": len(offers),
        "rendered_anchor_stack_offers": sum(1 for offer in render_offers if str(offer.get("presentation_mode", "")).startswith("anchor_stack")),
        "rendered_flexible_start_windows": sum(1 for offer in render_offers if offer.get("presentation_mode") == "flexible_start_window"),
        "suppressed_adjacent_duplicates": sum(1 for row in audit_rows if row.get("presentation_mode") == "suppressed_adjacent_candidate"),
        "suppressed_invalid": sum(1 for row in audit_rows if row.get("presentation_mode") == "suppressed_invalid"),
        "presentation_modes": dict(Counter(row["presentation_mode"] for row in audit_rows).most_common()),
        "public_render_decisions": dict(Counter(row["public_render_decision"] for row in audit_rows).most_common()),
    }
    return render_offers, audit_rows, stats


def render_markdown(stats: dict[str, Any], audit_rows: list[dict[str, Any]], render_offers: list[dict[str, Any]]) -> str:
    lines = [
        "# Dynamic Offer Presentation Policy Report",
        "",
        "Read-only audit for public presentation compaction. Internal dynamic candidates are preserved upstream; this report classifies which candidates should render publicly.",
        "",
        "## Summary",
        "",
        f"- Public sellable dynamic candidates: {stats['public_sellable_dynamic_candidates']}",
        f"- Rendered anchor-stack offers: {stats['rendered_anchor_stack_offers']}",
        f"- Rendered flexible-start windows: {stats['rendered_flexible_start_windows']}",
        f"- Suppressed adjacent duplicates: {stats['suppressed_adjacent_duplicates']}",
        f"- Suppressed invalid: {stats['suppressed_invalid']}",
        "",
        "## Presentation Modes",
        "",
    ]
    lines.extend(f"- `{key}`: {value}" for key, value in stats["presentation_modes"].items())
    lines.extend(["", "## Rendered Public Offer Examples", ""])
    if render_offers:
        lines.extend(["| Mode | Date | Time | Course | Instructor | Choices | Source Offer |", "| --- | --- | --- | --- | --- | ---: | --- |"])
        for offer in render_offers[:100]:
            lines.append(
                f"| `{offer.get('presentation_mode', UNKNOWN)}` | {offer.get('date', UNKNOWN)} | {offer.get('start_time', UNKNOWN)} | "
                f"{offer.get('course_title', UNKNOWN)} | {offer.get('instructor_display_name', UNKNOWN)} | "
                f"{len(offer.get('flexible_start_choices', []) or [])} | `{offer.get('offer_id', UNKNOWN)}` |"
            )
    else:
        lines.append("- None")
    lines.extend(["", "## Suppressed Adjacent Examples", ""])
    suppressed = [row for row in audit_rows if row.get("presentation_mode") == "suppressed_adjacent_candidate"]
    if suppressed:
        lines.extend(["| Offer | Course | Candidate | Reason |", "| --- | --- | --- | --- |"])
        for row in suppressed[:100]:
            lines.append(
                f"| `{row.get('offer_id', UNKNOWN)}` | {row.get('courseId', UNKNOWN)} | "
                f"{row.get('candidate_start', UNKNOWN)} | {row.get('reason', UNKNOWN)} |"
            )
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def build_report(public_preview: Any, schedule_payload: Any) -> dict[str, Any]:
    offers = public_preview.get("offers", []) if isinstance(public_preview, dict) else []
    render_offers, audit_rows, stats = apply_presentation_policy(offers, session_blocks(schedule_payload))
    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "read_only": True,
        "public_site_affected": False,
        "enrollware_called": False,
        "appointments_created": False,
        "source_public_sellable_offers": str(PUBLIC_SELLABLE_OFFERS_PATH),
        "source_schedule_future": str(SCHEDULE_FUTURE_PATH),
        "button_text_default": DEFAULT_FLEXIBLE_START_BUTTON_TEXT,
        "stats": stats,
        "render_offers": render_offers,
        "audit_rows": audit_rows,
    }


def run() -> dict[str, Any]:
    report = build_report(read_json(PUBLIC_SELLABLE_OFFERS_PATH), read_json(SCHEDULE_FUTURE_PATH))
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    PRESENTATION_JSON_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    PRESENTATION_MD_PATH.write_text(render_markdown(report["stats"], report["audit_rows"], report["render_offers"]), encoding="utf-8")
    return report


def main() -> int:
    report = run()
    stats = report["stats"]
    print("Dynamic offer presentation policy complete (READ ONLY).")
    print("No deployment, Enrollware calls, appointments, or internal candidate generation changes were made.")
    print(f"Public sellable dynamic candidates: {stats['public_sellable_dynamic_candidates']}")
    print(f"Rendered anchor-stack offers: {stats['rendered_anchor_stack_offers']}")
    print(f"Rendered flexible-start windows: {stats['rendered_flexible_start_windows']}")
    print(f"Suppressed adjacent duplicates: {stats['suppressed_adjacent_duplicates']}")
    print(f"Suppressed invalid: {stats['suppressed_invalid']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
