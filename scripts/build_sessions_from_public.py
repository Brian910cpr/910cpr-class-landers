import json
import os
from datetime import datetime

INPUT = "docs/data/public_schedule.json"
OUTPUT_DIR = "docs/classes"

def load_sessions():
    with open(INPUT, "r", encoding="utf-8") as f:
        return json.load(f)

def format_dt(dt_str):
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%B %d, %Y"), dt.strftime("%I:%M %p")
    except:
        return dt_str, ""

def build_html(s):
    sid = s.get("id")
    name = s.get("course_name", "CPR Class")
    start = s.get("start", "")
    location = s.get("location", "Wilmington, NC")
    register = s.get("register_url", "#")

    date, time = format_dt(start)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{name} | 910CPR</title>
</head>
<body>

<h1>{name}</h1>

<p><strong>Date:</strong> {date}</p>
<p><strong>Time:</strong> {time}</p>
<p><strong>Location:</strong> {location}</p>

<a href="{register}">Register Now</a>

</body>
</html>
"""

def main():
    print("Building session landers...")

    sessions = load_sessions()
    print(f"Sessions loaded: {len(sessions)}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    built = 0

    for s in sessions:
        sid = str(s.get("id"))
        if not sid:
            continue

        path = os.path.join(OUTPUT_DIR, f"{sid}.html")

        html = build_html(s)

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

        built += 1

    print(f"Landers built: {built}")

if __name__ == "__main__":
    main()