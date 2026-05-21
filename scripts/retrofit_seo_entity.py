import json
import re
from datetime import datetime
from html import escape, unescape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CLASSES = DOCS / "classes"
SITE_BASE = "https://www.910cpr.com"
IDENTITY = "910CPR is an Authorized American Heart Association Training Site serving Coastal North Carolina."
FULL_IDENTITY = "Authorized American Heart Association Training Site providing CPR, BLS, ACLS, PALS & Heartsaver courses throughout Coastal North Carolina."
PROHIBITED = re.compile(r"\b(?:American Heart Association\s+)?AHA?\s*Training Center\b|American Heart Association Training Center", re.I)
UNIQUENESS_VARIANTS = [
    "This page preserves the individual date, start time, city, registration URL, and class identifier for this exact session.",
    "Use this page to compare this specific session against nearby class dates before continuing to the registration checkout.",
    "The class record is intentionally kept separate from other dates so students can confirm the exact session details.",
    "This session page carries its own canonical URL, event schema, and registration route for the listed class ID.",
    "The schedule details here are tied to this single class occurrence rather than a generic course listing.",
]


def strip_html(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(str(value or "")))).strip()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_if_changed(path: Path, original: str, updated: str) -> bool:
    updated = "\n".join(line.rstrip() for line in updated.splitlines()) + "\n"
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def parse_json_ld_blocks(text: str) -> list[tuple[str, dict]]:
    out = []
    for block in re.findall(r'(<script[^>]+type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)', text, re.I | re.S):
        prefix, body, suffix = block
        try:
            data = json.loads(body.strip())
        except Exception:
            continue
        if isinstance(data, dict):
            out.append((prefix + body + suffix, data))
    return out


def event_schema(text: str) -> dict:
    for _raw, data in parse_json_ld_blocks(text):
        if data.get("@type") == "Event":
            return data
    return {}


def page_context_value(text: str, key: str) -> str:
    match = re.search(rf'{re.escape(key)}:\s*"([^"]*)"', text)
    return match.group(1).replace('\\"', '"') if match else ""


def first(pattern: str, text: str) -> str:
    match = re.search(pattern, text, re.I | re.S)
    return strip_html(match.group(1)) if match else ""


def session_id_from_path(path: Path) -> str:
    return path.stem if re.fullmatch(r"\d+", path.stem) else ""


def parse_date(value: str) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def family(course: str) -> str:
    lower = course.lower()
    if "acls" in lower:
        return "ACLS"
    if "pals" in lower:
        return "PALS"
    if "bls" in lower:
        return "BLS"
    if "heartsaver" in lower:
        return "Heartsaver"
    if "first aid" in lower:
        return "First Aid"
    if "hsi" in lower:
        return "HSI"
    if "red cross" in lower or "arc" in lower:
        return "ARC"
    return "CPR"


def city_from_location(location: str) -> str:
    clean = strip_html(location)
    if clean.startswith("::"):
        clean = clean[2:].strip()
    if ";" in clean:
        return clean.split(";", 1)[0].strip() or "Wilmington"
    match = re.search(r"([A-Za-z .'-]+),\s*[A-Z]{2}\b", clean)
    if match:
        return match.group(1).strip()
    for city in ("Wilmington", "Holly Ridge", "Jacksonville", "Burgaw", "Leland", "Southport", "Myrtle Grove"):
        if city.lower() in clean.lower():
            return city
    return clean.split(",", 1)[0].strip() or "Wilmington"


def daypart(dt: datetime | None) -> str:
    if not dt:
        return "Scheduled"
    if dt.weekday() >= 5:
        return "Weekend"
    if dt.hour < 12:
        return "Morning"
    if dt.hour < 17:
        return "Afternoon"
    return "Evening"


def title_for(session_id: str, course: str, dt: datetime | None, city: str) -> str:
    fam = family(course)
    weekday = dt.strftime("%A") if dt else "Upcoming"
    date_part = f"{dt.strftime('%b')} {dt.day}, {dt.year}" if dt else f"Session {session_id}"
    suffix = "HeartCode Skills Session" if re.search(r"heartcode|skills", course, re.I) else ("Renewal Course" if re.search(r"renewal", course, re.I) else "Class")
    return f"{weekday} {daypart(dt)} {fam} {suffix} in {city} - {date_part} Class {session_id} | 910CPR"


def uniqueness_variant(session_id: str) -> str:
    try:
        index = int(session_id) % len(UNIQUENESS_VARIANTS)
    except Exception:
        index = 0
    return UNIQUENESS_VARIANTS[index]


def session_signature_sentence(session_id: str) -> str:
    digest = f"{int(session_id or '0'):08x}" if str(session_id or "").isdigit() else "00000000"
    words_a = ["morning-ready", "skills-focused", "coastal", "provider", "workplace", "classroom", "certification", "schedule"]
    words_b = ["Wilmington", "Holly Ridge", "Jacksonville", "Burgaw", "Leland", "Southport", "Myrtle Grove", "Coastal NC"]
    words_c = ["check-in", "hands-on", "registration", "event", "course", "roster", "seat", "skills"]
    picks = [
        words_a[int(digest[0], 16) % len(words_a)],
        words_b[int(digest[1], 16) % len(words_b)],
        words_c[int(digest[2], 16) % len(words_c)],
        words_a[int(digest[3], 16) % len(words_a)],
        words_b[int(digest[4], 16) % len(words_b)],
        words_c[int(digest[5], 16) % len(words_c)],
    ]
    return f"Session reference {session_id} uses the local context markers {', '.join(picks)} to keep this event record distinct."


def h1_for(session_id: str, course: str, dt: datetime | None, city: str) -> str:
    fam = family(course)
    weekday = dt.strftime("%A") if dt else "Upcoming"
    date_part = f" on {dt.strftime('%b')} {dt.day}" if dt else ""
    return f"{weekday} {daypart(dt)} {fam} Class in {city}{date_part} - Class {session_id}"


def replace_or_insert(pattern: str, replacement: str, text: str, insert_before: str = "</head>") -> str:
    if re.search(pattern, text, re.I | re.S):
        return re.sub(pattern, replacement, text, count=1, flags=re.I | re.S)
    return text.replace(insert_before, replacement + "\n" + insert_before, 1)


def update_event_schema(text: str, self_url: str, register_url: str, course: str, city: str, dt: datetime | None) -> str:
    for raw, data in parse_json_ld_blocks(text):
        if data.get("@type") != "Event":
            continue
        data["@id"] = f"{self_url}#event"
        data["url"] = self_url
        if register_url:
            data["sameAs"] = register_url
            offer = data.get("offers") if isinstance(data.get("offers"), dict) else {"@type": "Offer"}
            offer["url"] = register_url
            data["offers"] = offer
        data["organizer"] = {"@type": "Organization", "name": "910CPR", "url": f"{SITE_BASE}/"}
        base_desc = strip_html(data.get("description") or "")
        base_desc = re.sub(r"^(?:[A-Z][A-Za-z /|&+-]+ in [A-Za-z .'-]+ on [A-Za-z]+ \d{1,2}, \d{4}\. Authorized American Heart Association Training Site providing CPR, BLS, ACLS, PALS & Heartsaver courses throughout Coastal North Carolina\.\s*)+", "", base_desc).strip()
        date_text = dt.strftime("%B %d, %Y").replace(" 0", " ") if dt else "the listed date"
        data["description"] = f"{family(course)} in {city} on {date_text}. {FULL_IDENTITY} {base_desc}".strip()
        replacement = '<script type="application/ld+json">\n' + json.dumps(data, indent=2) + "\n</script>"
        return text.replace(raw, replacement, 1)
    return text


def retrofit_class_page(path: Path) -> bool:
    original = read(path)
    text = PROHIBITED.sub("AHA Training Site", original)
    sid = session_id_from_path(path)
    if not sid:
        return write_if_changed(path, original, text)
    self_url = f"{SITE_BASE}/classes/{sid}.html"
    event = event_schema(text)
    course = page_context_value(text, "course_name") or strip_html(event.get("name") or first(r"<h1[^>]*>(.*?)</h1>", text)) or "CPR Class"
    location = page_context_value(text, "location_name") or strip_html((event.get("location") or {}).get("name") if isinstance(event.get("location"), dict) else "")
    city = city_from_location(location)
    dt = parse_date(str(event.get("startDate") or ""))
    register_url = page_context_value(text, "register_url") or ""
    if not register_url:
        offer = event.get("offers") if isinstance(event.get("offers"), dict) else {}
        register_url = str(offer.get("url") or event.get("sameAs") or "")
    page_title = title_for(sid, course, dt, city)
    page_h1 = h1_for(sid, course, dt, city)
    date_text = dt.strftime("%A, %B %d, %Y").replace(" 0", " ") if dt else "the listed date"
    time_text = dt.strftime("%I:%M %p").lstrip("0") if dt else "the listed time"
    meta = f"{family(course)} session {sid} in {city} on {date_text} at {time_text}. View details and continue to secure registration with 910CPR."

    text = replace_or_insert(r"<title[^>]*>.*?</title>", f"<title>{escape(page_title)}</title>", text)
    text = replace_or_insert(r'<meta[^>]+name=["\']description["\'][^>]*>', f'<meta name="description" content="{escape(meta, quote=True)}">', text)
    text = replace_or_insert(r'<meta[^>]+name=["\']robots["\'][^>]*>', '<meta name="robots" content="index,follow">', text)
    text = replace_or_insert(r'<link[^>]+rel=["\']canonical["\'][^>]*>', f'<link rel="canonical" href="{self_url}">', text)
    text = re.sub(r"<h1[^>]*>.*?</h1>", f"<h1>{escape(page_h1)}</h1>", text, count=1, flags=re.I | re.S)
    text = update_event_schema(text, self_url, register_url, course, city, dt)

    intro = f"""
<section class="section-box session-intro-block">
  <h2>This Session</h2>
  <p>This {daypart(dt).lower()} {family(course)} session, class ID {escape(sid)}, is scheduled in {escape(city)} on {escape(date_text)} at {escape(time_text)} for students and professionals who need a distinct class record and a reliable registration path.</p>
  <p>{escape(uniqueness_variant(sid))}</p>
  <p>{escape(session_signature_sentence(sid))}</p>
  <p>{IDENTITY}</p>
</section>
"""
    if "session-intro-block" not in text:
        text = re.sub(r'(<section class="section-box course-description-priority">)', intro + r"\n\1", text, count=1)
    else:
        text = re.sub(
            r'<section[^>]+class=["\'][^"\']*session-intro-block[^"\']*["\'][^>]*>.*?</section>',
            intro,
            text,
            count=1,
            flags=re.I | re.S,
        )

    if "session-faq-block" not in text:
        faq = """
<section class="section-box session-faq-block">
  <h2>Session FAQ</h2>
  <details><summary>When should I arrive?</summary><p>Arrive a few minutes before the listed start time so check-in does not shorten class time.</p></details>
  <details><summary>Where do I register?</summary><p>Use the Continue to Registration button on this class page for the secure Enrollware registration path.</p></details>
  <details><summary>When are cards issued?</summary><p>Cards are processed after successful completion and verified roster details.</p></details>
</section>
"""
        text = text.replace('<div class="build-stamp">', faq + '\n<div class="build-stamp">', 1)

    return write_if_changed(path, original, text)


def retrofit_identity_page(path: Path) -> bool:
    original = read(path)
    text = PROHIBITED.sub("AHA Training Site", original)
    page_rel = path.relative_to(DOCS).as_posix()
    expected = f"{SITE_BASE}/" if page_rel == "index.html" else f"{SITE_BASE}/{page_rel}"
    text = replace_or_insert(r'<meta[^>]+name=["\']robots["\'][^>]*>', '<meta name="robots" content="index,follow">', text)
    text = replace_or_insert(r'<link[^>]+rel=["\']canonical["\'][^>]*>', f'<link rel="canonical" href="{expected}">', text)
    if re.search(r"Authorized American Heart Association Training Site|AHA Training Site", text, re.I):
        return write_if_changed(path, original, text)
    snippet = f'\n<p class="entity-identity">{IDENTITY}</p>\n'
    if "</main>" in text:
        text = text.replace("</main>", snippet + "</main>", 1)
    elif "</body>" in text:
        text = text.replace("</body>", snippet + "</body>", 1)
    return write_if_changed(path, original, text)


def main() -> None:
    changed = 0
    class_pages = 0
    for path in sorted(CLASSES.glob("*.html")):
        if not re.fullmatch(r"\d+\.html", path.name):
            continue
        class_pages += 1
        if retrofit_class_page(path):
            changed += 1
    other_pages = 0
    for path in sorted(DOCS.rglob("*.html")):
        if path.parent == CLASSES and re.fullmatch(r"\d+\.html", path.name):
            continue
        other_pages += 1
        if retrofit_identity_page(path):
            changed += 1
    print(f"SEO/entity retrofit scanned {class_pages} class pages and {other_pages} other pages; changed {changed} files.")


if __name__ == "__main__":
    main()
