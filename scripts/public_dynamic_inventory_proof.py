from __future__ import annotations

import html
import json
import re
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote_plus, urlparse

from scripts import public_offer_integrity_audit as integrity


from scripts.local_data_paths import dynamic_offers_preview_path, public_sellable_offers_preview_path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
DOCS_DIR = ROOT / "docs"

PUBLIC_SELLABLE_OFFERS_PATH = public_sellable_offers_preview_path(ROOT)
DYNAMIC_OFFERS_PATH = dynamic_offers_preview_path(ROOT)
SEED_URL_PREVIEW_PATH = AUDIT_DIR / "seed_appointment_url_preview.json"
SCHEDULE_FUTURE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
SESSIONS_CURRENT_PATH = ROOT / "data" / "sessions_current.json"
LIVE_AVAILABILITY_PATH = AUDIT_DIR / "live_availability_snapshot_preview.json"
LEGACY_AVAILABILITY_PATH = ROOT / "data" / "inventory" / "instructor_availability.json"

REPORT_MD_PATH = AUDIT_DIR / "public_dynamic_inventory_proof.md"
REPORT_JSON_PATH = AUDIT_DIR / "public_dynamic_inventory_proof.json"

PUBLIC_HUB_PAGE_PATHS = [
    DOCS_DIR / "bls.html",
    DOCS_DIR / "acls.html",
    DOCS_DIR / "pals.html",
    DOCS_DIR / "heartsaver.html",
    DOCS_DIR / "arc.html",
    DOCS_DIR / "hsi.html",
    DOCS_DIR / "uscg-elementary-first-aid-cpr.html",
    DOCS_DIR / "classes" / "index.html",
]

UNKNOWN = "UNKNOWN"


def read_json(path: Path) -> tuple[Any | None, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"invalid_json: {exc}"
    except OSError as exc:
        return None, f"read_error: {exc}"


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", clean_text(value).lower()).strip("_")


def parse_dt(value: Any) -> datetime | None:
    return integrity.parse_dt(value)


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


class AppointmentCardParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cards: list[dict[str, Any]] = []
        self._active: dict[str, Any] | None = None
        self._depth = 0
        self._link_depth = 0
        self._link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {name: value or "" for name, value in attrs}
        classes = set(attr.get("class", "").split())
        if tag == "article" and "slug-appointment-option" in classes:
            self._active = {
                "attrs": attr,
                "text_parts": [],
                "links": [],
            }
            self._depth = 1
            return
        if self._active is None:
            return
        self._depth += 1
        if tag == "a":
            self._link_depth = self._depth
            self._link_text = []
            self._active["links"].append({
                "href": attr.get("href", ""),
                "class": attr.get("class", ""),
                "text": "",
            })

    def handle_endtag(self, tag: str) -> None:
        if self._active is None:
            return
        if tag == "a" and self._link_depth == self._depth and self._active["links"]:
            self._active["links"][-1]["text"] = clean_text(" ".join(self._link_text))
            self._link_depth = 0
            self._link_text = []
        if self._depth == 1 and tag == "article":
            self._active["text"] = clean_text(" ".join(self._active.pop("text_parts")))
            self.cards.append(self._active)
            self._active = None
            self._depth = 0
            return
        self._depth -= 1

    def handle_data(self, data: str) -> None:
        if self._active is None:
            return
        text = clean_text(data)
        if not text:
            return
        self._active["text_parts"].append(text)
        if self._link_depth:
            self._link_text.append(text)


class ExistingClassParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.existing_class_links = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attr = {name: value or "" for name, value in attrs}
        href = attr.get("href", "")
        if "coastalcprtraining.enrollware.com/enroll?id=" in href or "/classes/" in href:
            self.existing_class_links += 1


def parse_page(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "page_path": repo_path(path),
            "missing": True,
            "html": "",
            "appointment_cards": [],
            "existing_class_count": 0,
        }
    text = path.read_text(encoding="utf-8")
    card_parser = AppointmentCardParser()
    card_parser.feed(text)
    existing_parser = ExistingClassParser()
    existing_parser.feed(text)
    return {
        "page_path": repo_path(path),
        "missing": False,
        "html": text,
        "appointment_cards": card_parser.cards,
        "existing_class_count": existing_parser.existing_class_links,
    }


def seed_preview_lookup(seed_payload: Any) -> dict[tuple[str, str, str], dict[str, Any]]:
    previews = seed_payload.get("previews", []) if isinstance(seed_payload, dict) else []
    lookup: dict[tuple[str, str, str], dict[str, Any]] = {}
    if not isinstance(previews, list):
        return lookup
    for preview in previews:
        if not isinstance(preview, dict):
            continue
        key = (
            clean_text(preview.get("appointmentDayId")),
            clean_text(preview.get("course_id")),
            normalize_start_time_from_url(preview.get("appointment_url_preview")),
        )
        if all(key):
            lookup[key] = preview
    return lookup


def normalize_start_time_from_url(url: Any) -> str:
    parsed = urlparse(clean_text(url))
    raw = (parse_qs(parsed.query).get("startTime") or [""])[0]
    return normalize_clock(raw)


def normalize_clock(value: Any) -> str:
    text = unquote_plus(clean_text(value)).upper()
    text = re.sub(r"\s+", " ", text)
    for fmt in ("%I:%M %p", "%I %p", "%H:%M"):
        try:
            return datetime.strptime(text, fmt).strftime("%H:%M")
        except ValueError:
            continue
    return text


def href_tuple(url: Any) -> dict[str, str]:
    parsed = urlparse(clean_text(url))
    query = parse_qs(parsed.query)
    return {
        "appointmentDayId": clean_text((query.get("appointmentDayId") or [""])[0]),
        "courseId": clean_text((query.get("courseId") or [""])[0]),
        "startTime": clean_text((query.get("startTime") or [""])[0]),
        "startTime24": normalize_clock((query.get("startTime") or [""])[0]),
    }


def enrollware_validate(url: str, preview: dict[str, Any] | None, *, timeout: int = 20) -> dict[str, Any]:
    result = {
        "checked": False,
        "ok": False,
        "status_code": None,
        "final_url": url,
        "contains_continue_with_registration": False,
        "contains_expected_course": False,
        "contains_expected_date": False,
        "contains_expected_time": False,
        "contains_expected_location": False,
        "matched_location_by_core_tokens": False,
        "error": None,
    }
    if not url.startswith("https://coastalcprtraining.enrollware.com/enroll?"):
        result["error"] = "not_enrollware_appointment_url"
        return result
    request = urllib.request.Request(url, headers={"User-Agent": "910CPR public dynamic inventory proof"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(500000).decode("utf-8", errors="replace")
            result["checked"] = True
            result["status_code"] = response.status
            result["final_url"] = response.geturl()
    except urllib.error.HTTPError as exc:
        body = exc.read(500000).decode("utf-8", errors="replace")
        result["checked"] = True
        result["status_code"] = exc.code
        result["final_url"] = exc.geturl()
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    text = html.unescape(re.sub(r"<[^>]+>", " ", body))
    normalized = normalize_key(text)
    expected_course = normalize_key((preview or {}).get("course_title"))
    expected_location = normalize_key((preview or {}).get("location"))
    expected_date = clean_text((preview or {}).get("date"))
    expected_start = clean_text((preview or {}).get("start_time"))
    if expected_start:
        try:
            expected_start = datetime.strptime(expected_start, "%H:%M").strftime("%I:%M %p").lstrip("0")
        except ValueError:
            pass
    date_tokens = []
    if expected_date:
        parsed_date = datetime.fromisoformat(expected_date)
        date_tokens = [
            f"{parsed_date.strftime('%B')} {parsed_date.day}",
            parsed_date.strftime("%m/%d/%Y"),
            f"{parsed_date.month}/{parsed_date.day}/{parsed_date.year}",
        ]
    time_tokens = [expected_start, clean_text((preview or {}).get("start_time"))]

    raw_lower = body.lower()
    result["contains_continue_with_registration"] = (
        "continue with registration" in text.lower()
        or "continue with registration" in raw_lower
    )
    result["contains_expected_course"] = bool(expected_course and expected_course in normalized)
    result["contains_expected_location"] = bool(expected_location and expected_location in normalized)
    expected_location_tokens = meaningful_tokens((preview or {}).get("location"))
    result["matched_location_by_core_tokens"] = bool(
        expected_location_tokens
        and expected_location_tokens.issubset(meaningful_tokens(text))
    )
    result["contains_expected_date"] = any(token and token in text for token in date_tokens)
    result["contains_expected_time"] = any(token and token in text for token in time_tokens)
    result["ok"] = (
        200 <= int(result["status_code"] or 0) < 400
        and result["contains_continue_with_registration"]
        and result["contains_expected_course"]
        and result["contains_expected_date"]
        and result["contains_expected_time"]
        and (result["contains_expected_location"] or result["matched_location_by_core_tokens"])
    )
    return result


def meaningful_tokens(value: Any) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9]+", clean_text(value).lower()))
    stop = {"nc", "s", "room", "office", "the", "at", "and", "or"}
    return {token for token in tokens if token not in stop and len(token) > 1}


def dynamic_render_records(
    pages: list[dict[str, Any]],
    seed_lookup: dict[tuple[str, str, str], dict[str, Any]],
    integrity_records_by_offer_id: dict[str, dict[str, Any]],
    *,
    validate_urls: bool,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for page in pages:
        for card in page["appointment_cards"]:
            links = [link for link in card.get("links", []) if link.get("href")]
            href = links[0]["href"] if links else ""
            parsed = href_tuple(href)
            preview = seed_lookup.get((parsed["appointmentDayId"], parsed["courseId"], parsed["startTime24"]))
            integrity_record = integrity_records_by_offer_id.get(clean_text((preview or {}).get("source_offer_id")))
            validation = enrollware_validate(href, preview) if validate_urls else {"checked": False, "ok": False, "error": "url_validation_disabled"}
            records.append({
                "page_path": page["page_path"],
                "course_key": (integrity_record or {}).get("course_key") or (preview or {}).get("course_id") or UNKNOWN,
                "display_name": (integrity_record or {}).get("display_course_name") or (preview or {}).get("course_title") or UNKNOWN,
                "instructor": (integrity_record or {}).get("instructor") or (preview or {}).get("instructor_display_name") or UNKNOWN,
                "location": (integrity_record or {}).get("location") or (preview or {}).get("location") or UNKNOWN,
                "date_time": clean_text(f"{(preview or {}).get('date', UNKNOWN)} {(preview or {}).get('start_time', UNKNOWN)}"),
                "availability_block_source": (integrity_record or {}).get("source_availability_block_used") or UNKNOWN,
                "nearest_existing_enrollware_class": (integrity_record or {}).get("nearest_existing_enrollware_class_same_day_instructor_location"),
                "overlap_status": (integrity_record or {}).get("overlap_status") or UNKNOWN,
                "appointmentDayId": parsed["appointmentDayId"],
                "courseId": parsed["courseId"],
                "startTime": parsed["startTime"],
                "final_href": href,
                "rendered_on_page": True,
                "button_link_exists": bool(links),
                "url_validates_against_enrollware_page": validation.get("ok") is True,
                "enrollware_validation": validation,
                "source_offer_id": (preview or {}).get("source_offer_id") or UNKNOWN,
                "seed_id": (preview or {}).get("seed_id") or UNKNOWN,
                "card_text": card.get("text", ""),
                "trace_matched_seed_preview": preview is not None,
                "trace_matched_integrity_record": integrity_record is not None,
            })
    return records


def build_integrity_records() -> dict[str, dict[str, Any]]:
    dynamic_payload, _dynamic_error = read_json(DYNAMIC_OFFERS_PATH)
    public_payload, _public_error = read_json(PUBLIC_SELLABLE_OFFERS_PATH)
    schedule_payload, _schedule_error = read_json(SCHEDULE_FUTURE_PATH)
    current_payload, _current_error = read_json(SESSIONS_CURRENT_PATH)
    live_payload, _live_error = read_json(LIVE_AVAILABILITY_PATH)
    legacy_payload, _legacy_error = read_json(LEGACY_AVAILABILITY_PATH)

    schedule_sessions = integrity.normalize_sessions(schedule_payload or {}, "docs/data/schedule_future.json")
    occupancy_sessions = [
        *integrity.normalize_sessions(current_payload or {}, "data/sessions_current.json"),
        *schedule_sessions,
    ]
    availability = integrity.availability_blocks(live_payload or {}, legacy_payload or {})
    hidden_reasons = integrity.hidden_reasons_by_offer(public_payload if isinstance(public_payload, dict) else {})
    public_dynamic_ids = {
        str(offer.get("offer_id"))
        for offer in (public_payload or {}).get("offers", [])
        if isinstance(offer, dict)
    } if isinstance(public_payload, dict) else set()
    records: dict[str, dict[str, Any]] = {}
    for offer in (dynamic_payload or {}).get("offers", []) if isinstance(dynamic_payload, dict) else []:
        if isinstance(offer, dict) and str(offer.get("offer_id")) in public_dynamic_ids:
            record = integrity.dynamic_offer_record(offer, hidden_reasons, occupancy_sessions, availability)
            records[str(record["offer_id"])] = record
    return records


def page_summary(page: dict[str, Any], rendered_records: list[dict[str, Any]]) -> dict[str, Any]:
    page_records = [record for record in rendered_records if record["page_path"] == page["page_path"]]
    return {
        "page_path": page["page_path"],
        "course_category": Path(page["page_path"]).stem,
        "visible_offers_count": page["existing_class_count"] + len(page_records),
        "existing_enrollware_class_count": page["existing_class_count"],
        "dynamic_appointment_seed_count": len(page_records),
        "visible_dynamic_offers": page_records,
        "missing": page.get("missing") is True,
    }


def verdict(stats: dict[str, Any], records: list[dict[str, Any]], missing: dict[str, str]) -> tuple[str, str]:
    if missing:
        return "UNKNOWN", "Required data was missing or unreadable."
    if stats["public_sellable_dynamic_offers"] == 0:
        return "FAIL", "No public sellable dynamic appointment-seed offers exist after filtering."
    if stats["rendered_dynamic_offers"] == 0:
        return "FAIL", "Dynamic offers exist after filtering, but no appointment-seed cards were found in rendered public HTML."
    unsafe = [
        record for record in records
        if record["overlap_status"] in {"overlaps_existing_class", "overlaps_setup_cleanup_buffer"}
        or not record["button_link_exists"]
        or not record["url_validates_against_enrollware_page"]
        or not record["trace_matched_seed_preview"]
        or not record["trace_matched_integrity_record"]
    ]
    if unsafe:
        return "UNSAFE", "At least one rendered dynamic offer has an overlap, missing traceability, missing link, or invalid Enrollware URL proof."
    return "PASS", "Public site shows at least one valid, bookable, gap-based dynamic appointment-seed offer."


def run(*, validate_urls: bool = True) -> dict[str, Any]:
    public_payload, public_error = read_json(PUBLIC_SELLABLE_OFFERS_PATH)
    dynamic_payload, dynamic_error = read_json(DYNAMIC_OFFERS_PATH)
    seed_payload, seed_error = read_json(SEED_URL_PREVIEW_PATH)
    schedule_payload, schedule_error = read_json(SCHEDULE_FUTURE_PATH)
    current_payload, current_error = read_json(SESSIONS_CURRENT_PATH)
    missing = {
        name: error
        for name, error in {
            "public_sellable_offers_preview": public_error,
            "dynamic_offers_preview": dynamic_error,
            "seed_appointment_url_preview": seed_error,
            "schedule_future": schedule_error,
            "sessions_current": current_error,
        }.items()
        if error
    }

    public_offers = public_payload.get("offers", []) if isinstance(public_payload, dict) and isinstance(public_payload.get("offers"), list) else []
    dynamic_offers = dynamic_payload.get("offers", []) if isinstance(dynamic_payload, dict) and isinstance(dynamic_payload.get("offers"), list) else []
    seed_previews = seed_payload.get("previews", []) if isinstance(seed_payload, dict) and isinstance(seed_payload.get("previews"), list) else []
    public_ids = {str(offer.get("offer_id")) for offer in public_offers if isinstance(offer, dict)}
    public_dynamic = [offer for offer in dynamic_offers if isinstance(offer, dict) and str(offer.get("offer_id")) in public_ids]
    hidden_reasons = integrity.hidden_reasons_by_offer(public_payload if isinstance(public_payload, dict) else {})
    course_page_paths = sorted((DOCS_DIR / "courses").glob("*.html")) if (DOCS_DIR / "courses").exists() else []
    pages = [parse_page(path) for path in [*PUBLIC_HUB_PAGE_PATHS, *course_page_paths]]
    integrity_records = build_integrity_records()
    seed_lookup = seed_preview_lookup(seed_payload if isinstance(seed_payload, dict) else {})
    rendered_dynamic_records = dynamic_render_records(
        pages,
        seed_lookup,
        integrity_records,
        validate_urls=validate_urls,
    )
    page_summaries = [page_summary(page, rendered_dynamic_records) for page in pages]
    generated_not_public = [
        offer.get("offer_id")
        for offer in dynamic_offers
        if isinstance(offer, dict) and str(offer.get("offer_id")) not in public_ids
    ]
    duplicate_public = [
        record for record in integrity_records.values()
        if record.get("nearest_existing_enrollware_class_same_day_instructor_location")
        and record.get("public_display_start") == record["nearest_existing_enrollware_class_same_day_instructor_location"].get("start")
        and normalize_key(record.get("display_course_name")) == normalize_key(record["nearest_existing_enrollware_class_same_day_instructor_location"].get("display_course_name"))
    ]
    stats = {
        "public_sellable_dynamic_offers": len(public_dynamic),
        "dynamic_seed_url_previews": len(seed_previews),
        "rendered_dynamic_offers": len(rendered_dynamic_records),
        "rendered_dynamic_offers_with_links": sum(1 for record in rendered_dynamic_records if record["button_link_exists"]),
        "rendered_dynamic_offers_with_valid_enrollware_url": sum(1 for record in rendered_dynamic_records if record["url_validates_against_enrollware_page"]),
        "generated_dynamic_offers": len(dynamic_offers),
        "generated_dynamic_offers_filtered_out_before_public_rendering": len(generated_not_public),
        "public_dynamic_offers_not_rendered": max(len(public_dynamic) - len(rendered_dynamic_records), 0),
        "public_facing_offers_merely_duplicated_enrollware_classes": len(duplicate_public),
        "hidden_dynamic_reasons": dict(Counter(reason for reasons in hidden_reasons.values() for reason in reasons).most_common()),
        "pages_inspected": len(pages),
        "pages_with_dynamic_offers": sum(1 for page in page_summaries if page["dynamic_appointment_seed_count"]),
        "url_validation_enabled": validate_urls,
    }
    status, status_reason = verdict(stats, rendered_dynamic_records, missing)
    report = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "read_only": True,
        "deployed": False,
        "public_dynamic_inventory_status": status,
        "verdict_reason": status_reason,
        "files_missing_or_unreadable": missing,
        "stats": stats,
        "answers": {
            "any_public_facing_dynamic_seed_offers": len(public_dynamic) > 0,
            "any_visible_on_rendered_public_pages": len(rendered_dynamic_records) > 0,
            "visible_on_reachable_course_pages_or_hubs": any(page["dynamic_appointment_seed_count"] for page in page_summaries if not page["missing"]),
            "book_buttons_point_to_enrollware_appointment_urls": all(record["button_link_exists"] and "appointmentDayId=" in record["final_href"] for record in rendered_dynamic_records) if rendered_dynamic_records else False,
            "appointment_urls_validate_against_enrollware_page": all(record["url_validates_against_enrollware_page"] for record in rendered_dynamic_records) if rendered_dynamic_records else False,
            "dynamic_offers_generated_from_gaps_without_existing_class": all(record["trace_matched_integrity_record"] and record["overlap_status"] == "no_overlap" for record in rendered_dynamic_records) if rendered_dynamic_records else False,
            "any_public_facing_offers_merely_duplicated_enrollware_classes": bool(duplicate_public),
            "any_generated_dynamic_offers_filtered_out_before_public_rendering": bool(generated_not_public),
        },
        "public_pages_inspected": page_summaries,
        "rendered_dynamic_offers": rendered_dynamic_records,
        "filtered_dynamic_offer_sample": generated_not_public[:100],
        "duplicate_public_dynamic_offer_records": duplicate_public,
    }
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD_PATH.write_text(render_markdown(report), encoding="utf-8")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    stats = report["stats"]
    lines = [
        "# Public Dynamic Inventory Proof",
        "",
        "Read-only proof report. No deployment, redesign, branding changes, public data mutation, Enrollware writes, or appointment creation were performed.",
        "",
        "## PUBLIC DYNAMIC INVENTORY STATUS",
        "",
        f"- {report['public_dynamic_inventory_status']}: {report['verdict_reason']}",
        "",
        "## Direct Answers",
        "",
    ]
    for key, value in report["answers"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend([
        "",
        "## Counts",
        "",
        f"- Public sellable dynamic offers: `{stats['public_sellable_dynamic_offers']}`",
        f"- Dynamic seed URL previews: `{stats['dynamic_seed_url_previews']}`",
        f"- Rendered dynamic offers: `{stats['rendered_dynamic_offers']}`",
        f"- Rendered dynamic offers with links: `{stats['rendered_dynamic_offers_with_links']}`",
        f"- Rendered dynamic offers with valid Enrollware URL: `{stats['rendered_dynamic_offers_with_valid_enrollware_url']}`",
        f"- Generated dynamic offers: `{stats['generated_dynamic_offers']}`",
        f"- Generated dynamic offers filtered out before public rendering: `{stats['generated_dynamic_offers_filtered_out_before_public_rendering']}`",
        f"- Public dynamic offers not rendered: `{stats['public_dynamic_offers_not_rendered']}`",
        f"- Duplicated Enrollware-class dynamic offers: `{stats['public_facing_offers_merely_duplicated_enrollware_classes']}`",
        "",
        "## Public Pages Inspected",
        "",
    ])
    for page in report["public_pages_inspected"]:
        lines.extend([
            f"### {page['page_path']}",
            "",
            f"- Course/category: `{page['course_category']}`",
            f"- Visible offers count: `{page['visible_offers_count']}`",
            f"- Existing Enrollware class count: `{page['existing_enrollware_class_count']}`",
            f"- Dynamic appointment-seed count: `{page['dynamic_appointment_seed_count']}`",
            "",
        ])
        for offer in page["visible_dynamic_offers"]:
            lines.extend([
                f"- Dynamic offer `{offer['source_offer_id']}`",
                f"  - Course: `{offer['display_name']}`",
                f"  - Instructor: `{offer['instructor']}`",
                f"  - Location: `{offer['location']}`",
                f"  - Date/time: `{offer['date_time']}`",
                f"  - Availability block: `{offer['availability_block_source']}`",
                f"  - Overlap status: `{offer['overlap_status']}`",
                f"  - appointmentDayId/courseId/startTime: `{offer['appointmentDayId']}` / `{offer['courseId']}` / `{offer['startTime']}`",
                f"  - Final href: `{offer['final_href']}`",
                f"  - Rendered/button/url valid: `{offer['rendered_on_page']}` / `{offer['button_link_exists']}` / `{offer['url_validates_against_enrollware_page']}`",
                "",
            ])
    if stats["hidden_dynamic_reasons"]:
        lines.extend(["## Filtered Dynamic Offer Reasons", ""])
        lines.extend(f"- `{reason}`: `{count}`" for reason, count in stats["hidden_dynamic_reasons"].items())
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = run(validate_urls=True)
    stats = report["stats"]
    print("Public dynamic inventory proof complete (READ ONLY).")
    print("No deployment performed.")
    print("")
    print(f"PUBLIC DYNAMIC INVENTORY STATUS: {report['public_dynamic_inventory_status']}")
    print(report["verdict_reason"])
    print("")
    print(f"Public sellable dynamic offers: {stats['public_sellable_dynamic_offers']}")
    print(f"Rendered dynamic offers: {stats['rendered_dynamic_offers']}")
    print(f"Rendered dynamic offers with valid Enrollware URL: {stats['rendered_dynamic_offers_with_valid_enrollware_url']}")
    print(f"Generated dynamic offers filtered out before public rendering: {stats['generated_dynamic_offers_filtered_out_before_public_rendering']}")
    print("")
    print("Output files:")
    print(f"- {REPORT_MD_PATH}")
    print(f"- {REPORT_JSON_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
