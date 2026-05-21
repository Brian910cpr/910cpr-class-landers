import json
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from html import unescape
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DEBUG = ROOT / "debug"
SITE_BASE = "https://www.910cpr.com"

SESSION_GLOB = "classes/*.html"
PROHIBITED = re.compile(r"\bAHA\s+Training\s+Center\b|\bAmerican\s+Heart\s+Association\s+Training\s+Center\b", re.I)
IDENTITY = re.compile(r"Authorized American Heart Association Training Site|AHA Training Site|910CPR is an Authorized", re.I)
ENTITY_LANGUAGE = re.compile(r"910CPR|Coastal North Carolina|Coastal NC|Wilmington|Holly Ridge|Jacksonville|Burgaw|Leland", re.I)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def rel(path: Path) -> str:
    return path.relative_to(DOCS).as_posix()


def strip_tags(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(text or ""))).strip()


def first_match(pattern: str, text: str, flags: int = re.I | re.S) -> str:
    match = re.search(pattern, text, flags)
    return strip_tags(match.group(1)) if match else ""


def canonical(text: str) -> str:
    return first_match(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']', text)


def title(text: str) -> str:
    return first_match(r"<title[^>]*>(.*?)</title>", text)


def h1(text: str) -> str:
    return first_match(r"<h1[^>]*>(.*?)</h1>", text)


def meta_description(text: str) -> str:
    return first_match(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', text)


def intro_copy(text: str) -> str:
    return first_match(r'<section[^>]+class=["\'][^"\']*session-intro-block[^"\']*["\'][^>]*>(.*?)</section>', text)


def faq_set(text: str) -> list[str]:
    block = first_match(r'<section[^>]+class=["\'][^"\']*session-faq-block[^"\']*["\'][^>]*>(.*?)</section>', text)
    return sorted(re.findall(r"<summary[^>]*>(.*?)</summary>", block, re.I | re.S))


def json_ld_blocks(text: str) -> list[dict]:
    blocks = re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', text, re.I | re.S)
    parsed = []
    for block in blocks:
        try:
            data = json.loads(block.strip())
        except Exception:
            continue
        if isinstance(data, list):
            parsed.extend(item for item in data if isinstance(item, dict))
        elif isinstance(data, dict):
            parsed.append(data)
    return parsed


def schema_types(item: dict) -> list[str]:
    value = item.get("@type")
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)] if value else []


def event_schemas(text: str) -> list[dict]:
    events = []
    for item in json_ld_blocks(text):
        if "Event" in schema_types(item):
            events.append(item)
        graph = item.get("@graph")
        if isinstance(graph, list):
            events.extend(node for node in graph if isinstance(node, dict) and "Event" in schema_types(node))
    return events


def duplicate_values(records: list[dict], key: str) -> list[dict]:
    buckets: dict[str, list[str]] = defaultdict(list)
    for record in records:
        value = record.get(key) or ""
        if value:
            buckets[value].append(record["path"])
    return [{"value": value, "pages": pages[:25], "count": len(pages)} for value, pages in buckets.items() if len(pages) > 1]


def load_sitemap_urls() -> set[str]:
    path = DOCS / "sitemap.xml"
    if not path.exists():
        return set()
    try:
        root = ET.fromstring(read(path))
    except Exception:
        return set()
    urls = set()
    for node in root.iter():
        if node.tag.endswith("loc") and node.text:
            urls.add(node.text.strip())
    return urls


def html_pages() -> list[Path]:
    return [path for path in DOCS.rglob("*.html") if path.is_file()]


def session_pages() -> list[Path]:
    return sorted(path for path in DOCS.glob(SESSION_GLOB) if re.fullmatch(r"\d+\.html", path.name))


def write_json(name: str, payload: dict) -> None:
    DEBUG.mkdir(parents=True, exist_ok=True)
    (DEBUG / name).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def audit_entity_identity(pages: list[Path]) -> None:
    missing_identity = []
    prohibited = []
    missing_entity_language = []
    for path in pages:
        text = read(path)
        path_rel = rel(path)
        if PROHIBITED.search(text):
            prohibited.append(path_rel)
        if not IDENTITY.search(text):
            missing_identity.append(path_rel)
        if not ENTITY_LANGUAGE.search(text):
            missing_entity_language.append(path_rel)
    write_json(
        "entity_identity_audit.json",
        {
            "summary": {
                "pages_scanned": len(pages),
                "pages_missing_aha_training_site_identity": len(missing_identity),
                "pages_using_training_center": len(prohibited),
                "pages_missing_910cpr_entity_language": len(missing_entity_language),
            },
            "pages_missing_aha_training_site_identity": missing_identity[:500],
            "pages_using_training_center": prohibited,
            "pages_missing_910cpr_entity_language": missing_entity_language[:500],
        },
    )


def audit_session_uniqueness(sessions: list[Path]) -> None:
    records = []
    for path in sessions:
        text = read(path)
        records.append(
            {
                "path": rel(path),
                "title": title(text),
                "h1": h1(text),
                "meta_description": meta_description(text),
                "intro_copy": intro_copy(text),
                "faq_key": " | ".join(faq_set(text)),
            }
        )
    similarity = []
    for index, left in enumerate(records[:2000]):
        for right in records[index + 1 : min(index + 75, len(records))]:
            ratio = SequenceMatcher(None, left["intro_copy"], right["intro_copy"]).ratio() if left["intro_copy"] and right["intro_copy"] else 0
            if ratio >= 0.997:
                similarity.append({"left": left["path"], "right": right["path"], "intro_similarity": round(ratio, 3)})
                if len(similarity) >= 250:
                    break
        if len(similarity) >= 250:
            break
    write_json(
        "session_uniqueness_audit.json",
        {
            "summary": {"session_pages_scanned": len(records), "similarity_warnings": len(similarity)},
            "repeated_titles": duplicate_values(records, "title"),
            "repeated_h1s": duplicate_values(records, "h1"),
            "duplicate_meta_descriptions": duplicate_values(records, "meta_description"),
            "pages_with_identical_intro_copy": duplicate_values(records, "intro_copy"),
            "pages_with_identical_faq_sets": duplicate_values(records, "faq_key"),
            "session_to_session_similarity_warnings": similarity,
        },
    )


def audit_schema_inventory(pages: list[Path], sessions: list[Path]) -> None:
    session_set = {rel(path) for path in sessions}
    pages_with_event = []
    hubs_with_event = []
    sessions_missing_event = []
    sessions_missing_unique_id = []
    sessions_missing_canonical = []
    pages_without_event = []
    for path in pages:
        text = read(path)
        path_rel = rel(path)
        events = event_schemas(text)
        if events:
            pages_with_event.append(path_rel)
        else:
            pages_without_event.append(path_rel)
        if path_rel in session_set:
            self_url = f"{SITE_BASE}/{path_rel}"
            if not events:
                sessions_missing_event.append(path_rel)
            if not canonical(text):
                sessions_missing_canonical.append(path_rel)
            for event in events:
                if event.get("@id") != f"{self_url}#event" or event.get("url") != self_url:
                    sessions_missing_unique_id.append(path_rel)
                    break
        elif events:
            hubs_with_event.append(path_rel)
    write_json(
        "schema_inventory_audit.json",
        {
            "summary": {
                "pages_scanned": len(pages),
                "pages_with_event_schema": len(pages_with_event),
                "hubs_accidentally_emitting_event_schema": len(hubs_with_event),
                "session_pages_missing_event_schema": len(sessions_missing_event),
            },
            "pages_with_event_schema": pages_with_event[:1000],
            "pages_without_event_schema": pages_without_event[:1000],
            "hubs_accidentally_emitting_event_schema": hubs_with_event,
            "session_pages_missing_event_schema": sessions_missing_event,
            "session_pages_missing_unique_event_id_or_url": sessions_missing_unique_id,
            "session_pages_missing_canonical": sessions_missing_canonical,
        },
    )


def audit_canonical_alignment(pages: list[Path]) -> None:
    sitemap_urls = load_sitemap_urls()
    canonical_targets = defaultdict(list)
    mismatch = []
    missing_self = []
    sitemap_mismatch = []
    for path in pages:
        text = read(path)
        path_rel = rel(path)
        expected = f"{SITE_BASE}/{path_rel}" if path_rel != "index.html" else f"{SITE_BASE}/"
        found = canonical(text)
        if found:
            canonical_targets[found].append(path_rel)
        if not found or found != expected:
            mismatch.append({"page": path_rel, "canonical": found, "expected": expected})
        if not found:
            missing_self.append(path_rel)
        if expected in sitemap_urls and found and found != expected:
            sitemap_mismatch.append({"sitemap_url": expected, "canonical": found, "page": path_rel})
    duplicate_targets = [{"canonical": key, "pages": value[:25], "count": len(value)} for key, value in canonical_targets.items() if len(value) > 1]
    write_json(
        "canonical_alignment_audit.json",
        {
            "summary": {
                "pages_scanned": len(pages),
                "canonical_mismatches": len(mismatch),
                "sitemap_url_vs_canonical_mismatches": len(sitemap_mismatch),
                "duplicate_canonical_targets": len(duplicate_targets),
                "pages_lacking_self_canonical": len(missing_self),
            },
            "canonical_mismatch": mismatch[:1000],
            "sitemap_url_vs_canonical_url_mismatch": sitemap_mismatch,
            "duplicate_canonical_targets": duplicate_targets[:500],
            "pages_lacking_self_canonical": missing_self[:1000],
        },
    )


def audit_hub_routing(pages: list[Path], sessions: set[str]) -> None:
    direct = []
    session_links = []
    missing_session_urls = []
    forward_flags = []
    for path in pages:
        path_rel = rel(path)
        if path_rel.startswith("classes/"):
            continue
        text = read(path)
        if "Book Seat" not in text and "Register" not in text and "finder-pill" not in text:
            continue
        anchors = re.findall(r'<a\b[^>]*\shref=["\']([^"\']+)["\']', text, re.I)
        for href in anchors:
            if "coastalcprtraining.enrollware.com/enroll" in href:
                direct.append({"page": path_rel, "href": href})
            if re.search(r"/classes/\d+\.html", href):
                record = {"page": path_rel, "href": href}
                session_links.append(record)
                if "#ForwardToEnrollware" in href:
                    forward_flags.append(record)
        if "data-session-id" in text and not any(re.search(r"/classes/\d+\.html", href) for href in anchors):
            missing_session_urls.append(path_rel)
    write_json(
        "hub_routing_audit.json",
        {
            "summary": {
                "hub_pages_scanned": len([p for p in pages if not rel(p).startswith("classes/")]),
                "hub_cards_linking_directly_to_enrollware": len(direct),
                "hub_cards_linking_to_session_pages": len(session_links),
                "cards_missing_session_urls": len(missing_session_urls),
                "cards_with_forward_to_enrollware_flag": len(forward_flags),
            },
            "hub_cards_linking_directly_to_enrollware": direct[:1000],
            "hub_cards_linking_to_session_pages": session_links[:1000],
            "cards_missing_session_urls": missing_session_urls[:500],
            "cards_with_forward_to_enrollware_flag": forward_flags[:1000],
        },
    )


def main() -> None:
    pages = html_pages()
    sessions = session_pages()
    audit_entity_identity(pages)
    audit_session_uniqueness(sessions)
    audit_schema_inventory(pages, sessions)
    audit_canonical_alignment(pages)
    audit_hub_routing(pages, {rel(path) for path in sessions})
    print(f"SEO/entity audits written to {DEBUG}")


if __name__ == "__main__":
    main()
