from __future__ import annotations

import html
import json
import re
import urllib.parse
from collections import defaultdict
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from scripts import public_dynamic_inventory_proof as url_proof
from scripts import public_offer_integrity_audit as integrity


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
DOCS_DIR = ROOT / "docs"

PUBLIC_SELLABLE_OFFERS_PATH = AUDIT_DIR / "public_sellable_offers_preview.json"
PRESENTATION_POLICY_PATH = AUDIT_DIR / "dynamic_offer_presentation_policy_report.json"
PUBLIC_INTEGRITY_PATH = AUDIT_DIR / "public_offer_integrity_report.json"
REPORT_MD_PATH = AUDIT_DIR / "rendered_dynamic_offer_proof.md"
REPORT_JSON_PATH = AUDIT_DIR / "rendered_dynamic_offer_proof.json"

ENROLLWARE_BASE = "https://coastalcprtraining.enrollware.com/enroll"
PUBLIC_ENTRY_PAGES = [
    DOCS_DIR / "classes" / "index.html",
    DOCS_DIR / "heartsaver.html",
    DOCS_DIR / "hsi.html",
    DOCS_DIR / "bls.html",
    DOCS_DIR / "acls.html",
    DOCS_DIR / "pals.html",
    DOCS_DIR / "arc.html",
    DOCS_DIR / "uscg-elementary-first-aid-cpr.html",
    DOCS_DIR / "group-training.html",
]


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


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def display_clock(value: Any) -> str:
    text = clean_text(value)
    for fmt in ("%H:%M", "%I:%M %p", "%I %p"):
        try:
            return datetime.strptime(text, fmt).strftime("%-I:%M %p")
        except ValueError:
            continue
    try:
        return datetime.strptime(text, "%H:%M").strftime("%#I:%M %p")
    except ValueError:
        return text


def windows_clock(value: Any) -> str:
    text = clean_text(value)
    for fmt in ("%H:%M", "%I:%M %p", "%I %p"):
        try:
            return datetime.strptime(text, fmt).strftime("%#I:%M %p")
        except ValueError:
            continue
    return text


def appointment_href(offer: dict[str, Any]) -> str:
    direct = clean_text(offer.get("appointment_registration_url"))
    if direct:
        return direct
    start = windows_clock(offer.get("start_time"))
    return (
        f"{ENROLLWARE_BASE}?appointmentDayId={urllib.parse.quote(clean_text(offer.get('appointmentDayId')), safe='')}"
        f"&startTime={urllib.parse.quote(start, safe='')}"
        f"&courseId={urllib.parse.quote(clean_text(offer.get('course_id')), safe='')}"
    )


def offer_id(offer: dict[str, Any]) -> str:
    return clean_text(offer.get("offer_id"))


class LinkContextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, Any]] = []
        self._stack: list[dict[str, Any]] = []
        self._active_link: dict[str, Any] | None = None
        self._active_link_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {name: value or "" for name, value in attrs}
        node = {"tag": tag, "attrs": attr, "text": []}
        self._stack.append(node)
        if tag == "a":
            self._active_link = {
                "href": html.unescape(attr.get("href", "")),
                "text_parts": [],
                "attrs": attr,
                "ancestors": [item["attrs"] for item in self._stack],
            }
            self._active_link_depth = len(self._stack)

    def handle_endtag(self, tag: str) -> None:
        if self._active_link and len(self._stack) == self._active_link_depth and tag == "a":
            href = self._active_link["href"]
            if "appointmentDayId=" in href:
                text = clean_text(" ".join(self._active_link["text_parts"]))
                context_node = self._nearest_context_node()
                classes = " ".join(
                    clean_text(attrs.get("class"))
                    for attrs in self._active_link["ancestors"]
                    if attrs.get("class")
                )
                self.links.append({
                    "href": href,
                    "text": text,
                    "context_text": clean_text(" ".join(context_node.get("text", []))) if context_node else text,
                    "distinguishable_as_dynamic": "slug-appointment-option" in classes or "data-source-type=\"seed\"" in classes,
                    "ancestor_classes": classes,
                })
            self._active_link = None
            self._active_link_depth = 0
        if self._stack:
            node = self._stack.pop()
            if self._stack:
                self._stack[-1]["text"].extend(node.get("text", []))

    def handle_data(self, data: str) -> None:
        text = clean_text(data)
        if not text:
            return
        if self._stack:
            self._stack[-1]["text"].append(text)
        if self._active_link:
            self._active_link["text_parts"].append(text)

    def _nearest_context_node(self) -> dict[str, Any] | None:
        for node in reversed(self._stack):
            classes = set(clean_text(node.get("attrs", {}).get("class")).split())
            if {"slug-pill", "slug-appointment-option"} & classes:
                return node
        return self._stack[-2] if len(self._stack) > 1 else None


class AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attr = {name: value or "" for name, value in attrs}
        href = html.unescape(attr.get("href", ""))
        if href:
            self.hrefs.append(href)


def html_pages() -> list[Path]:
    return sorted(path for path in DOCS_DIR.rglob("*.html") if "control-center" not in path.parts)


def parse_rendered_links() -> dict[str, list[dict[str, Any]]]:
    rendered: dict[str, list[dict[str, Any]]] = {}
    for path in html_pages():
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        parser = LinkContextParser()
        parser.feed(text)
        if parser.links:
            rendered[repo_path(path)] = parser.links
    return rendered


def page_reachability() -> dict[str, bool]:
    reachable = {repo_path(path): True for path in PUBLIC_ENTRY_PAGES if path.exists()}
    for entry in PUBLIC_ENTRY_PAGES:
        if not entry.exists():
            continue
        parser = AnchorParser()
        parser.feed(entry.read_text(encoding="utf-8"))
        base = entry.parent
        for href in parser.hrefs:
            local = href.split("#", 1)[0].split("?", 1)[0]
            if not local or local.startswith(("http:", "https:", "mailto:", "tel:")):
                continue
            target = (DOCS_DIR / local.lstrip("/")).resolve() if local.startswith("/") else (base / local).resolve()
            if target.exists() and target.suffix == ".html":
                reachable[repo_path(target)] = True
    return reachable


def integrity_by_offer_id(payload: Any) -> dict[str, dict[str, Any]]:
    records = payload.get("offer_records", []) if isinstance(payload, dict) else []
    return {clean_text(record.get("offer_id")): record for record in records if isinstance(record, dict)}


def public_dynamic_offers(payload: Any) -> list[dict[str, Any]]:
    offers = payload.get("offers", []) if isinstance(payload, dict) else []
    return [offer for offer in offers if isinstance(offer, dict)]


def presentation_dynamic_offers(payload: Any) -> list[dict[str, Any]]:
    offers = payload.get("render_offers", []) if isinstance(payload, dict) else []
    return [offer for offer in offers if isinstance(offer, dict)]


def duplicate_existing_rendered(record: dict[str, Any], rendered_by_href: dict[str, list[dict[str, Any]]]) -> bool:
    nearest = record.get("nearest_existing_enrollware_class_same_day_instructor_location")
    if not isinstance(nearest, dict):
        return False
    return (
        normalize_key(record.get("display_course_name")) == normalize_key(nearest.get("display_course_name"))
        and clean_text(record.get("public_display_start")) == clean_text(nearest.get("start"))
        and normalize_key(record.get("location")) == normalize_key(nearest.get("location"))
    )


def proof_record(
    offer: dict[str, Any],
    integrity_record: dict[str, Any],
    rendered_by_href: dict[str, list[dict[str, Any]]],
    reachable: dict[str, bool],
    *,
    validate_url: bool,
) -> dict[str, Any]:
    href = appointment_href(offer)
    rendered_matches = rendered_by_href.get(href, [])
    rendered_paths = sorted({match["page_path"] for match in rendered_matches})
    sample_link = rendered_matches[0] if rendered_matches else {}
    preview = {
        "course_title": offer.get("course_title"),
        "date": offer.get("date"),
        "start_time": offer.get("start_time"),
        "location": offer.get("location"),
    }
    validation = url_proof.enrollware_validate(href, preview) if validate_url else {
        "checked": False,
        "ok": False,
        "error": "not_sampled",
    }
    return {
        "offer_id": offer_id(offer),
        "course_key": offer.get("course_family") or integrity_record.get("course_key"),
        "display_course_name": offer.get("course_title") or integrity_record.get("display_course_name"),
        "instructor": offer.get("instructor_display_name") or integrity_record.get("instructor"),
        "location": offer.get("location") or integrity_record.get("location"),
        "date": offer.get("date"),
        "public_display_start": offer.get("appointment_display_start") or offer.get("start_datetime"),
        "public_display_end": offer.get("appointment_display_end") or offer.get("end_datetime"),
        "scheduler_consumption_start": offer.get("scheduler_consumption_start"),
        "scheduler_consumption_end": offer.get("scheduler_consumption_end"),
        "source_availability_block": offer.get("source_availability_window") or integrity_record.get("source_availability_block_used"),
        "appointmentDayId": offer.get("appointmentDayId"),
        "courseId": offer.get("course_id"),
        "startTime": windows_clock(offer.get("start_time")),
        "final_enrollware_href": href,
        "rendered_page_paths": rendered_paths,
        "rendered": bool(rendered_matches),
        "link_or_button_text": sorted({match.get("text", "") for match in rendered_matches if match.get("text")}),
        "href_in_html_exactly_matches_audited_href": bool(rendered_matches),
        "page_reachable_from_course_hub_or_catalog": any(reachable.get(path) for path in rendered_paths),
        "dynamic_offer_distinguishable_in_html": any(match.get("distinguishable_as_dynamic") for match in rendered_matches),
        "duplicate_existing_enrollware_class_rendered_same_tuple": duplicate_existing_rendered(integrity_record, rendered_by_href),
        "overlap_status": integrity_record.get("overlap_status", "unknown"),
        "nearest_existing_enrollware_class": integrity_record.get("nearest_existing_enrollware_class_same_day_instructor_location"),
        "enrollware_url_sample_checked": validation["checked"],
        "enrollware_url_validates": validation["ok"],
        "enrollware_validation": validation,
        "rendered_context_text": sorted({match.get("context_text", "") for match in rendered_matches if match.get("context_text")}),
    }


def verdict(records: list[dict[str, Any]], missing: dict[str, str]) -> tuple[str, str]:
    if missing:
        return "UNKNOWN", "Required input data was missing or unreadable."
    if not records:
        return "FAIL", "No public sellable dynamic appointment-seed offers were available to audit."
    unsafe = [
        record for record in records
        if record["overlap_status"] in {"overlaps_existing_class", "overlaps_setup_cleanup_buffer"}
        or (record["rendered"] and not record["href_in_html_exactly_matches_audited_href"])
        or (record["rendered"] and not record["link_or_button_text"])
    ]
    if unsafe:
        return "UNSAFE", "One or more rendered dynamic offers overlaps occupancy, lacks a link label, or has an invalid rendered href."
    rendered_count = sum(1 for record in records if record["rendered"])
    if rendered_count == len(records):
        return "PASS", "All public sellable dynamic appointment-seed offers are visible in rendered customer-facing HTML with correct links."
    if rendered_count:
        return "PARTIAL", f"{rendered_count} of {len(records)} public sellable dynamic appointment-seed offers render; {len(records) - rendered_count} are absent from HTML."
    return "FAIL", "Public sellable dynamic appointment-seed offers exist in data but do not render publicly."


def run(*, validate_sample_count: int = 3) -> dict[str, Any]:
    public_payload, public_error = read_json(PUBLIC_SELLABLE_OFFERS_PATH)
    presentation_payload, presentation_error = read_json(PRESENTATION_POLICY_PATH)
    integrity_payload, integrity_error = read_json(PUBLIC_INTEGRITY_PATH)
    presentation_offers = presentation_dynamic_offers(presentation_payload if isinstance(presentation_payload, dict) else {})
    offer_source = "dynamic_offer_presentation_policy_report" if presentation_offers else "public_sellable_offers_preview"
    missing = {
        name: error
        for name, error in {
            "public_sellable_offers_preview": public_error,
            "dynamic_offer_presentation_policy_report": presentation_error if not presentation_offers else None,
            "public_offer_integrity_report": integrity_error,
        }.items()
        if error
    }
    offers = presentation_offers or public_dynamic_offers(public_payload if isinstance(public_payload, dict) else {})
    integrity_lookup = integrity_by_offer_id(integrity_payload if isinstance(integrity_payload, dict) else {})
    rendered_by_page = parse_rendered_links()
    rendered_by_href: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for page_path, links in rendered_by_page.items():
        for link in links:
            item = dict(link)
            item["page_path"] = page_path
            rendered_by_href[item["href"]].append(item)
    reachable = page_reachability()
    sample_ids = {offer_id(offer) for offer in offers[:validate_sample_count]}
    records = [
        proof_record(
            offer,
            integrity_lookup.get(offer_id(offer), {}),
            rendered_by_href,
            reachable,
            validate_url=offer_id(offer) in sample_ids,
        )
        for offer in offers
    ]
    status, reason = verdict(records, missing)
    stats = {
        "public_sellable_dynamic_offers": len(records),
        "rendered_dynamic_offers": sum(1 for record in records if record["rendered"]),
        "missing_from_rendered_html": sum(1 for record in records if not record["rendered"]),
        "rendered_with_book_enroll_register_link": sum(1 for record in records if record["rendered"] and record["link_or_button_text"]),
        "rendered_with_exact_href_match": sum(1 for record in records if record["href_in_html_exactly_matches_audited_href"]),
        "reachable_from_course_hub_or_catalog": sum(1 for record in records if record["page_reachable_from_course_hub_or_catalog"]),
        "distinguishable_dynamic_in_html": sum(1 for record in records if record["dynamic_offer_distinguishable_in_html"]),
        "duplicate_existing_enrollware_class_rendered_same_tuple": sum(1 for record in records if record["duplicate_existing_enrollware_class_rendered_same_tuple"]),
        "overlap_failures": sum(1 for record in records if record["overlap_status"] in {"overlaps_existing_class", "overlaps_setup_cleanup_buffer"}),
        "enrollware_urls_sample_checked": sum(1 for record in records if record["enrollware_url_sample_checked"]),
        "enrollware_urls_sample_valid": sum(1 for record in records if record["enrollware_url_validates"]),
    }
    report = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "read_only": True,
        "deployed": False,
        "static_site_render_command_used": "python -m scripts.build_slug_hubs",
        "audited_offer_source": offer_source,
        "rendered_dynamic_offer_status": status,
        "verdict_reason": reason,
        "files_missing_or_unreadable": missing,
        "stats": stats,
        "offers": records,
    }
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD_PATH.write_text(render_markdown(report), encoding="utf-8")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    stats = report["stats"]
    lines = [
        "# Rendered Dynamic Offer Proof",
        "",
        "Read-only rendered public-page proof. No deployment, redesign, filtering logic change, Enrollware write, or appointment creation was performed.",
        "",
        "## RENDERED PUBLIC DYNAMIC OFFER STATUS",
        "",
        f"- {report['rendered_dynamic_offer_status']}: {report['verdict_reason']}",
        "",
        "## Render Command",
        "",
        f"- `{report['static_site_render_command_used']}`",
        "",
        "## Counts",
        "",
        f"- Public sellable dynamic appointment-seed offers: `{stats['public_sellable_dynamic_offers']}`",
        f"- Rendered dynamic offers: `{stats['rendered_dynamic_offers']}`",
        f"- Missing from rendered HTML: `{stats['missing_from_rendered_html']}`",
        f"- Rendered with Book/Enroll/Register link text: `{stats['rendered_with_book_enroll_register_link']}`",
        f"- Rendered with exact audited href match: `{stats['rendered_with_exact_href_match']}`",
        f"- Reachable from course hub or catalog: `{stats['reachable_from_course_hub_or_catalog']}`",
        f"- Distinguishable dynamic in HTML: `{stats['distinguishable_dynamic_in_html']}`",
        f"- Duplicate existing Enrollware class same tuple: `{stats['duplicate_existing_enrollware_class_rendered_same_tuple']}`",
        f"- Overlap failures: `{stats['overlap_failures']}`",
        f"- Enrollware URLs sample checked: `{stats['enrollware_urls_sample_checked']}`",
        f"- Enrollware URLs sample valid: `{stats['enrollware_urls_sample_valid']}`",
        "",
        "## Offer Results",
        "",
    ]
    for record in report["offers"]:
        lines.extend([
            f"### {record['offer_id']}",
            "",
            f"- Course key: `{record['course_key']}`",
            f"- Display course name: `{record['display_course_name']}`",
            f"- Instructor: `{record['instructor']}`",
            f"- Location: `{record['location']}`",
            f"- Date: `{record['date']}`",
            f"- Public display start/end: `{record['public_display_start']}` / `{record['public_display_end']}`",
            f"- Scheduler consumption start/end: `{record['scheduler_consumption_start']}` / `{record['scheduler_consumption_end']}`",
            f"- Source availability block: `{record['source_availability_block']}`",
            f"- appointmentDayId/courseId/startTime: `{record['appointmentDayId']}` / `{record['courseId']}` / `{record['startTime']}`",
            f"- Final Enrollware href: `{record['final_enrollware_href']}`",
            f"- Rendered page path(s): `{', '.join(record['rendered_page_paths']) if record['rendered_page_paths'] else 'NONE'}`",
            f"- Link/button text: `{', '.join(record['link_or_button_text']) if record['link_or_button_text'] else 'NONE'}`",
            f"- HTML href exactly matches audited href: `{record['href_in_html_exactly_matches_audited_href']}`",
            f"- Reachable from course hub/catalog: `{record['page_reachable_from_course_hub_or_catalog']}`",
            f"- Dynamic distinguishable internally: `{record['dynamic_offer_distinguishable_in_html']}`",
            f"- Duplicate existing Enrollware class rendered same tuple: `{record['duplicate_existing_enrollware_class_rendered_same_tuple']}`",
            f"- Overlap status: `{record['overlap_status']}`",
            f"- Enrollware URL sample checked/valid: `{record['enrollware_url_sample_checked']}` / `{record['enrollware_url_validates']}`",
            "",
        ])
    return "\n".join(lines)


def main() -> int:
    report = run(validate_sample_count=3)
    stats = report["stats"]
    print("Rendered dynamic offer proof complete (READ ONLY).")
    print("No deployment performed.")
    print("")
    print(f"RENDERED PUBLIC DYNAMIC OFFER STATUS: {report['rendered_dynamic_offer_status']}")
    print(report["verdict_reason"])
    print("")
    print(f"Public sellable dynamic offers: {stats['public_sellable_dynamic_offers']}")
    print(f"Rendered dynamic offers: {stats['rendered_dynamic_offers']}")
    print(f"Missing from rendered HTML: {stats['missing_from_rendered_html']}")
    print(f"Enrollware URLs sample valid: {stats['enrollware_urls_sample_valid']}/{stats['enrollware_urls_sample_checked']}")
    print("")
    print("Output files:")
    print(f"- {REPORT_MD_PATH}")
    print(f"- {REPORT_JSON_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
