from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import date, datetime
from html import escape
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

from scripts.ensure_analytics_tags import GTM_HEAD_SNIPPET, GTM_NOSCRIPT_SNIPPET

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ARTIFACTS = DOCS / "data" / "block-selector-availability"
SCHEDULE = DOCS / "data" / "schedule_future.json"
MANIFEST = DOCS / "data" / "date_availability_manifest.json"
REPORT = ROOT / "data" / "audit" / "date_availability_build_report.json"
SITEMAP = DOCS / "sitemap.xml"
SITE = "https://www.910cpr.com"
TZ = ZoneInfo("America/New_York")
PHONE = "910-395-5193"
ADDRESS = "4018 Shipyard Blvd, Wilmington, NC 28403"
FULL_SCHEDULE = "/schedule.html"

PAGE_NAMES = {
    "bls": "BLS Certification",
    "acls": "ACLS Certification",
    "pals": "PALS Certification",
    "arc": "Red Cross Certification",
    "hsi": "HSI Certification",
    "heartsaver": "Heartsaver Certification",
    "family_cpr": "Family & Friends CPR",
    "uscg_first_aid_cpr_aed": "USCG First Aid & CPR",
}
HUB_PATHS = {
    "family_cpr": "/family-cpr.html",
    "uscg_first_aid_cpr_aed": "/uscg-elementary-first-aid-cpr.html",
}


def slug(value: object) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")
    return text or "wilmington"


def city_for(location: str) -> str:
    match = re.search(r"\b(Wilmington|Jacksonville|Leland|Raleigh|Durham|Fayetteville)\b", location, re.I)
    return match.group(1).title() if match else "Wilmington"


def clean_location(location: str) -> str:
    city = city_for(location)
    if city == "Wilmington":
        return f"910CPR Training Center, {ADDRESS}"
    return re.sub(r"^:+\s*", "", location).replace(";", ",").strip()


def load_json(path: Path, fallback: object) -> object:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def page_key_for_session(session: dict) -> str:
    family = str(session.get("mapped_family") or "").lower()
    agency = str(session.get("mapped_certifying_body") or "").lower()
    if agency == "arc":
        return "arc"
    if agency == "hsi":
        return "hsi"
    if family in {"bls", "acls", "pals"}:
        return family
    if "heartsaver" in str(session.get("course_name") or "").lower():
        return "heartsaver"
    return ""


def session_date(session: dict) -> str:
    return str(session.get("start_at") or "")[:10]


def is_real_session(offer: dict) -> bool:
    return offer.get("offerType") == "seated_class" or str(offer.get("availabilityBlockId") or "").startswith("seated:")


def offer_key(offer: dict) -> tuple[str, str, str]:
    return (
        str(offer.get("courseId") or ""),
        str(offer.get("date") or ""),
        str(offer.get("startTime") or ""),
    )


def valid_appointment_url(offer: dict) -> bool:
    url = str(offer.get("appointmentUrl") or offer.get("registrationUrl") or "")
    if is_real_session(offer):
        return bool(re.search(r"[?&]id=\d+", url))
    query = parse_qs(urlparse(url).query)
    return (
        query.get("appointmentDayId", [""])[0] == str(offer.get("appointmentDayId") or "")
        and query.get("courseId", [""])[0] == str(offer.get("courseId") or "")
        and bool(query.get("startTime", [""])[0])
    )


def collect(now: date) -> tuple[dict[tuple[str, str, str], dict], int]:
    pages: dict[tuple[str, str, str], dict] = {}
    skipped = 0
    for path in sorted(ARTIFACTS.glob("*.json")):
        payload = load_json(path, {})
        if not isinstance(payload, dict) or payload.get("schemaVersion") != "selector-resolved-availability.v1":
            continue
        page_key = str(payload.get("pageKey") or path.stem)
        for day in payload.get("dates", []):
            grouped: dict[str, list[dict]] = defaultdict(list)
            for slot in day.get("startTimes", []):
                for raw in slot.get("courses", []):
                    offer = dict(raw)
                    offer.setdefault("date", day.get("date"))
                    offer.setdefault("displayDate", day.get("displayDate"))
                    offer.setdefault("startTime", slot.get("startTime"))
                    offer.setdefault("displayStartTime", slot.get("displayStartTime"))
                    if not offer.get("publicSelectable") or not valid_appointment_url(offer):
                        skipped += 1
                        continue
                    grouped[city_for(str(offer.get("location") or ""))].append(offer)
            for city, offers in grouped.items():
                if offers:
                    key = (page_key, slug(city), str(day["date"]))
                    pages[key] = {
                        "page_key": page_key,
                        "city": city,
                        "date": str(day["date"]),
                        "display_date": str(day.get("displayDate") or day["date"]),
                        "offers": sorted(offers, key=lambda row: (row["startTime"], row["courseName"])),
                        "authority": payload.get("authority", {}),
                        "generated_at": payload.get("generatedAt"),
                    }

    schedule = load_json(SCHEDULE, {})
    sessions = schedule.get("sessions", []) if isinstance(schedule, dict) else []
    for session in sessions:
        page_key = page_key_for_session(session)
        day = session_date(session)
        location = str(session.get("location_display") or session.get("location_name") or "")
        if not page_key or not day or not location:
            continue
        city = city_for(location)
        key = (page_key, slug(city), day)
        if key not in pages:
            pages[key] = {
                "page_key": page_key,
                "city": city,
                "date": day,
                "display_date": datetime.fromisoformat(day).strftime("%A, %B %-d, %Y") if __import__("os").name != "nt" else datetime.fromisoformat(day).strftime("%A, %B %#d, %Y"),
                "offers": [],
                "authority": {"name": "schedule_future real session"},
                "generated_at": schedule.get("build", {}).get("generated_at"),
            }
        pages[key]["real_sessions"] = pages[key].get("real_sessions", []) + [session]
    return pages, skipped


def course_schema(page: dict, canonical: str, location: str) -> list[dict]:
    seen: set[str] = set()
    schemas = []
    for offer in page["offers"]:
        cid = str(offer.get("courseId") or "")
        if cid in seen:
            continue
        seen.add(cid)
        schemas.append({
            "@type": "Course",
            "@id": f"{SITE}/courses/{slug(offer.get('courseName'))}.html#course",
            "name": offer.get("courseName"),
            "description": f"{offer.get('courseName')} training available through 910CPR.",
            "provider": {"@id": f"{SITE}/#organization"},
            "courseMode": "Blended" if offer.get("deliveryMode") == "blended" else "Onsite",
            "url": canonical,
            "location": {"@id": f"{SITE}/locations/{slug(page['city'])}.html#place"},
        })
    return schemas


def event_schema(session: dict) -> dict:
    start = str(session.get("start_at") or "")
    end = str(session.get("end_at") or "")
    sid = str(session.get("session_id") or "")
    url = str(session.get("registration_url") or f"{SITE}/classes/{sid}.html")
    status = str(session.get("registration_status") or "").lower()
    return {
        "@type": "Event",
        "@id": f"{SITE}/classes/{sid}.html#event",
        "name": session.get("official_course_name") or session.get("course_name"),
        "startDate": start,
        "endDate": end,
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "eventStatus": "https://schema.org/EventScheduled",
        "location": {
            "@type": "Place",
            "@id": f"{SITE}/locations/{slug(city_for(str(session.get('location_display') or '')))}.html#place",
            "name": clean_location(str(session.get("location_display") or "")),
            "address": {"@type": "PostalAddress", "streetAddress": "4018 Shipyard Blvd", "addressLocality": "Wilmington", "addressRegion": "NC", "postalCode": "28403", "addressCountry": "US"},
        },
        "organizer": {"@id": f"{SITE}/#organization"},
        "offers": {
            "@type": "Offer",
            "url": url,
            "availability": "https://schema.org/SoldOut" if status in {"closed", "full"} else "https://schema.org/InStock",
        },
    }


def data_layer_script(page: dict, state: str) -> str:
    agency = sorted({str(o.get("certifyingBody") or "") for o in page["offers"]})
    payload = {
        "event": "view_date_availability",
        "course_family": page["page_key"],
        "agency": ",".join(agency),
        "location_name": page["city"],
        "city": page["city"],
        "date": page["date"],
        "availability_state": state,
        "page_type": "date_availability",
    }
    return f"<script>window.dataLayer=window.dataLayer||[];window.dataLayer.push({json.dumps(payload, separators=(',', ':'))});</script>"


def render(page: dict, future_pages: list[dict], now: date, build_id: str) -> tuple[str, str]:
    key = page["page_key"]
    city = page["city"]
    display_date = page["display_date"]
    canonical_path = f"/{key}/{slug(city)}/{page['date']}.html"
    canonical = SITE + canonical_path
    sessions = page.get("real_sessions", [])
    seated_offers = [o for o in page["offers"] if is_real_session(o)]
    anchors = {str(o.get("sourceAvailabilityBlock", {}).get("sessionId") or "") for o in seated_offers}
    matched_anchor_sessions = [s for s in sessions if str(s.get("session_id") or "") in anchors] or [
        s for s in sessions if str(s.get("registered_count") or "0") not in {"", "0"}
    ]
    anchor_sessions = [
        s for s in matched_anchor_sessions
        if str(s.get("registration_status") or "open").lower() not in {"closed", "full"}
        and s.get("public_direct_booking") is not False
    ]
    closed_session_ids = {
        str(s.get("session_id") or "") for s in matched_anchor_sessions if s not in anchor_sessions
    }
    seated_offers = [
        o for o in seated_offers
        if str(o.get("sourceAvailabilityBlock", {}).get("sessionId") or "") not in closed_session_ids
    ]
    expired = date.fromisoformat(page["date"]) < now
    open_appointments = [o for o in page["offers"] if not is_real_session(o)]
    full = bool(matched_anchor_sessions) and not seated_offers and not open_appointments
    state = "expired" if expired else "anchored" if seated_offers or anchor_sessions else "full" if full else "open"
    family_name = PAGE_NAMES.get(key, key.replace("_", " ").title())
    hub_path = HUB_PATHS.get(key, f"/{key}.html")
    agency = ", ".join(sorted({str(o.get("certifyingBody") or "") for o in page["offers"] if o.get("certifyingBody")})) or "910CPR"
    title = f"{family_name} in {city} on {display_date} | 910CPR"
    description = f"View current {family_name} start times in {city} for {display_date}. Register through 910CPR using live resolved availability."
    location = clean_location(str((page["offers"] or [{}])[0].get("location") or city))
    related = "".join(
        f'<a data-analytics-event="related_date" href="/{p["page_key"]}/{slug(p["city"])}/{p["date"]}.html"><strong>{escape(p["display_date"])}</strong><span>View availability</span></a>'
        for p in future_pages[:8]
    )
    upcoming = f'<div class="related-grid">{related}</div>' if related else "<p>New dates are added as availability is confirmed.</p>"
    if expired:
        schedule_html = f"""
          <section class="status-panel expired"><p class="eyebrow">This date has passed</p>
          <h2>Classes for {escape(datetime.fromisoformat(page["date"]).strftime("%B %#d" if __import__("os").name == "nt" else "%B %-d"))} have concluded.</h2>
          <p>View the next available {escape(family_name)} dates in {escape(city)}.</p></section>"""
    else:
        anchor_cards = []
        for offer in seated_offers:
            anchor_cards.append(f"""<a class="anchor-card" data-registration data-event="select_seated_class" data-anchor="true" href="{escape(str(offer.get("appointmentUrl") or offer.get("registrationUrl")))}">
              <span class="status-dot">Scheduled class — join this class</span><strong>{escape(str(offer["displayStartTime"]))}</strong>
              <span>{escape(str(offer["courseName"]))}</span><b>Reserve your seat</b></a>""")
        options = []
        seen = set()
        for offer in open_appointments:
            k = offer_key(offer)
            if k in seen:
                continue
            seen.add(k)
            options.append(f"""<a class="time-choice" data-registration data-event="select_appointment_time" data-anchor="false" href="{escape(str(offer["appointmentUrl"]))}">
              <strong>{escape(str(offer["displayStartTime"]))}</strong><span>{escape(str(offer["courseName"]))}</span><b>Choose this time</b></a>""")
        if anchor_cards:
            anchor_html = '<h2>Scheduled class — join this class</h2>' + "".join(anchor_cards)
        elif full:
            anchor_html = '<div class="status-panel full"><h2>This date is currently full</h2><p>Choose a nearby date below.</p></div>'
        else:
            anchor_html = '<div class="availability-note"><strong>Open scheduling day</strong><span>Choose any start time currently shown.</span></div>'
        option_html = (
            '<h2>Additional available start times</h2><div class="time-grid">' + "".join(options) + "</div>"
            if options else ("" if full else '<p class="muted">No additional start times are currently available.</p>')
        )
        schedule_html = f'<section class="schedule-card">{anchor_html}{option_html}</section>'
    breadcrumbs = {
        "@type": "BreadcrumbList",
        "@id": canonical + "#breadcrumbs",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": family_name, "item": SITE + hub_path},
            {"@type": "ListItem", "position": 3, "name": city, "item": f"{SITE}/course-at-city/{key}-{slug(city)}.html"},
            {"@type": "ListItem", "position": 4, "name": display_date, "item": canonical},
        ],
    }
    organization = {
        "@type": ["Organization", "LocalBusiness"],
        "@id": f"{SITE}/#organization",
        "name": "910CPR",
        "url": SITE + "/",
        "telephone": "+1-910-395-5193",
        "address": {"@type": "PostalAddress", "streetAddress": "4018 Shipyard Blvd", "addressLocality": "Wilmington", "addressRegion": "NC", "postalCode": "28403", "addressCountry": "US"},
    }
    graph = [organization, breadcrumbs, *course_schema(page, canonical, location)]
    graph.extend(event_schema(s) for s in matched_anchor_sessions)
    schema = json.dumps({"@context": "https://schema.org", "@graph": graph}, separators=(",", ":"))
    primary = seated_offers[0] if seated_offers else open_appointments[0] if open_appointments else None
    primary_cta = (
        f'<a class="primary-cta" data-registration data-event="{"select_seated_class" if is_real_session(primary) else "select_appointment_time"}" href="{escape(str(primary.get("appointmentUrl") or primary.get("registrationUrl")))}">{"Join the scheduled class" if is_real_session(primary) else "Choose a start time"}</a>'
        if primary and not expired else f'<a class="primary-cta" data-event="expired_date_recovery" href="#upcoming">View upcoming dates</a>'
    )
    return canonical_path, f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title><meta name="description" content="{escape(description)}"><meta name="robots" content="index,follow">
<link rel="canonical" href="{escape(canonical)}"><meta property="og:type" content="website"><meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}"><meta property="og:url" content="{escape(canonical)}"><meta property="og:image" content="{SITE}/images/910CPR_wave.jpg">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{escape(title)}"><meta name="twitter:description" content="{escape(description)}">
<meta name="twitter:image" content="{SITE}/images/910CPR_wave.jpg"><link rel="icon" href="/images/910CPR round __ PNG.png">
<link rel="stylesheet" href="/css/date-availability.css?v=20260724"><script type="application/ld+json">{schema}</script>{GTM_HEAD_SNIPPET}</head>
<body data-page-id="{escape(key)}-{escape(slug(city))}-{page['date']}" data-build-id="{escape(build_id)}" data-page-state="{state}">
{GTM_NOSCRIPT_SNIPPET}{data_layer_script(page, state)}
<header class="site-header"><a href="/" class="brand"><img src="/images/910CPR_wave.jpg" alt="910CPR"><span>Professional certification training</span></a><a data-event="click_phone" href="tel:+19103955193">{PHONE}</a></header>
<main><nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>›</span><a href="{hub_path}">{escape(family_name)}</a><span>›</span><span>{escape(display_date)}</span></nav>
<section class="hero"><div><p class="eyebrow">{escape(agency)} training · {escape(city)}, NC</p><h1>{escape(family_name)}</h1><p class="date-line">{escape(display_date)}</p>
<p class="location-line">{escape(location)}</p>{primary_cta}</div><img src="/images/{'0arc.png' if key == 'arc' else '0hsi.png' if key == 'hsi' else '0aha.png'}" alt="{escape(agency)} training identity"></section>
<section class="facts" aria-label="Course details"><div><span>Location</span><strong>{escape(city)}, NC</strong></div><div><span>Format</span><strong>In person / blended as listed</strong></div><div><span>Duration</span><strong>Shown by course</strong></div><div><span>Price</span><strong>Shown in registration</strong></div></section>
{schedule_html}
<section class="expectations"><div><p class="eyebrow">Before class</p><h2>Arrive ready to begin</h2><p>Plan to arrive a few minutes early. HeartCode students should bring proof that the required online portion is complete.</p></div>
<div><p class="eyebrow">After completion</p><h2>Credential processing</h2><p>Cards are processed after successful completion when roster details and course requirements are complete.</p></div></section>
<section class="trust"><img src="/images/111 aha-authorized-training-site.png" alt="Authorized training credentials"><div><p class="eyebrow">Local training you can verify</p><h2>910CPR in Wilmington</h2>
<p>{ADDRESS} · <a data-event="click_phone" href="tel:+19103955193">{PHONE}</a></p><p>Experienced local instructors and provider credentials are shown when confirmed. Read our <a href="https://www.google.com/maps/search/?api=1&query=910CPR%204018%20Shipyard%20Blvd%20Wilmington%20NC%2028403">Google reviews</a>.</p></div></section>
<section id="upcoming" class="upcoming"><p class="eyebrow">Related dates</p><h2>More {escape(family_name)} dates in {escape(city)}</h2>{upcoming}
<a class="text-link" data-event="view_more_dates" href="{FULL_SCHEDULE}">View the full schedule →</a></section>
</main><footer><span>© 910CPR</span><button id="copy-diagnostics" type="button">Copy page diagnostics</button></footer>
<script src="/assets/date-availability.js?v=20260724" defer></script></body></html>"""


def update_sitemap(paths: list[str]) -> None:
    if not SITEMAP.exists():
        return
    ElementTree.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    tree = ElementTree.parse(SITEMAP)
    root = tree.getroot()
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    existing = {str(node.text or "") for node in root.findall(f"{ns}url/{ns}loc")}
    for path in paths:
        url = SITE + path
        if url in existing:
            continue
        node = ElementTree.SubElement(root, f"{ns}url")
        ElementTree.SubElement(node, f"{ns}loc").text = url
        existing.add(url)
    tree.write(SITEMAP, encoding="utf-8", xml_declaration=True)


def build(output_root: Path, now: date) -> dict:
    pages, skipped = collect(now)
    previous = load_json(MANIFEST, {})
    prior_rows = previous.get("pages", []) if isinstance(previous, dict) else []
    build_id = datetime.now(TZ).isoformat(timespec="seconds")
    page_list = []
    seated_pages = set()
    sorted_pages = sorted(pages.values(), key=lambda p: (p["page_key"], p["city"], p["date"]))
    for page in sorted_pages:
        related = [p for p in sorted_pages if p["page_key"] == page["page_key"] and p["city"] == page["city"] and p["date"] > max(page["date"], now.isoformat())]
        path, html = render(page, related, now, build_id)
        target = output_root / path.lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        state = re.search(r'data-page-state="([^"]+)"', html).group(1)
        if state == "anchored":
            seated_pages.add(path)
        page_list.append({"path": path, "state": state, "page_key": page["page_key"], "city": page["city"], "date": page["date"]})
    if output_root == DOCS:
        for old in prior_rows:
            if old.get("path") not in {p["path"] for p in page_list}:
                old_path = DOCS / str(old.get("path") or "").lstrip("/")
                if old_path.exists() and str(old.get("date") or "") < now.isoformat():
                    page_list.append(old)
        manifest = {"schemaVersion": "date-availability-manifest.v1", "generatedAt": build_id, "pages": page_list}
        MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        update_sitemap([row["path"] for row in page_list])
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "generated_at": build_id,
            "date_pages_generated": len(page_list),
            "seated_class_pages_generated_by_date_builder": 0,
            "anchored_date_pages_generated": len(seated_pages),
            "real_session_landers_present": len(list((DOCS / "classes").glob("*.html"))) - int((DOCS / "classes" / "index.html").exists()),
            "skipped_empty_or_invalid_offers": skipped,
            "state_counts": dict(__import__("collections").Counter(row["state"] for row in page_list)),
            "examples": {state: next((SITE + row["path"] for row in page_list if row["state"] == state), None) for state in ("open", "anchored", "full", "expired")},
        }
        REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return {"date_pages_generated": len(page_list), "anchored_date_pages_generated": len(seated_pages), "seated_class_pages_generated": 0, "skipped_empty_or_invalid_offers": skipped}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DOCS)
    parser.add_argument("--now", default=datetime.now(TZ).date().isoformat())
    args = parser.parse_args()
    counts = build(args.output_root.resolve(), date.fromisoformat(args.now))
    print(json.dumps(counts, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
