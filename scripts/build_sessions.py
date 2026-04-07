import json
import os
from datetime import datetime

# ========= CONFIG =========
SCHEDULE_PATH = "data/schedule.json"
OUTPUT_DIR = "docs/classes"
FORCE_REBUILD = False   # flip to True if needed
SKIP_PRIVATE = True     # skip non-public sessions

# ========= HELPERS =========
def load_schedule():
    with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_existing_ids():
    files = os.listdir(OUTPUT_DIR)
    ids = set()
    for f in files:
        if f.endswith(".html"):
            ids.add(f.replace(".html", ""))
    return ids

def is_valid_session(session):
    if SKIP_PRIVATE and not session.get("public", True):
        return False

    # Skip garbage / corrupted names
    name = session.get("course_name", "")
    if not name or "̍" in name:
        return False

    return True

def build_html(session):
    session_id = str(session.get("id"))
    title = session.get("course_name", "CPR Class")
    start = session.get("start", "")
    location = session.get("location", "Wilmington, NC")
    register_url = session.get("register_url", "#")

    try:
        dt = datetime.fromisoformat(start)
        date_str = dt.strftime("%B %d, %Y")
        time_str = dt.strftime("%I:%M %p")
    except:
        date_str = start
        time_str = ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title} | 910CPR</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>

<h1>{title}</h1>

<p><strong>Date:</strong> {date_str}</p>
<p><strong>Time:</strong> {time_str}</p>
<p><strong>Location:</strong> {location}</p>

<a href="{register_url}">Register Now</a>

</body>
</html>
"""

def write_file(session_id, html):
    path = os.path.join(OUTPUT_DIR, f"{session_id}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

# ========= MAIN =========
def main():
    print("\n=== SESSION LANDER BUILDER ===\n")

    ensure_output_dir()
    schedule = load_schedule()
    existing_ids = get_existing_ids()

    built = 0
    skipped = 0

    for session in schedule:
        session_id = str(session.get("id"))

        if not session_id:
            print("⚠️ Missing session ID, skipping")
            skipped += 1
            continue

        if not is_valid_session(session):
            print(f"⏭️ Skipping invalid/private: {session_id}")
            skipped += 1
            continue

        filepath = os.path.join(OUTPUT_DIR, f"{session_id}.html")
        exists = os.path.exists(filepath)

        print(f"🔍 {session_id} → exists={exists}")

        if FORCE_REBUILD or not exists:
            html = build_html(session)
            write_file(session_id, html)
            print(f"✅ BUILT: {session_id}")
            built += 1
        else:
            print(f"✔️ OK: {session_id}")

    print("\n=== SUMMARY ===")
    print(f"Built: {built}")
    print(f"Skipped: {skipped}")
    print("Done.\n")


if __name__ == "__main__":
    main()