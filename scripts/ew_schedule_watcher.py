import requests
import json
import time
from pathlib import Path

BASE_URL = "https://coastalcprtraining.enrollware.com/registration/schedule-feed.ashx?courseid="

COURSE_FILE = Path("scripts/course_ids.json")
CURRENT_FILE = Path("data/sessions_current.json")
PREVIOUS_FILE = Path("data/sessions_previous.json")


def load_course_ids():
    with open(COURSE_FILE) as f:
        return json.load(f)


def fetch_course_sessions(course_id):
    url = BASE_URL + str(course_id)

    r = requests.get(url)
    r.raise_for_status()

    data = r.text

    # strip jsonp wrapper
    start = data.find("(") + 1
    end = data.rfind(")")
    json_data = json.loads(data[start:end])

    sessions = {}

    for item in json_data:
        sid = str(item["id"])

        sessions[sid] = {
            "course_id": course_id,
            "url": item.get("url"),
            "location": item.get("location"),
            "times": item.get("dateTimes"),
            "seats": item.get("seatsLeft"),
            "closed": item.get("closed")
        }

    return sessions


def fetch_all_sessions():

    course_ids = load_course_ids()

    all_sessions = {}

    for cid in course_ids:
        try:
            sessions = fetch_course_sessions(cid)
            all_sessions.update(sessions)
        except Exception as e:
            print("Feed error for course", cid, e)

        time.sleep(0.5)

    return all_sessions


def load_previous():

    if not PREVIOUS_FILE.exists():
        return {}

    with open(PREVIOUS_FILE) as f:
        return json.load(f)


def save_current(data):

    with open(CURRENT_FILE, "w") as f:
        json.dump(data, f, indent=2)


def rotate_snapshots():

    if CURRENT_FILE.exists():
        CURRENT_FILE.rename(PREVIOUS_FILE)


def diff_sessions(previous, current):

    prev_ids = set(previous.keys())
    curr_ids = set(current.keys())

    new_sessions = curr_ids - prev_ids
    removed_sessions = prev_ids - curr_ids
    common_sessions = prev_ids & curr_ids

    changed_sessions = []

    for sid in common_sessions:

        if previous[sid] != current[sid]:
            changed_sessions.append(sid)

    return new_sessions, removed_sessions, changed_sessions


def main():

    previous = load_previous()

    current = fetch_all_sessions()

    save_current(current)

    new_sessions, removed_sessions, changed_sessions = diff_sessions(previous, current)

    print("New sessions:", len(new_sessions))
    print("Removed sessions:", len(removed_sessions))
    print("Changed sessions:", len(changed_sessions))

    print("\nNEW")
    for s in new_sessions:
        print(s)

    print("\nREMOVED")
    for s in removed_sessions:
        print(s)

    print("\nCHANGED")
    for s in changed_sessions:
        print(s)

    rotate_snapshots()


if __name__ == "__main__":
    main()