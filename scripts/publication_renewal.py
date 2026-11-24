"""Read-only renewal check for public selector publication leases."""
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.audit_family_publication_coverage import FAMILIES

def _expiry(value):
    if not isinstance(value, str):
        raise ValueError("missing or invalid lease")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("lease requires timezone")
    return parsed

def publication_needs_renewal(directory, now, margin_minutes=45):
    """Check every family and every rendered dynamic offer; never modify leases."""
    if now.tzinfo is None:
        raise ValueError("now requires timezone")
    renew_before = now + timedelta(minutes=margin_minutes)
    for family in FAMILIES:
        try:
            payload = json.loads((directory / (family + ".json")).read_text(encoding="utf-8"))
            if _expiry(payload.get("validUntil")) <= renew_before:
                return True
            dates = payload["dates"]
            if not isinstance(dates, list):
                return True
            for date in dates:
                starts = date["startTimes"]
                if not isinstance(starts, list):
                    return True
                for start in starts:
                    courses = start["courses"]
                    if not isinstance(courses, list):
                        return True
                    for course in courses:
                        kind = course.get("offerType")
                        if kind == "seated_class":
                            continue
                        if kind != "dynamic_appointment" or _expiry(course.get("validUntil")) <= renew_before:
                            return True
        except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError):
            return True
    return False

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--margin-minutes", type=int, default=45)
    parser.add_argument("--directory", type=Path, default=Path("docs/data/block-selector-availability"))
    args = parser.parse_args()
    if args.margin_minutes < 0:
        parser.error("margin must be nonnegative")
    print("true" if publication_needs_renewal(args.directory, datetime.now(timezone.utc), args.margin_minutes) else "false")

if __name__ == "__main__":
    main()
