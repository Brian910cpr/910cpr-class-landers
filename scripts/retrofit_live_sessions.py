from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
CLASSES_DIR = ROOT / "docs" / "classes"
TZ = ZoneInfo("America/New_York")
SCRIPT_TAG = '<script src="/assets/live-sessions.js"></script>'
UPCOMING_SECTION_PATTERN = re.compile(
    r'<section id="upcoming-times" class="section-box(?: js-live-session-group)?"[^>]*>.*?</section>',
    flags=re.S,
)
UPCOMING_CARD_PATTERN = re.compile(
    r'<div class="upcoming-card\b[^>]*>.*?<div class="upcoming-actions">.*?</div>\s*</div>',
    flags=re.S,
)


def session_start_iso(card_html: str) -> str:
    data_match = re.search(r'data-session-start="([^"]+)"', card_html)
    if data_match:
        return data_match.group(1).strip()

    date_match = re.search(r'<div class="upcoming-date">([^<]+)</div>', card_html)
    time_match = re.search(r'<div class="upcoming-time">([^<]+)</div>', card_html)
    if not date_match or not time_match:
        return ""

    raw = f"{date_match.group(1).strip()} {time_match.group(1).strip()}"
    try:
        dt = datetime.strptime(raw, "%B %d, %Y %I:%M %p").replace(tzinfo=TZ)
    except ValueError:
        return ""
    return dt.isoformat()


def parse_session_start(card_html: str) -> datetime | None:
    iso_value = session_start_iso(card_html)
    if not iso_value:
        return None
    try:
        dt = datetime.fromisoformat(iso_value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)


def ensure_session_card_attrs(card_html: str, start: datetime) -> str:
    iso_value = start.isoformat()
    updated_card = card_html

    if "js-session-item" not in updated_card:
        updated_card = re.sub(
            r'<div class="upcoming-card\b([^"]*)"',
            lambda m: f'<div class="upcoming-card{m.group(1)} js-session-item"',
            updated_card,
            count=1,
        )

    if 'data-session-start="' not in updated_card:
        updated_card = re.sub(
            r'<div class="upcoming-card\b([^>]*)>',
            lambda m: f'<div class="upcoming-card{m.group(1)} data-session-start="{iso_value}">',
            updated_card,
            count=1,
        )

    return updated_card


def retrofit_upcoming_section(section_html: str, now: datetime) -> str:
    heading_match = re.search(r"(<div class=\"upcoming-head\">\s*<h2>Upcoming Classes</h2>\s*</div>|<h2>Upcoming Classes</h2>)", section_html)
    heading_html = heading_match.group(1) if heading_match else "<h2>Upcoming Classes</h2>"

    footer_match = re.search(
        r'<div class="upcoming-footer-link">\s*<a class="text-link strong-link" href="([^"]+)">([^<]+)</a>\s*</div>',
        section_html,
        flags=re.S,
    )
    empty_link = ""
    empty_label = "See full schedule for this course"
    if footer_match:
        empty_link = footer_match.group(1)
        empty_label = footer_match.group(2)
    else:
        data_link_match = re.search(r'data-empty-link="([^"]+)"', section_html)
        data_label_match = re.search(r'data-empty-link-label="([^"]+)"', section_html)
        if data_link_match:
            empty_link = data_link_match.group(1)
        if data_label_match:
            empty_label = data_label_match.group(1)

    cards = []
    for card_html in UPCOMING_CARD_PATTERN.findall(section_html):
        start = parse_session_start(card_html)
        if not start or start <= now:
            continue
        cards.append((start, ensure_session_card_attrs(card_html, start)))

    cards.sort(key=lambda item: item[0])
    rendered_cards = "".join(card for _, card in cards)

    section_attrs = ""
    if empty_link:
        section_attrs = (
            f' class="section-box js-live-session-group" data-empty-link="{empty_link}" '
            f'data-empty-link-label="{empty_label}"'
        )
    else:
        section_attrs = ' class="section-box js-live-session-group"'

    if not cards:
        footer_html = ""
        if empty_link:
            footer_html = (
                '\n<div class="upcoming-footer-link">\n'
                f'  <a class="text-link strong-link" href="{empty_link}">{empty_label}</a>\n'
                '</div>'
            )
        return (
            f'<section id="upcoming-times"{section_attrs}>\n'
            f'  {heading_html}\n'
            '  <p>No upcoming times are currently listed. See full schedule for this course.</p>'
            f'{footer_html}\n'
            '</section>'
        )

    footer_html = ""
    if empty_link:
        footer_html = (
            '\n  <div class="upcoming-footer-link">\n'
            f'    <a class="text-link strong-link" href="{empty_link}">{empty_label}</a>\n'
            '  </div>'
        )

    return (
        f'<section id="upcoming-times"{section_attrs}>\n'
        f'  {heading_html}\n'
        '  <div class="upcoming-grid">\n'
        f'{rendered_cards}\n'
        '  </div>'
        f'{footer_html}\n'
        '</section>'
    )


def retrofit_html(html: str, now: datetime) -> str:
    updated = html.replace(
        '<a class="button secondary" href="#upcoming-times">See Other Upcoming Class Times</a>',
        "",
    )

    updated = UPCOMING_SECTION_PATTERN.sub(
        lambda match: retrofit_upcoming_section(match.group(0), now),
        updated,
        count=1,
    )

    if SCRIPT_TAG not in updated and "</body>" in updated:
        updated = updated.replace("</body>", f"{SCRIPT_TAG}\n</body>", 1)

    return updated


def main() -> None:
    changed = 0
    now = datetime.now(TZ)
    for path in sorted(CLASSES_DIR.glob("*.html")):
        original = path.read_text(encoding="utf-8")
        updated = retrofit_html(original, now)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    print(f"Retrofitted class pages: {changed}")


if __name__ == "__main__":
    main()
