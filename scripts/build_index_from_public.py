import json
from datetime import datetime
import os

INPUT = "docs/data/public_schedule.json"
OUTPUT = "docs/schedule.html"

def load_sessions():
    with open(INPUT, "r", encoding="utf-8") as f:
        return json.load(f)

def format_dt(dt_str):
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%B %d, %Y"), dt.strftime("%I:%M %p")
    except:
        return dt_str, ""

def build_html(sessions):
    items = []

    for s in sessions[:100]:  # limit for sanity (adjust later)
        name = s.get("course_name", "CPR Class")
        start = s.get("start", "")
        sid = s.get("id")

        date, time = format_dt(start)

        items.append(f"""
<li>
  <a href="classes/{sid}.html">{name}</a><br>
  <small>{date} at {time}</small>
</li>
""")

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>CPR Class Schedule | 910CPR</title>
</head>
<body>

<h1>Available CPR Classes</h1>

<p>Total sessions: {len(sessions)}</p>

<ul>
{''.join(items)}
</ul>

</body>
</html>
"""

def main():
    print("Loading public schedule...")
    sessions = load_sessions()
    print(f"Sessions loaded: {len(sessions)}")

    html = build_html(sessions)

    os.makedirs("docs", exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Wrote: {OUTPUT}")

if __name__ == "__main__":
    main()