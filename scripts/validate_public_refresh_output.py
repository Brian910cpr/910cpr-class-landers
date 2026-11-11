from __future__ import annotations

import json
import re
from hashlib import sha256
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit, parse_qs
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any
from scripts.canonical_scheduling_demand import load_publication_demand, resolve_canonical_demand


ROOT = Path(__file__).resolve().parents[1]
SCHEDULE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
CURRENT_SESSIONS_PATH = ROOT / "data" / "sessions_current.json"
ADMIN_SCHEDULE_PATH = ROOT / "docs" / "data" / "admin_schedule.json"
SELECTOR_DIR = ROOT / "docs" / "data" / "block-selector-availability"
REQUIRED_SELECTORS = ("bls", "heartsaver", "acls", "pals")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def session_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("sessions", "classes", "events"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, dict)]
    return []


def is_durable_admin_session(row: dict[str, Any]) -> bool:
    source = str(row.get("source") or "").strip().lower()
    native = (source == "landerware_event"
        and row.get("registration_backend") == "landerware"
        and str(row.get("session_id") or "").startswith("lw-")
        and row.get("count_available") is True
        and row.get("workspace_projection_status") == "current")
    return native or (bool(row.get("hot_sync")) and source.startswith("hot_sync"))


def validate_admin_reconciliation(current_payload: Any, admin_payload: Any) -> set[str]:
    hot_sync_source = (admin_payload.get("sources") or {}).get("hot_sync", {}) if isinstance(admin_payload, dict) else {}
    require(hot_sync_source.get("available") is True, "admin schedule was not reconciled with authoritative HOT_SYNC")
    current_ids = {
        str(row.get("session_id") or row.get("sessionId") or row.get("id") or "")
        for row in session_rows(current_payload)
        if row.get("session_id") or row.get("sessionId") or row.get("id")
    }
    admin_rows = session_rows(admin_payload)
    invalid_stale_ids = {
        str(row.get("session_id") or row.get("sessionId") or row.get("id") or "")
        for row in admin_rows
        if (row.get("session_id") or row.get("sessionId") or row.get("id"))
        and str(row.get("session_id") or row.get("sessionId") or row.get("id")) not in current_ids
        and not is_durable_admin_session(row)
    }
    require(not invalid_stale_ids, f"admin schedule contains stale sessions: {sorted(invalid_stale_ids)[:10]}")

    durable_lineages: list[str] = []
    for row in admin_rows:
        if not is_durable_admin_session(row):
            continue
        session_id = str(row.get("copied_from_session_id") or row.get("session_id") or "").strip()
        while session_id.startswith("manual-copy-"):
            session_id = session_id.removeprefix("manual-copy-")
        durable_lineages.append(session_id)
    duplicate_lineages = {lineage for lineage in durable_lineages if durable_lineages.count(lineage) > 1}
    require(not duplicate_lineages, f"admin schedule contains duplicate durable sessions: {sorted(duplicate_lineages)[:10]}")
    return {
        str(row.get("session_id") or row.get("sessionId") or row.get("id"))
        for row in admin_rows
        if row.get("session_id") or row.get("sessionId") or row.get("id")
    }


def validate_selector_lease(payload: dict, page_key: str, *, now=None) -> None:
    expiry = datetime.fromisoformat(str(payload.get("validUntil") or "").replace("Z", "+00:00"))
    require(expiry.tzinfo is not None, f"{page_key}: publication expiry lacks timezone")
    # Existing classes survive expired offer leases in both V2 finalization
    # and the browser. Only calculated offers depend on that availability proof.
    calculated = any(course.get('offerType') != 'seated_class'
                     for day in payload.get('dates', [])
                     for slot in day.get('startTimes', [])
                     for course in slot.get('courses', []))
    if calculated:
        require(expiry > (now or datetime.now(timezone.utc)), f"{page_key}: expired publication")


def validate_selector(page_key: str, public_session_ids: set[str], *, now=None) -> dict[str, int]:
    path = SELECTOR_DIR / f"{page_key}.json"
    payload = load_json(path)
    require(payload.get("schemaVersion") == "selector-resolved-availability.v1", f"{page_key}: invalid schema")
    require((payload.get("anchor_policy") or {}).get("finalized") is True, f"{page_key}: selector has not passed final policy")
    validate_selector_lease(payload, page_key, now=now)
    blocked = set(payload.get("synthesisBlockedDates", []))
    occupied = set(payload.get("occupiedDates", []))
    dates = payload.get("dates")
    require(isinstance(dates, list), f"{page_key}: dates must be a list")

    date_count = len(dates)
    start_count = 0
    offer_count = 0
    for day in dates:
        require(isinstance(day, dict) and day.get("date"), f"{page_key}: date row lacks date")
        starts = day.get("startTimes")
        require(isinstance(starts, list), f"{page_key}: startTimes must be a list")
        start_count += len(starts)
        for slot in starts:
            require(slot.get("startTime"), f"{page_key}: slot lacks startTime")
            courses = slot.get("courses")
            require(isinstance(courses, list) and courses, f"{page_key}: slot has no courses")
            offer_count += len(courses)
            for course in courses:
                for field in ("courseId", "courseName", "startTime", "location"):
                    require(course.get(field) not in (None, ""), f"{page_key}: offer lacks {field}")
                if course.get("offerType") == "seated_class":
                    # Public selector payloads are intentionally compact: they retain
                    # the seated identity as availabilityBlockId="seated:<session_id>"
                    # and expose the registration destination as appointmentUrl.
                    source_block = course.get("sourceAvailabilityBlock") or {}
                    session_id = str(source_block.get("sessionId") or "").strip()
                    block_id = str(course.get("availabilityBlockId") or "").strip()
                    if not session_id and block_id.startswith("seated:"):
                        session_id = block_id.removeprefix("seated:").strip()
                    require(session_id, f"{page_key}: seated offer lacks session identity")
                    require(session_id in public_session_ids, f"{page_key}: stale seated session {session_id}")
                    registration_url = course.get("registrationUrl") or course.get("appointmentUrl")
                    require(registration_url, f"{page_key}: seated session {session_id} lacks registration URL")
                    if course.get('authority') == 'native-heartsaver-session-booking.v1':
                        validate_native_heartsaver_seated(course, payload, page_key, day['date'], slot['startTime'], now=now)
                    if str(course.get('courseId')) == '509474':
                        validate_native_skills_offer(course, page_key, day['date'], slot['startTime'], payload, now=now)
                else:
                    require(day["date"] not in blocked, f"{page_key}: synthetic offer on unreconciled date {day['date']}")
                    require(day["date"] not in occupied or (
                        (course.get("schedule_role") or course.get("scheduleRole")) == "barnacle" and course.get("attached_to_session_id")
                    ), f"{page_key}: orphan synthetic offer on occupied date {day['date']}")
                    # matchedContainerId is an internal planning field and is omitted
                    # from the compact public selector contract.
                    if course.get('authority') == 'native-full-course.v2':
                        validate_native_full_offer(course, payload, page_key, day['date'], slot['startTime'], now=now)
                    elif str(course.get('courseId')) == '509474' or (page_key == 'bls' and str(course.get('courseId')) == '210549' and urlsplit(str(course.get('registrationUrl') or course.get('appointmentUrl') or '')).path == '/register/skills-session/'):
                        validate_native_skills_offer(course, page_key, day['date'], slot['startTime'], payload, now=now)
                    else:
                        for field in ("appointmentDayId", "appointmentUrl", "availabilityBlockId"):
                            require(course.get(field) not in (None, ""), f"{page_key}: dynamic offer lacks {field}")

    counts = payload.get("counts") or {}
    require(counts.get("publicSelectableDateCount") == date_count, f"{page_key}: date count mismatch")
    require(counts.get("publicSelectableStartTimeCount") == start_count, f"{page_key}: start count mismatch")
    require(counts.get("publicSelectableOfferCount") == offer_count, f"{page_key}: offer count mismatch")
    # A correctly closed feed must replace stale inventory even when it has no offers.
    return {"dates": date_count, "starts": start_count, "offers": offer_count}


def validate_native_full_offer(course: dict, payload: dict, page_key: str,
                               day: str, clock: str, *, now=None) -> None:
    """Native BLS v2 uses original first-party proof, never a legacy container."""
    label = 'native full: '
    from scripts.native_publication_scope import HEARTSAVER
    cid = course.get('courseId')
    heartsaver = cid in HEARTSAVER
    expected_page = 'heartsaver' if heartsaver else 'bls'
    require(page_key == expected_page and payload.get('pageKey') == expected_page, label+'invalid page')
    instruction = HEARTSAVER[cid]['instructionMinutes'] if heartsaver else 120
    cleanup = HEARTSAVER[cid]['cleanupMinutes'] if heartsaver else 30
    if heartsaver:
        require(course.get('coursePolicyKey') == 'heartsaver-full:'+cid+'.v1', label+'invalid course policy')
    require(course.get('authority') == 'native-full-course.v2' and
            course.get('nativeScopeId') == 'brian-shipyard-b.v1', label+'invalid authority or scope')
    require(course.get('courseId') in ({'209806','359474'} | set(HEARTSAVER)) and
            course.get('offerType') == 'dynamic_appointment' and course.get('publicSelectable') is True,
            label+'invalid course or selection state')
    for key,value in {'durationMinutes':instruction,'schedulerConsumptionMinutes':instruction+cleanup,
                      'cleanupBufferMinutes':cleanup,'setupBufferMinutes':0}.items():
        require(type(course.get(key)) is int and course[key] == value,label+'invalid '+key)
    require(course.get('instructor') == 'Brian Ennis' and
            course.get('resource') == ':: Wilmington; Shipyard Blvd - B' and
            course.get('location') == ':: Wilmington; Shipyard Blvd',label+'invalid instructor or resource')
    block, sources = course.get('availabilityBlockId'), course.get('sourceSessionIds')
    require(isinstance(block,str) and bool(block.strip()) and isinstance(sources,list) and
            all(isinstance(x,str) and x.strip() for x in sources) and len(sources)==len(set(sources)),
            label+'missing or invalid source trace')
    require('appointmentDayId' not in course and 'matchedContainerId' not in course,
            label+'unexpected legacy identity')
    require(course.get('date') == day and course.get('startTime') == clock and
            re.fullmatch(r'\d{4}-\d{2}-\d{2}',day) and re.fullmatch(r'\d{2}:\d{2}',clock),
            label+'inconsistent local date or time')
    local = datetime.fromisoformat(day+'T'+clock)
    require(local.minute % 15 == 0,label+'invalid start grid')
    zone = ZoneInfo('America/New_York')
    candidates = {local.replace(tzinfo=zone,fold=fold).astimezone(timezone.utc) for fold in (0,1)
                  if local.replace(tzinfo=zone,fold=fold).astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)==local}
    require(len(candidates)==1,label+'ambiguous or nonexistent Eastern time')
    start = next(iter(candidates))
    def instant(value):
        value = datetime.fromisoformat(str(value or '').replace('Z','+00:00'))
        require(value.tzinfo is not None,label+'timezone required')
        return value.astimezone(timezone.utc)
    current = instant(now or datetime.now(timezone.utc))
    observed,generated = instant(course.get('proofObservedAt')),instant(payload.get('generatedAt'))
    lease,publication_lease = instant(course.get('validUntil')),instant(payload.get('validUntil'))
    require(observed <= generated <= current < lease <= observed+timedelta(minutes=15),
            label+'original proof stale, future or extended')
    require(lease <= publication_lease,label+'offer lease exceeds publication')
    if heartsaver:
        calendar_observed, policy_observed = instant(course.get('calendarProofObservedAt')), instant(course.get('policyProofObservedAt'))
        require(observed == min(calendar_observed, policy_observed) and max(calendar_observed, policy_observed) <= generated,
                label+'invalid scoped proof')
    require(current+timedelta(hours=24) <= start <= current+timedelta(days=90),label+'outside lead or horizon')
    require(instant(course.get('occupiedUntil')) == start+timedelta(minutes=instruction+cleanup),label+'invalid occupied interval')
    selection = course.get('selectionId')
    require(isinstance(selection,str) and re.fullmatch(r'native-full:[a-f0-9]{64}',selection),label+'invalid selection identity')
    raw = '|'.join([course['nativeScopeId'],course['courseId'],start.isoformat(),
                    course['instructor'],course['resource'],str(instruction),str(instruction+cleanup)])
    require(selection == 'native-full:'+sha256(raw.encode()).hexdigest(),label+'selection identity mismatch')
    destination = course.get('registrationUrl')
    require(isinstance(destination,str) and destination.startswith('/register/skills-session/?') and
            not any(ord(ch)<32 or ord(ch)==127 for ch in destination) and '\\' not in destination and '#' not in destination,
            label+'invalid native destination')
    url = urlsplit(destination)
    require(not url.scheme and not url.netloc and not url.fragment and url.path == '/register/skills-session/',
            label+'invalid native destination')
    query = parse_qs(url.query,keep_blank_values=True,strict_parsing=True,max_num_fields=3)
    require(query == {'course':[course['courseId']],'selectionId':[selection]},label+'invalid native query')
    require('appointmentUrl' not in course or course['appointmentUrl'] == destination,
            label+'inconsistent registration destinations')


def validate_native_heartsaver_seated(course, payload, page_key, day, clock, *, now=None):
    from scripts.native_publication_scope import HEARTSAVER, SCOPE, instant
    label = 'native heartsaver seated: '
    cid, sid = course.get('courseId'), course.get('session_id')
    require(page_key == payload.get('pageKey') == 'heartsaver' and cid in HEARTSAVER, label+'invalid course or page')
    require(course.get('authority') == 'native-heartsaver-session-booking.v1' and course.get('nativeScopeId') == SCOPE
            and course.get('coursePolicyKey') == 'heartsaver-full:'+cid+'.v1'
            and course.get('offerType') == 'seated_class' and course.get('publicSelectable') is True, label+'invalid scope')
    require(isinstance(sid,str) and re.fullmatch(r'(?:[0-9]+|lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})',sid)
            and course.get('availabilityBlockId') == 'seated:'+sid and course.get('sourceSessionIds') == [sid], label+'invalid identity')
    require(re.fullmatch(r'[a-f0-9]{32}', str(course.get('identityWitness') or ''))
            and type(course.get('profileVersion')) is int and course['profileVersion'] > 0, label+'invalid canonical witness')
    require(all(type(course.get(k)) is int for k in ['capacity','remainingSeats'])
            and 0 < course['remainingSeats'] <= course['capacity'] <= 100, label+'invalid seats')
    instruction, cleanup = HEARTSAVER[cid]['instructionMinutes'], HEARTSAVER[cid]['cleanupMinutes']
    for key,value in {'durationMinutes':instruction,'cleanupBufferMinutes':cleanup,'setupBufferMinutes':0,'schedulerConsumptionMinutes':instruction+cleanup}.items():
        require(type(course.get(key)) is int and course[key] == value, label+'invalid geometry')
    require(course.get('date') == day and course.get('startTime') == clock, label+'invalid local time')
    local = datetime.fromisoformat(day+'T'+clock); zone = ZoneInfo('America/New_York')
    starts = {local.replace(tzinfo=zone,fold=fold).astimezone(timezone.utc) for fold in (0,1)
              if local.replace(tzinfo=zone,fold=fold).astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)==local}
    require(len(starts) == 1, label+'ambiguous or nonexistent local time')
    current = instant(now or datetime.now(timezone.utc)); start = next(iter(starts))
    observed, expiry = instant(course.get('proofObservedAt')), instant(course.get('validUntil'))
    require(observed <= instant(payload['generatedAt']) <= current < expiry <= observed+timedelta(minutes=15)
            and expiry <= instant(payload['validUntil']) and start > current
            and instant(course.get('occupiedUntil')) == start+timedelta(minutes=instruction+cleanup), label+'invalid original proof or interval')
    require(course.get('instructor') == 'Brian Ennis' and course.get('resource') == ':: Wilmington; Shipyard Blvd - B'
            and course.get('location') == ':: Wilmington; Shipyard Blvd', label+'invalid resource')
    require('appointmentDayId' not in course and 'matchedContainerId' not in course
            and course.get('registrationUrl') == course.get('appointmentUrl') == '/register/?session='+sid, label+'invalid native destination')


def validate_native_skills_offer(course: dict, page_key: str, day: str, clock: str, payload: dict | None = None, *, now: datetime | None = None) -> None:
    """Native skills use a leased canonical selection, never an Enrollware container."""
    require(page_key in {'heartsaver', 'arc', 'hsi', 'bls'}, 'native skills: invalid page context')
    require(course.get('publicSelectable') is True, 'native skills: not selectable')
    for key, value in {'durationMinutes':45, 'schedulerConsumptionMinutes':60,
                       'cleanupBufferMinutes':15, 'setupBufferMinutes':0}.items():
        require(type(course.get(key)) is int and course[key] == value, 'native skills: invalid '+key)
    require(course.get('instructor') == 'Brian Ennis' and
            course.get('resource') == ':: Wilmington; Shipyard Blvd - B' and
            course.get('location') == ':: Wilmington; Shipyard Blvd', 'native skills: invalid resource or instructor')
    require(bool(course.get('availabilityBlockId')) and isinstance(course.get('sourceSessionIds'), list),
            'native skills: missing source trace')
    require(course.get('date') == day and course.get('startTime') == clock, 'native skills: inconsistent date or time')
    lease = datetime.fromisoformat(str(course.get('validUntil') or '').replace('Z', '+00:00'))
    now = now or datetime.now(timezone.utc)
    require(lease.tzinfo is not None and lease > now, 'native skills: expired lease')
    start = datetime.fromisoformat(day+'T'+clock).replace(tzinfo=ZoneInfo('America/New_York')).astimezone(timezone.utc)
    end = datetime.fromisoformat(str(course.get('occupiedUntil') or '').replace('Z', '+00:00'))
    require(end.tzinfo is not None and end == start+timedelta(minutes=60), 'native skills: invalid occupied interval')
    url = urlsplit(str(course.get('registrationUrl') or course.get('appointmentUrl') or ''))
    query = parse_qs(url.query)
    require(not url.scheme and not url.netloc and not url.fragment and url.path == '/register/skills-session/',
            'native skills: invalid native destination')
    course_id = str(course.get('courseId') or '509474')
    require(course_id == '509474' or course_id == '210549' and page_key == 'bls', 'native skills: invalid course')
    for key, value in {'course':course_id, 'date':day, 'startTime':clock,
                       'instructor':course['instructor'], 'location':course['location']}.items():
        require(query.get(key) == [value], 'native skills: mismatched URL '+key)
    require(not course.get('appointmentDayId') and 'appointmentDayId' not in query,
            'native skills: unexpected Enrollware container')
    if course.get('authority') or course.get('nativeOfferId') or course.get('nativeScopeId') or course.get('offerType') == 'seated_class':
        from scripts.native_publication_scope import SKILLS_AUTHORITY, SKILLS_CONTEXTS, SCOPE
        seated = course.get('authority') == 'native-skills-seated.v1'
        require(course.get('authority') in {SKILLS_AUTHORITY, 'native-skills-seated.v1'} and course.get('nativeScopeId') == SCOPE,
                'native skills: invalid authority or scope')
        require(page_key in SKILLS_CONTEXTS and course_id == '509474', 'native skills: unsupported first-party course')
        require('appointmentDayId' not in course and 'matchedContainerId' not in course,
                'native skills: unexpected external identity')
        require(course.get('offerType') == ('seated_class' if seated else 'dynamic_appointment'), 'native skills: wrong offer kind')
        if seated:
            sid = course.get('session_id')
            require(isinstance(sid, str) and re.fullmatch(r'(?:[0-9]+|lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})', sid)
                and course.get('nativeOfferId') == 'native-skills-seated:'+sid
                and course.get('availabilityBlockId') == 'seated:'+sid and course.get('sourceSessionIds') == [sid]
                and re.fullmatch(r'[a-f0-9]{32}', str(course.get('identityWitness') or ''))
                and type(course.get('profileVersion')) is int and course['profileVersion'] > 0
                and type(course.get('remainingSeats')) is int and 1 <= course['remainingSeats'] <= 2,
                'native skills: invalid seated proof')
        else:
            require(re.fullmatch(r'native-skills:[a-f0-9]{64}', str(course.get('nativeOfferId') or '')) is not None,
                    'native skills: invalid native identity')
            raw = '|'.join([course['nativeScopeId'], '509474', start.isoformat(), course['instructor'], course['resource'], '45', '60'])
            require(course['nativeOfferId'] == 'native-skills:'+sha256(raw.encode()).hexdigest(),
                    'native skills: native identity mismatch')
        local = datetime.fromisoformat(day+'T'+clock)
        zone = ZoneInfo('America/New_York')
        candidates = {local.replace(tzinfo=zone,fold=fold).astimezone(timezone.utc) for fold in (0,1)
                      if local.replace(tzinfo=zone,fold=fold).astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)==local}
        require(len(candidates) == 1, 'native skills: ambiguous or nonexistent Eastern time')
        block, sources = course.get('availabilityBlockId'), course.get('sourceSessionIds')
        require(isinstance(block,str) and bool(block.strip()) and isinstance(sources,list) and
                all(isinstance(x,str) and x.strip() for x in sources) and len(sources)==len(set(sources)),
                'native skills: invalid source trace')
        destination = course.get('registrationUrl')
        require(isinstance(destination,str) and destination.startswith('/register/skills-session/?') and
                not any(ord(ch)<32 or ord(ch)==127 for ch in destination) and '\\' not in destination and '#' not in destination,
                'native skills: invalid native destination')
        require(parse_qs(url.query,keep_blank_values=True,strict_parsing=True,max_num_fields=5) == {
                    'course':['509474'], 'date':[day], 'startTime':[clock],
                    'instructor':[course['instructor']], 'location':[course['location']]},
                'native skills: invalid native query')
        require('appointmentUrl' not in course or course['appointmentUrl'] == destination,
                'native skills: inconsistent registration destinations')
        contexts = course.get('skillsContexts')
        require(isinstance(contexts, list) and bool(contexts), 'native skills: missing contexts')
        expected_contexts = sorted(set(contexts) & set(SKILLS_CONTEXTS[page_key])) if seated else sorted(SKILLS_CONTEXTS[page_key])
        require(course.get('qualificationPolicy') == 'skills-session-policy.v1' and course.get('capacity') == 2
                and contexts == expected_contexts, 'native skills: invalid canonical context policy')
        require(isinstance(payload, dict), 'native skills: original publication proof required')
        observed = datetime.fromisoformat(str(course.get('proofObservedAt') or '').replace('Z', '+00:00'))
        generated = datetime.fromisoformat(str(payload.get('generatedAt') or '').replace('Z', '+00:00'))
        publication_lease = datetime.fromisoformat(str(payload.get('validUntil') or '').replace('Z', '+00:00'))
        require(all(value.tzinfo is not None for value in (observed, generated, publication_lease)) and
                observed <= generated <= now < lease <= observed+timedelta(minutes=15) and
                lease <= publication_lease <= generated+timedelta(minutes=15),
                'native skills: original proof expired or extended')
        require(now+timedelta(hours=24) <= start <= now+timedelta(days=90) and start.minute % 15 == 0,
                'native skills: invalid native horizon or grid')


def validate_non_session_publication(root: Path, demand: dict[str, Any]) -> None:
    ids = {str(row["external_class_id"]) for row in demand.get("non_session_sources", [])}
    for name in ("schedule_future.json", "admin_schedule.json"):
        rows = session_rows(load_json(root / "docs/data" / name))
        leaked = ids & {str(row.get("external_session_id") or row.get("session_id")) for row in rows}
        require(not leaked, f"{name}: classified non-sessions were published: {sorted(leaked)}")
    calendar = (root / "docs/data/landerware.ics").read_text(encoding="utf-8")
    for external_id in ids:
        require(not (root / "docs/classes" / f"{external_id}.html").exists(), f"Classified non-session page remains: {external_id}")
        require(f"-{external_id}@" not in calendar, f"Classified non-session calendar block remains: {external_id}")


def validate_public_demand(rows: list[dict[str, Any]], demand: dict[str, Any]) -> None:
    """Fail closed on roster *counts* without freezing fresh occupancy.

    The public schedule and selector blockers must stay current even when the
    canonical participant projection is temporarily stale or incomplete. Unknown
    demand may therefore publish only as unknown: it must not carry an
    authoritative registration count or promote an Anchor. Enrollware remains the
    registration destination for these seated classes and enforces its own seat
    availability.
    """
    resolved, _ = resolve_canonical_demand(rows, demand["sessions"])
    unknown: list[str] = []
    unsafe_counts: list[str] = []

    for published, current in zip(rows, resolved):
        if current.get("count_available") is True:
            continue

        session_id = str(
            current.get("session_id")
            or published.get("session_id")
            or published.get("external_session_id")
            or "unknown"
        )
        status = str(current.get("demand_status") or "unknown")
        unknown.append(f"{session_id}: {status}")

        published_count = published.get("active_registration_count")
        published_basis = str(published.get("demand_basis") or "").strip()
        published_available = published.get("count_available")
        if (
            published_count is not None
            or published_available is True
            or published_basis == "canonical_active_registrations"
        ):
            unsafe_counts.append(f"{session_id}: {status}")

    require(
        not unsafe_counts,
        "Refusing publication because unknown canonical demand is still exposed "
        "as an authoritative registration count for: "
        + "; ".join(unsafe_counts),
    )

    if unknown:
        print(
            "::warning title=Canonical demand unavailable::"
            "Publishing fresh occupied-session timing with participant counts "
            "failed closed for: "
            + "; ".join(unknown)
        )


def main() -> int:
    schedule = load_json(SCHEDULE_PATH)
    rows = session_rows(schedule)
    require(rows, "schedule_future.json contains no public sessions")
    public_session_ids = {
        str(row.get("session_id") or row.get("sessionId") or row.get("id") or "")
        for row in rows
        if row.get("session_id") or row.get("sessionId") or row.get("id")
    }

    admin_ids = validate_admin_reconciliation(load_json(CURRENT_SESSIONS_PATH), load_json(ADMIN_SCHEDULE_PATH))
    demand = load_publication_demand(ROOT)
    validate_public_demand(rows, demand)
    validate_non_session_publication(ROOT, demand)

    results = {page_key: validate_selector(page_key, public_session_ids) for page_key in REQUIRED_SELECTORS}
    print(f"Validated public sessions: {len(public_session_ids)}")
    print(f"Validated admin sessions: {len(admin_ids)}")
    for page_key, counts in results.items():
        print(f"{page_key}: dates={counts['dates']} starts={counts['starts']} offers={counts['offers']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
