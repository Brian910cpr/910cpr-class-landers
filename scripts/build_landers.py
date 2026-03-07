import json
import os
import re
from html import unescape
from datetime import datetime

DATA_FILE = "../data/schedule.json"
OUTPUT_DIR = "../docs/classes"

PUBLIC_LOCATION = "Wilmington; Shipyard Blvd"
PUBLIC_SEATS_SENTINEL = 555

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

all_sessions = data["sessions"]


def strip_html(text: str) -> str:
    if text is None:
        return ""
    text = unescape(str(text))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_start(start_value: str):
    raw = str(start_value).strip()

    dt = None
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %I:%M %p",
    ):
        try:
            dt = datetime.strptime(raw, fmt)
            break
        except ValueError:
            pass

    if dt is None:
        return raw, "", ""

    display_date = dt.strftime("%B %d, %Y")
    display_time = dt.strftime("%I:%M %p").lstrip("0")
    iso_date = dt.strftime("%Y-%m-%d")
    return display_date, display_time, iso_date


def is_public(session: dict) -> bool:
    location = str(session.get("location", "")).strip()
    seats = session.get("seats")

    try:
        seats = int(seats) if seats is not None else None
    except Exception:
        seats = None

    if location == PUBLIC_LOCATION:
        return True

    if location != PUBLIC_LOCATION and seats == PUBLIC_SEATS_SENTINEL:
        return True

    return False


public_sessions = [s for s in all_sessions if is_public(s)]


def next_sessions(course_name: str, current_session_id):
    matches = []

    for s in public_sessions:
        if s.get("session_id") == current_session_id:
            continue
        if s.get("course") == course_name:
            matches.append(s)

    matches.sort(key=lambda item: str(item.get("start", "")))
    return matches[:10]


template = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{page_title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{meta_description}">

<style>
body {{
  font-family: Arial, sans-serif;
  background: linear-gradient(#f5f6f7, #e9eef2);
  margin: 0;
  padding: 40px 20px;
  color: #222;
}}

.wrap {{
  max-width: 960px;
  margin: 0 auto;
}}

.card {{
  background: #f1f1f1;
  border-radius: 14px;
  padding: 30px;
  box-shadow: 0 3px 12px rgba(0,0,0,0.15);
}}

.button {{
  display: inline-block;
  background: #2c73d2;
  color: white;
  padding: 14px 24px;
  border-radius: 10px;
  text-decoration: none;
  font-size: 16px;
  font-weight: bold;
}}

.button:hover {{
  background: #1f5ca8;
}}

h1, h2 {{
  margin-top: 0;
}}

ul {{
  padding-left: 20px;
}}

li {{
  margin-bottom: 10px;
}}

.muted {{
  color: #555;
}}

hr {{
  border: 0;
  border-top: 1px solid #ddd;
  margin: 28px 0;
}}
</style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <h1>{course_name}</h1>

    <p>
      <strong>Date:</strong> {display_date}<br>
      <strong>Time:</strong> {display_time}<br>
      <strong>Location:</strong> {location}
    </p>

    <p>Reserve your seat in this CPR certification class.</p>

    <p>
      <a class="button" href="{register_url}">Register Now</a>
    </p>

    <hr>

    <h2>Upcoming {course_name} Classes</h2>
    {upcoming_html}
  </div>
</div>
</body>
</html>
"""

count = 0

for s in public_sessions:
    session_id = s.get("session_id")
    course_raw = s.get("course", "CPR Class")
    course_name = strip_html(course_raw)
    location = str(s.get("location", "Wilmington NC")).strip()
    register_url = s.get("register_url", "#")
    start_value = s.get("start", "")

    display_date, display_time, iso_date = parse_start(start_value)

    upcoming = next_sessions(course_raw, session_id)

    if upcoming:
        upcoming_items = []
        for u in upcoming:
            u_date, u_time, _ = parse_start(u.get("start", ""))
            u_location = str(u.get("location", "")).strip()
            u_register = u.get("register_url", "#")
            upcoming_items.append(
                f'<li>{u_date} at {u_time} <span class="muted">• {u_location}</span> '
                f'<a href="{u_register}">Register</a></li>'
            )
        upcoming_html = "<ul>\n" + "\n".join(upcoming_items) + "\n</ul>"
    else:
        upcoming_html = "<p class=\"muted\">No additional upcoming public sessions found for this course right now.</p>"

    page_title = f"{course_name} | {location} | 910CPR"
    meta_description = f"{course_name} in {location}. View date and time and register online with 910CPR."

    filename = f"{session_id}.html"
    path = os.path.join(OUTPUT_DIR, filename)

    html = template.format(
        page_title=page_title,
        meta_description=meta_description,
        course_name=course_name,
        display_date=display_date,
        display_time=display_time,
        location=location,
        register_url=register_url,
        upcoming_html=upcoming_html,
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    count += 1

print(f"Finished building {count} PUBLIC landers.")