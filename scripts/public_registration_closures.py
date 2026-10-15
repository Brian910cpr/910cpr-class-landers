"""Explicit reversible owner closures; projection only, never cancel source facts."""
from copy import deepcopy
from datetime import datetime, timedelta
import json
from pathlib import Path
from zoneinfo import ZoneInfo

POLICY_PATH = Path(__file__).resolve().parents[1]/'docs/data/public-registration-closures.json'
ZONE = ZoneInfo('America/New_York')


def instant(value):
    result = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    return result.replace(tzinfo=ZONE) if result.tzinfo is None else result


def load_closures():
    if not POLICY_PATH.exists():
        return []
    policy = json.loads(POLICY_PATH.read_text(encoding='utf-8'))
    if policy.get('schemaVersion') != 'public-registration-closures.v1':
        raise ValueError('invalid public closure policy')
    closures = policy['closures']
    for closure in closures:
        if instant(closure['endsAt']) <= instant(closure['startsAt']):
            raise ValueError('invalid public closure interval')
    return closures


def overlaps_closure(start, end, closures):
    start, end = instant(start), instant(end)
    return any(start < instant(c['endsAt']) and end > instant(c['startsAt']) for c in closures)


def apply_closures(feed, closures=None):
    """Filter both new appointments and extra seats, including overnight overlap.

    Canonical sessions, landscape occupancy and existing registrations remain
    untouched. This public feed guard is not an external checkout guarantee.
    """
    closures = load_closures() if closures is None else closures
    result = deepcopy(feed)
    removed = []
    dates = []
    for day in result.get('dates', []):
        times = []
        for slot in day.get('startTimes', []):
            courses = []
            start = instant(day['date']+'T'+slot['startTime'])
            for course in slot.get('courses', []):
                duration = max(1, int(course.get('schedulerConsumptionMinutes') or course.get('durationMinutes') or 1))
                end = course.get('occupiedUntil') or start+timedelta(minutes=duration)
                if overlaps_closure(start, end, closures):
                    removed.append(dict(date=day['date'], startTime=slot['startTime'], courseId=course.get('courseId')))
                else:
                    courses.append(course)
            if courses:
                slot['courses'] = courses
                times.append(slot)
        if times:
            day['startTimes'] = times
            dates.append(day)
    result['dates'] = dates
    if 'offers' in result:
        allowed = {(d['date'], t['startTime'], str(c.get('courseId')))
                   for d in dates for t in d['startTimes'] for c in t['courses']}
        result['offers'] = [o for o in result['offers']
            if (o.get('date'), o.get('startTime'), str(o.get('courseId'))) in allowed]
    result['counts'] = dict(result.get('counts', {}),
        publicSelectableDateCount=len(dates),
        publicSelectableStartTimeCount=sum(len(d['startTimes']) for d in dates),
        publicSelectableOfferCount=sum(len(t['courses']) for d in dates for t in d['startTimes']))
    result['registrationClosures'] = deepcopy(closures)
    return result, removed


if __name__ == '__main__':
    # Surgical emergency projection: no scheduling generator or source refresh.
    for path in sorted((POLICY_PATH.parent/'block-selector-availability').glob('*.json')):
        original = json.loads(path.read_text(encoding='utf-8'))
        result, removed = apply_closures(original)
        path.write_text(json.dumps(result, separators=(',', ':'), ensure_ascii=False)+'\n', encoding='utf-8')
        print(f'{path.name}: removed {len(removed)} choices; preserved {result["counts"]["publicSelectableOfferCount"]}')
