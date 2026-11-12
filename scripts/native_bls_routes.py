"""Gate-aware BLS links. Never changes inventory or treats a URL as a reservation."""
import json
from datetime import datetime, timezone
from urllib.parse import urlencode

SUPPORTED = frozenset({"209806", "359474", "210549", "509474"})
FULL = frozenset({"209806", "359474"})

def enabled(root):
    try:
        a = json.loads((root / "data/config/native_skills_activation.json").read_text(encoding="utf-8"))
        verified = datetime.fromisoformat(a["canonicalVerifiedAt"].replace("Z", "+00:00"))
        return (a.get("schemaVersion") == "native-skills-activation.v1" and a.get("enabled") is True
                and a.get("blsEnabled") is True and bool(a.get("evidence"))
                and verified.tzinfo is not None and verified <= datetime.now(timezone.utc))
    except (OSError, ValueError, TypeError, KeyError):
        return False

def course_link(root, course_id, legacy):
    cid = str(course_id or "")
    return "/bls.html?" + urlencode({"course": cid}) if cid in SUPPORTED and enabled(root) else legacy

def session_link(root, course_id, session_id, legacy):
    cid, sid = str(course_id or ""), str(session_id or "")
    # HeartCode's logical identity must remain a bundle selection, not be inferred
    # from an older physical class bearing that external course number.
    if cid in FULL and sid and enabled(root):
        import re
        if re.fullmatch(r"(?:[0-9]+|lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})", sid):
            return "/register/?" + urlencode({"session": sid})
    return course_link(root, cid, legacy) if cid in SUPPORTED and enabled(root) else legacy

def appointment_link(root, course_id, date, start_time, location, instructor, legacy):
    cid = str(course_id or "")
    if cid not in FULL or not enabled(root):
        return legacy
    return "/register/?" + urlencode({"course": cid, "date": date, "startTime": start_time,
        "location": location or "", "instructor": instructor or ""})
