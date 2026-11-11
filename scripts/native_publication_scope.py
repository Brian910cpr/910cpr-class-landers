"""Default-off first-party scope adapter. No network, persistence, or scheduler.

The existing interval-subtraction/layered scheduler owns candidate generation.
This module replaces ONLY legacy container bounds and appointment identities.
"""
import json
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo('America/New_York')
SAFE_SKIPS = {'outside_export_window', 'excluded_by_exdate',
              'suppressed_by_recurrence_override', 'duplicate_generated_occurrence',
              'duplicate_explicit_event_same_uid_start'}
SCOPE = 'brian-shipyard-b.v1'
COURSES = {'209806', '359474'}
HEARTSAVER = {
    '209809': {'canonicalCourseId': '23dfcfa7-4224-46ed-8d45-64d43d5425db', 'instructionMinutes': 120, 'cleanupMinutes': 30},
    '344085': {'canonicalCourseId': '306bc81a-0e09-49e1-8910-e05501222eb4', 'instructionMinutes': 90, 'cleanupMinutes': 15},
}
HEARTSAVER_PROOF = 'native-heartsaver-publication-policy.v1'
SKILLS_CONTEXTS = {
    'heartsaver': {'cpr-aed': '209808', 'first-aid-cpr-aed': '329495'},
    'arc': {'arc-blended': '372258'},
    'hsi': {'hsi-blended': '445670'},
}
SKILLS_AUTHORITY = 'native-skills-publication.v1'
SKILLS_QUALIFICATION_POLICY = 'skills-session-policy.v1'


def instant(value):
    dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('timezone_required')
    return dt.astimezone(timezone.utc)


def active(policy):
    return policy.get('enabled') is True and policy.get('schemaVersion') == 'native-publication-scope.v1'



def skills_active(policy, page_key):
    return active(policy) and policy.get('skillsEnabled') is True and page_key in SKILLS_CONTEXTS


def skills_offer_fields(policy, candidate, report, window, now, course, page_key):
    """Versioned skills envelope; canonical qualification/capacity is rechecked at claim.

    Four contexts and Brian's shared skills qualification come from the existing
    20261107112218 skills-session-policy.v1 contract, never inferred certification.
    """
    if not skills_active(policy, page_key):
        return None
    if policy.get('scopeId') != SCOPE or str(candidate.get('course')) != '509474':
        raise ValueError('unsupported_native_skills_course')
    option = course.get('schedule_page_option', {})
    contexts = {c.get('key'): c.get('template_course_id') for c in option.get('skills_contexts', [])}
    if (contexts != SKILLS_CONTEXTS[page_key] or option.get('native_registration_path') != '/register/skills-session/'
            or option.get('scheduling_template_course_id') not in contexts.values()
            or course.get('kind') != 'skills' or course.get('default_capacity') != 2
            or course.get('duration_minutes') != 45 or course.get('cleanup_buffer_minutes') != 15
            or course.get('scheduler_consumption_minutes') != 60):
        raise ValueError('native_skills_context_policy_mismatch')
    if not any(candidate == c for c in report.get('accepted', [])):
        raise ValueError('accepted_engine_candidate_required')
    if (candidate.get('instructor') != 'Brian Ennis' or window.get('person_id') != 'instructor_24057895173'
            or candidate.get('location') != ':: Wilmington; Shipyard Blvd - B'
            or window.get('location_name') != ':: Wilmington; Shipyard Blvd'
            or not report.get('availability_window') or not isinstance(candidate.get('source_ids'), list)):
        raise ValueError('native_skills_candidate_identity_mismatch')
    if (window.get('native_publication_scope_id') != SCOPE
            or not isinstance(window.get('native_calendar_source_ids'), list)
            or 'brian_do_not_schedule' not in window['native_calendar_source_ids']):
        raise ValueError('native_skills_first_party_window_required')
    now, start, end = instant(now), instant(candidate['start']), instant(candidate['end'])
    teaching_end = instant(candidate['instruction_end'])
    observed = min(instant(report['native_proof_observed_at']), instant(window['native_proof_observed_at']))
    lease = min(instant(report['valid_until']), instant(window['native_valid_until']))
    if not observed <= now < lease <= observed+timedelta(minutes=15):
        raise ValueError('native_original_proof_expired_or_extended')
    if (start < now+timedelta(hours=24) or start > now+timedelta(days=90)
            or teaching_end-start != timedelta(minutes=45) or end-start != timedelta(minutes=60)):
        raise ValueError('native_skills_timing_invalid')
    local = start.astimezone(EASTERN)
    if local.minute % 15 or local.second or local.microsecond:
        raise ValueError('native_start_grid_invalid')
    # Physical identity stays stable across refreshes and provider pages. Context
    # is added by the service's exact-selection reader, not manufactured here.
    raw = '|'.join([SCOPE, '509474', start.isoformat(), candidate['instructor'], candidate['location'], '45', '60'])
    return {'authority': SKILLS_AUTHORITY, 'nativeScopeId': SCOPE,
            'nativeOfferId': 'native-skills:' + sha256(raw.encode()).hexdigest(),
            'qualificationPolicy': SKILLS_QUALIFICATION_POLICY,
            'skillsContexts': sorted(contexts), 'capacity': 2,
            'validUntil': lease.isoformat(), 'proofObservedAt': observed.isoformat(),
            'registrationUrl': '/register/skills-session/?' + urlencode({
                'course': '509474', 'date': local.date().isoformat(), 'startTime': local.strftime('%H:%M'),
                'instructor': candidate['instructor'], 'location': window['location_name']})}

def heartsaver_active(policy, page_key='heartsaver'):
    return active(policy) and policy.get('heartsaverFullEnabled') is True and page_key == 'heartsaver'


def validate_heartsaver_proof(proof, now):
    """Service-only source proof. Config/cached page capacities are never authority."""
    if not isinstance(proof, dict) or proof.get('schemaVersion') != HEARTSAVER_PROOF or set(proof.get('courses', {})) != set(HEARTSAVER):
        raise ValueError('native_heartsaver_policy_proof_required')
    observed, lease, now = instant(proof['observedAt']), instant(proof['validUntil']), instant(now)
    if not observed <= now < lease <= observed+timedelta(minutes=15):
        raise ValueError('native_heartsaver_policy_proof_expired_or_extended')
    for cid, expected in HEARTSAVER.items():
        policy = proof['courses'][cid]
        if not isinstance(policy, dict) or any(type(policy.get(k)) is not bool for k in ('materializationEnabled', 'nativePublicationEnabled')):
            raise ValueError('native_heartsaver_policy_invalid')
        if not policy['materializationEnabled'] or not policy['nativePublicationEnabled']:
            continue
        if (any(policy.get(k) != v or type(policy.get(k)) != type(v) for k,v in expected.items())
                or policy.get('coursePolicyKey') != 'heartsaver-full:'+cid+'.v1'
                or policy.get('nativeScopeId') != SCOPE or policy.get('pageKey') != 'heartsaver'
                or type(policy.get('maxStudents')) is not int or not 1 <= policy['maxStudents'] <= 100
                or instant(policy['qualificationValidThrough']) <= now):
            raise ValueError('native_heartsaver_policy_invalid')
    return proof


def heartsaver_course_policy(proof, course_id, now, through=None):
    proof = validate_heartsaver_proof(proof, now)
    policy = proof['courses'].get(str(course_id), {})
    if not policy.get('materializationEnabled') or not policy.get('nativePublicationEnabled'):
        return None
    if through is not None and instant(policy['qualificationValidThrough']) < instant(through):
        return None
    return policy


def heartsaver_offer_fields(policy, candidate, report, window, now, course):
    if not heartsaver_active(policy):
        return None
    cid = str(candidate.get('course'))
    if policy.get('scopeId') != SCOPE or cid not in HEARTSAVER or course.get('kind') != 'full':
        raise ValueError('unsupported_native_heartsaver_course')
    proof = policy.get('_heartsaverProof')
    backend = heartsaver_course_policy(proof, cid, now, candidate['end'])
    if not backend:
        raise ValueError('native_heartsaver_course_not_ready')
    if not any(candidate == c for c in report.get('accepted', [])):
        raise ValueError('accepted_engine_candidate_required')
    if (candidate.get('instructor') != 'Brian Ennis' or window.get('person_id') != 'instructor_24057895173'
            or candidate.get('location') != ':: Wilmington; Shipyard Blvd - B'
            or window.get('location_name') != ':: Wilmington; Shipyard Blvd'
            or not report.get('availability_window') or not isinstance(candidate.get('source_ids'), list)
            or window.get('native_publication_scope_id') != SCOPE
            or not isinstance(window.get('native_calendar_source_ids'), list)
            or 'brian_do_not_schedule' not in window['native_calendar_source_ids']):
        raise ValueError('native_heartsaver_candidate_identity_mismatch')
    now, start, end = instant(now), instant(candidate['start']), instant(candidate['end'])
    teaching_end = instant(candidate['instruction_end'])
    calendar_observed = min(instant(report['native_proof_observed_at']), instant(window['native_proof_observed_at']))
    observed = min(calendar_observed, instant(proof['observedAt']))
    lease = min(instant(report['valid_until']), instant(window['native_valid_until']), instant(proof['validUntil']))
    instruction, cleanup = backend['instructionMinutes'], backend['cleanupMinutes']
    if not observed <= now < lease <= observed+timedelta(minutes=15):
        raise ValueError('native_original_proof_expired_or_extended')
    if (start < now+timedelta(hours=24) or start > now+timedelta(days=90)
            or teaching_end-start != timedelta(minutes=instruction) or end-start != timedelta(minutes=instruction+cleanup)):
        raise ValueError('native_heartsaver_timing_invalid')
    local = start.astimezone(EASTERN)
    if local.minute % 15 or local.second or local.microsecond:
        raise ValueError('native_start_grid_invalid')
    raw = '|'.join([SCOPE, cid, start.isoformat(), candidate['instructor'], candidate['location'], str(instruction), str(instruction+cleanup)])
    selection = 'native-full:' + sha256(raw.encode()).hexdigest()
    return {'authority': 'native-full-course.v2', 'nativeScopeId': SCOPE, 'coursePolicyKey': backend['coursePolicyKey'],
            'selectionId': selection, 'validUntil': lease.isoformat(), 'proofObservedAt': observed.isoformat(),
            'calendarProofObservedAt': calendar_observed.isoformat(), 'policyProofObservedAt': proof['observedAt'],
            'registrationUrl': '/register/skills-session/?'+urlencode({'course': cid, 'selectionId': selection})}


def inverse_bounds(policy, source, calendars, snapshot, now, validate_event):
    """Return finite first-party bounds, never an inferred empty-calendar window.

    validate_event is the existing event_time_validation(source,event) function.
    All active configured calendars owned by Brian must be complete and fresh.
    No default business hours are imposed; current owner policy permits overnight.
    """
    if not active(policy):
        return None
    if policy.get('scopeId') != SCOPE or source.get('calendar_source_key') != 'brian_do_not_schedule':
        raise ValueError('unsupported_native_scope')
    if (source.get('active', True) is not True or
        source.get('calendar_mode') != 'inverse_blocking' or
        (source.get('owner_instructor_key') or source.get('instructor_key')) != 'brian'):
        raise ValueError('native_inverse_policy_required')
    now = instant(now)
    owned = [s for s in calendars.get('calendar_sources', [])
             if s.get('active', True) is True and
             (s.get('owner_instructor_key') or s.get('instructor_key')) == 'brian']
    if not owned or not any(s.get('calendar_source_key') == source['calendar_source_key'] for s in owned):
        raise ValueError('configured_calendar_coverage_required')
    starts, ends, observations = [], [], []
    for s in owned:
        key = s['calendar_source_key']
        item = snapshot.get('source_evidence', {}).get(key)
        events = snapshot.get('events_by_source', {}).get(key)
        if not isinstance(item, dict) or not isinstance(events, list):
            raise ValueError('calendar_export_missing')
        if (item.get('export_status') != 'ok' or item.get('warnings') or
            any(n for reason, n in item.get('skipped', {}).items() if reason not in SAFE_SKIPS)):
            raise ValueError('calendar_export_incomplete')
        observed = instant(item['generated_at'])
        start, end = instant(item['date_range']['start']), instant(item['date_range']['end'])
        if not timedelta(0) <= now-observed < timedelta(minutes=15) or end <= start:
            raise ValueError('calendar_export_stale_or_invalid')
        if any(validate_event(s, e)[2] for e in events):
            raise ValueError('unresolved_calendar_event')
        starts.append(start); ends.append(end); observations.append(observed)
    horizon = source.get('inverse_expansion_horizon_days', 90)
    if type(horizon) is not int or not 1 <= horizon <= 90:
        raise ValueError('unsupported_native_horizon')
    start, end = max([now, *starts]), min([now+timedelta(days=horizon), *ends])
    if end <= start:
        raise ValueError('calendar_coverage_empty')
    return {'scopeId': SCOPE, 'startsAt': start.astimezone(EASTERN),
            'endsAt': end.astimezone(EASTERN), 'observedAt': min(observations),
            'validUntil': min(observations)+timedelta(minutes=15),
            'sourceIds': sorted(s['calendar_source_key'] for s in owned)}


def offer_fields(policy, candidate, report, window, now):
    """Envelope an ALREADY accepted layered-engine BLS candidate.

    Caller must retain the engine's qualification, full canonical occupancy,
    uncertainty, travel, closures, consolidation and public-policy filters.
    This function never turns a rejected candidate into an accepted one.
    """
    if not active(policy):
        return None
    if policy.get('scopeId') != SCOPE or str(candidate.get('course')) not in COURSES:
        raise ValueError('unsupported_native_course')
    if not any(candidate == c for c in report.get('accepted', [])):
        raise ValueError('accepted_engine_candidate_required')
    if (candidate.get('instructor') != 'Brian Ennis' or
        candidate.get('location') != ':: Wilmington; Shipyard Blvd - B' or
        window.get('location_name') != ':: Wilmington; Shipyard Blvd' or
        not report.get('availability_window') or
        not isinstance(candidate.get('source_ids'), list)):
        raise ValueError('native_candidate_identity_mismatch')
    now, start, end = instant(now), instant(candidate['start']), instant(candidate['end'])
    teaching_end, lease = instant(candidate['instruction_end']), instant(report['valid_until'])
    observed = instant(report['native_proof_observed_at'])
    if not observed <= now < lease <= observed+timedelta(minutes=15):
        raise ValueError('native_original_proof_expired_or_extended')
    if (start < now+timedelta(hours=24) or start > now+timedelta(days=90) or
        teaching_end-start != timedelta(minutes=120) or end-start != timedelta(minutes=150) or
        not now < lease <= now+timedelta(minutes=15)):
        raise ValueError('native_candidate_timing_or_lease_invalid')
    local = start.astimezone(EASTERN)
    if local.minute % 15 or local.second or local.microsecond:
        raise ValueError('native_start_grid_invalid')
    # Scope + physical identity is stable across publication refreshes. Historical
    # session IDs remain provenance/blockers, never an external booking authority.
    raw = '|'.join([SCOPE, str(candidate['course']), start.isoformat(),
                    candidate['instructor'], candidate['location'], '120', '150'])
    selection = 'native-full:' + sha256(raw.encode()).hexdigest()
    return {'authority': 'native-full-course.v2', 'nativeScopeId': SCOPE,
            'selectionId': selection,
            'registrationUrl': '/register/skills-session/?' + urlencode({
                'course': candidate['course'], 'selectionId': selection}),
            'validUntil': lease.isoformat(), 'proofObservedAt': observed.isoformat()}


def load_policy(root):
    path = root / 'data/config/native_publication_scope.json'
    if not path.exists():
        return {}
    policy = json.loads(path.read_text())
    if not isinstance(policy, dict):
        raise ValueError('invalid_native_publication_policy')
    return policy
