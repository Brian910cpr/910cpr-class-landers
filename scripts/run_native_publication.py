"""Bounded first-party publication. Never imports an external session fetcher.

Historical occurrence geometry is retained conservatively. Canonical demand owns
counts and new native sessions; absence/uncertainty never means zero occupancy.
Only explicit public paths may be committed by this runner. Skills adds nine
known generator outputs only when its independent default-off gate is enabled.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
import re
from pathlib import Path
import subprocess
import time
import urllib.request
from urllib.parse import urlsplit

from scripts import native_publication_scope as scope
from scripts import native_pediatric_publication as pediatric
from scripts.canonical_scheduling_demand import load_publication_demand, resolve_canonical_demand
from scripts.validate_public_refresh_output import validate_selector, session_rows

ROOT = Path(__file__).resolve().parents[1]
POLICY = 'data/config/native_publication_scope.json'
REPORT = 'debug/status/native_publication.json'
PATHS = ('docs/data/schedule_future.json', 'docs/bls.html', 'docs/BLS.html',
         'docs/bls-schedule.html', 'docs/data/block-selector-availability/bls.json',
         'docs/assets/resolved-selector-availability.js')
PAGE_PATHS = {
    'bls': ('docs/bls.html', 'docs/BLS.html', 'docs/bls-schedule.html',
            'docs/data/block-selector-availability/bls.json'),
    'heartsaver': ('docs/heartsaver.html', 'docs/HEARTSAVER.html', 'docs/heartsaver-schedule.html',
                  'docs/data/block-selector-availability/heartsaver.json'),
    'arc': ('docs/arc.html', 'docs/data/block-selector-availability/arc.json'),
    'hsi': ('docs/hsi.html', 'docs/hsi-schedule.html', 'docs/data/block-selector-availability/hsi.json'),
}
# Explicit public DTO. No client names, participant records, notes, or freeform
# upstream fields can enter the public schedule through a retained projection.
PUBLIC_FIELDS = frozenset('''session_id external_class_id course_id course_key official_course_name
raw_course_name course_match_method course_match_confidence course_needs_review
included_by_mapping_method course_name course_subtitle course_number course_code
certifying_body delivery_mode start_at end_at end_inference_reason
inferred_scheduler_consumption_minutes timezone location_name location_display
lead_instructor_name price max_students registered_count enrolled_count available_seats
is_full registration_url session_status registration_status public_direct_booking
registration_status_source registration_status_reason mapped_family mapped_subtype
mapped_certifying_body mapped_delivery_mode mapped_logo_key mapped_price mapped_clean_title
mapped_short_description mapped_long_description mapped_who_class_for mapped_prerequisites
mapped_what_to_expect mapped_certification_card mapped_renewal_info
mapped_official_description_source mapped_description_status mapping_status mapping_notes
build_classification canonical_session_id active_registration_count count_available demand_basis
consumption_start_at consumption_end_at workspace_projection_status source_observed_at
demand_status demand_match_basis canonical_start_at registration_backend source
uncertainty_scope last_verified_native_identity'''.split())
PRIVATE_KEYS = frozenset('''email phone first_name last_name student_name customer_name
participants students registrations attendee_name contact_email contact_phone
payment_intent_id stripe_customer_id notes calendar_title description'''.split())


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def write(path, value):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def policy_enabled(policy):
    require(isinstance(policy, dict) and policy.get('schemaVersion') == 'native-publication-scope.v1'
            and type(policy.get('enabled')) is bool and policy.get('scopeId') == scope.SCOPE
            and type(policy.get('skillsEnabled', False)) is bool
            and type(policy.get('heartsaverFullEnabled', False)) is bool
            and type(policy.get('pediatricExistingSessionEnabled', False)) is bool
            and type(policy.get('blsSkillsEnabled', False)) is bool
            and type(policy.get('blsBundleEnabled', False)) is bool,
            'invalid_native_publication_policy')
    return policy['enabled']


def publication_pages(skills_enabled=False, heartsaver_enabled=False, pediatric_enabled=False):
    require(type(pediatric_enabled) is bool, "invalid_pediatric_publication_gate")
    require(type(skills_enabled) is bool, 'invalid_skills_publication_gate')
    require(type(heartsaver_enabled) is bool, 'invalid_heartsaver_publication_gate')
    return ('bls', 'heartsaver', 'arc', 'hsi') if skills_enabled else ('bls', 'heartsaver') if (heartsaver_enabled or pediatric_enabled) else ('bls',)


def publication_paths(skills_enabled=False, heartsaver_enabled=False, pediatric_enabled=False):
    return PATHS + tuple(path for page in publication_pages(skills_enabled, heartsaver_enabled, pediatric_enabled)[1:] for path in PAGE_PATHS[page])


def privacy_check(value):
    if isinstance(value, dict):
        require(not (set(k.casefold() for k in value) & PRIVATE_KEYS), 'private_field_in_public_output')
        for child in value.values():
            privacy_check(child)
    elif isinstance(value, list):
        for child in value:
            privacy_check(child)


def session_admission(row, source, observed):
    """Only current exact-identity canonical booking proof can admit an old seat."""
    booking = source.get('native_booking_admission')
    if not isinstance(booking, dict):
        return None
    try:
        count = source['active_registration_count']
        capacity, remaining = booking['capacity'], booking['remaining']
        sid = str(row['session_id'])
        valid = (source.get('registration_authority') in {'landerware-session-authority.v1', 'landerware-generated-session.v1'}
            and source.get('registration_backend') == 'landerware'
            and source.get('session_status') in {'scheduled', 'active'}
            and source.get('visibility') == 'public' and source.get('registration_status') == 'open'
            and source.get('workspace_projection_status') == 'current'
            and source.get('count_available') is True and row.get('demand_status') == 'current'
            and booking.get('schemaVersion') == 'native-session-booking.v1'
            and str(row.get('course_id')) == source.get('external_course_id') == booking.get('publicCourseId')
            and booking['publicCourseId'] in scope.COURSES
            and source.get('external_class_id') == sid
            and re.fullmatch(r'(?:[0-9]+|lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})', sid)
            and all(type(v) is int for v in [count, capacity, remaining, booking.get('profileVersion')])
            and 0 <= count < capacity and remaining == capacity-count and booking['profileVersion'] > 0
            and all(scope.instant(row[k]) == scope.instant(source[k]) for k in ['start_at', 'end_at'])
            and row.get('location_name') == source.get('location_name')
            and row.get('lead_instructor_name') == source.get('lead_instructor_name'))
        if not valid:
            return None
        return {**booking, 'proofObservedAt': observed,
                'validUntil': (scope.instant(observed)+timedelta(minutes=15)).isoformat()}
    except (KeyError, ValueError, TypeError):
        return None


def skills_session_admission(row, source, observed):
    booking = source.get('native_skills_booking_admission')
    if not isinstance(booking, dict):
        return None
    try:
        count = source['active_registration_count']
        valid = (source.get('registration_authority') in {'landerware-session-authority.v1', 'landerware-generated-session.v1'}
            and source.get('registration_backend') == 'landerware' and source.get('session_status') in {'scheduled', 'active'}
            and source.get('visibility') == 'public' and source.get('registration_status') == 'open'
            and source.get('workspace_projection_status') == 'current' and source.get('count_available') is True
            and row.get('demand_status') == 'current' and type(count) is int and 0 <= count < 2
            and booking.get('schemaVersion') == 'native-skills-session-booking.v1'
            and booking.get('profileKey') == 'native_skills_shared' and type(booking.get('profileVersion')) is int and booking['profileVersion'] > 0
            and booking.get('qualificationPolicy') == 'skills-session-policy.v1'
            and booking.get('capacity') == 2 and type(booking.get('remaining')) is int and booking['remaining'] == 2-count
            and str(row.get('course_id')) == source.get('external_course_id') == booking.get('publicCourseId') == '509474'
            and str(row.get('session_id')) == source.get('external_class_id') == booking.get('sourceSessionId')
            and re.fullmatch(r'(?:[0-9]+|lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})', booking['sourceSessionId'])
            and re.fullmatch(r'[a-f0-9]{32}', booking.get('identityWitness', ''))
            and isinstance(booking.get('skillsContexts'), list) and booking['skillsContexts']
            and len(set(booking['skillsContexts'])) == len(booking['skillsContexts'])
            and set(booking['skillsContexts']) <= {'cpr-aed','first-aid-cpr-aed','arc-blended','hsi-blended','bls-skills'}
            and all(scope.instant(row[k]) == scope.instant(source[k]) for k in ['start_at','end_at','consumption_start_at','consumption_end_at'])
            and scope.instant(row['end_at']) == scope.instant(row['start_at'])+timedelta(minutes=45)
            and scope.instant(row['consumption_start_at']) == scope.instant(row['start_at'])
            and scope.instant(row['consumption_end_at']) == scope.instant(row['start_at'])+timedelta(minutes=60)
            and row.get('location_name') == source.get('location_name') == ':: Wilmington; Shipyard Blvd'
            and row.get('lead_instructor_name') == source.get('lead_instructor_name') == 'Brian Ennis')
        if valid:
            return {**booking, 'proofObservedAt': observed, 'validUntil': (scope.instant(observed)+timedelta(minutes=15)).isoformat()}
    except (KeyError, ValueError, TypeError):
        pass
    return None


def heartsaver_session_admission(row, source, observed, proof, now):
    booking = source.get('native_heartsaver_booking_admission')
    cid = str(row.get('course_id'))
    if not isinstance(booking, dict) or cid not in scope.HEARTSAVER:
        return None
    try:
        backend = scope.heartsaver_course_policy(proof, cid, now, row['consumption_end_at'])
        if not backend:
            return None
        count, capacity, remaining = source['active_registration_count'], booking['capacity'], booking['remaining']
        sid = str(row['session_id'])
        instruction, cleanup = backend['instructionMinutes'], backend['cleanupMinutes']
        valid = (source.get('registration_authority') in {'landerware-session-authority.v1','landerware-generated-session.v1'}
            and source.get('registration_backend') == 'landerware' and source.get('session_status') in {'scheduled','active'}
            and source.get('visibility') == 'public' and source.get('registration_status') == 'open'
            and source.get('workspace_projection_status') == 'current' and source.get('count_available') is True
            and row.get('demand_status') == 'current'
            and booking.get('schemaVersion') == 'native-heartsaver-session-booking.v1'
            and source.get('external_course_id') == booking.get('publicCourseId') == cid
            and booking.get('canonicalCourseId') == backend['canonicalCourseId']
            and booking.get('coursePolicyKey') == backend['coursePolicyKey']
            and booking.get('profileKey') == 'native_heartsaver_'+cid+'_draft'
            and source.get('external_class_id') == booking.get('sourceSessionId') == sid
            and re.fullmatch(r'(?:[0-9]+|lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})', sid)
            and re.fullmatch(r'[a-f0-9]{32}', booking.get('identityWitness',''))
            and all(type(v) is int for v in [count,capacity,remaining,booking.get('profileVersion'),booking.get('instructionMinutes'),booking.get('cleanupMinutes')])
            and 0 <= count < capacity <= backend['maxStudents'] and remaining == capacity-count and booking['profileVersion'] > 0
            and booking['instructionMinutes'] == instruction and booking['cleanupMinutes'] == cleanup
            and all(scope.instant(row[k]) == scope.instant(source[k]) for k in NATIVE_INTERVAL_FIELDS)
            and scope.instant(row['end_at']) == scope.instant(row['start_at'])+timedelta(minutes=instruction)
            and scope.instant(row['consumption_start_at']) == scope.instant(row['start_at'])
            and scope.instant(row['consumption_end_at']) == scope.instant(row['start_at'])+timedelta(minutes=instruction+cleanup)
            and row.get('location_name') == source.get('location_name') == ':: Wilmington; Shipyard Blvd'
            and row.get('lead_instructor_name') == source.get('lead_instructor_name') == 'Brian Ennis')
        if valid:
            return {**booking, 'proofObservedAt': min(scope.instant(observed),scope.instant(proof['observedAt'])).isoformat(),
                    'validUntil': min(scope.instant(observed)+timedelta(minutes=15),scope.instant(proof['validUntil'])).isoformat()}
    except (KeyError, ValueError, TypeError):
        pass
    return None


def skills_registration_url(row):
    from urllib.parse import urlencode
    starts = scope.instant(row['start_at']).astimezone(scope.EASTERN)
    return '/register/skills-session/?'+urlencode({'course':'509474','date':starts.date().isoformat(),
        'startTime':starts.strftime('%H:%M'),'instructor':row['lead_instructor_name'],'location':row['location_name']})


NATIVE_INTERVAL_FIELDS = ('start_at', 'end_at', 'consumption_start_at', 'consumption_end_at')
NATIVE_IDENTITY_FIELDS = ('canonical_session_id', 'external_class_id', *NATIVE_INTERVAL_FIELDS)
NATIVE_IDENTITY_SCHEMA = 'retained-native-identity.v1'


def same_native_intervals(left, right):
    try:
        return (scope.instant(left['end_at']) > scope.instant(left['start_at'])
            and all((left.get(k) is None and right.get(k) is None) or
                    scope.instant(left[k]) == scope.instant(right[k]) for k in NATIVE_INTERVAL_FIELDS))
    except (KeyError, ValueError, TypeError):
        return False


def verified_native_projection_identity(row):
    """Retain exact prior identity only, never occupancy or booking authority."""
    sid = row.get('session_id')
    if not (isinstance(sid, str) and re.fullmatch(r'lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', sid)
            and row.get('external_class_id') == sid and row.get('canonical_session_id')
            and row.get('source') == 'landerware_event' and row.get('registration_backend') == 'landerware'
            and row.get('demand_status') == 'current' and row.get('count_available') is True
            and row.get('demand_match_basis') == 'external_class_id'
            and row.get('workspace_projection_status') == 'current'
            and same_native_intervals(row, row)):
        return None
    return {'schemaVersion': NATIVE_IDENTITY_SCHEMA,
            **{k: deepcopy(row.get(k)) for k in NATIVE_IDENTITY_FIELDS}}


def preserve_native_projection_identity(row):
    identity = verified_native_projection_identity(row)
    if identity:
        row['last_verified_native_identity'] = identity
    elif isinstance(row.get('last_verified_native_identity'), dict):
        # This is a bounded DTO, not an arbitrary upstream object. Keep the
        # original interval binding through unknown reads; never rewrite it to
        # match changed retained geometry. A later release must match both.
        prior = row['last_verified_native_identity']
        keys = ('schemaVersion', *NATIVE_IDENTITY_FIELDS)
        if (all(k in prior for k in keys)
                and all(isinstance(prior[k], str) and prior[k] for k in
                        ('schemaVersion', 'canonical_session_id', 'external_class_id', 'start_at', 'end_at'))
                and all(prior[k] is None or isinstance(prior[k], str) for k in
                        ('consumption_start_at', 'consumption_end_at'))):
            row['last_verified_native_identity'] = {k: prior[k] for k in keys}
        else:
            row.pop('last_verified_native_identity', None)
    else:
        row.pop('last_verified_native_identity', None)


def retire_released_occurrences(rows, demand):
    releases = {str(row['external_class_id']): row for row in demand.get('released_native_sessions', [])}
    kept, retired = [], []
    for row in rows:
        release = releases.get(str(row.get('session_id')))
        if release is None:
            kept.append(row); continue
        prior = row.get('last_verified_native_identity')
        identity = prior if isinstance(prior, dict) else row
        if not identity.get('canonical_session_id'):
            # Older projections may already have lost their canonical ID.
            # Do not invent it from the external ID, and do not prevent
            # publication of unrelated safe offers. Keep this blocker.
            kept.append(row); continue
        if isinstance(prior, dict):
            require(prior.get('schemaVersion') == NATIVE_IDENTITY_SCHEMA
                    and (not row.get('canonical_session_id')
                         or row['canonical_session_id'] == prior['canonical_session_id']),
                    'retained_native_release_identity_changed')
        require(release.get('authority') == 'native-generated-release.v1'
            and release.get('release_reason') == 'expired_unpaid_hold'
            and str(row.get('session_id', '')).startswith('lw-')
            and row.get('external_class_id') == identity.get('external_class_id') == release.get('external_class_id')
            and identity.get('canonical_session_id') == release.get('canonical_session_id')
            and same_native_intervals(row, identity) and same_native_intervals(row, release)
            and scope.instant(release['released_at']) <= scope.instant(demand['generated_at']),
            'retained_native_release_identity_changed')
        retired.append(str(row['session_id']))
    return kept, retired


def retained_projection(retained, demand, *, skills_enabled=False, heartsaver_enabled=False, bls_skills_enabled=False, bls_bundle_enabled=False, now=None):
    now = now or datetime.now(timezone.utc)
    if heartsaver_enabled:
        scope.validate_heartsaver_proof(demand.get('native_heartsaver_policy_proof'), now)
    rows = deepcopy(session_rows(retained))
    require(isinstance(retained, dict) and isinstance(retained.get('sessions'), list), 'retained_occurrences_required')
    ids = [str(row.get('session_id') or '') for row in rows]
    require(all(ids) and len(set(ids)) == len(ids), 'retained_occurrence_identity_invalid')
    # Preserve every retained occurrence, including unknown, private/closed and
    # moved geometry as conservative occupancy. The engine also reads the entire
    # canonical demand separately, so private and offsite commitments still block.
    rows, retired = retire_released_occurrences(rows, demand)
    for row in rows:
        preserve_native_projection_identity(row)
    projected, _ = resolve_canonical_demand(rows, demand['sessions'])
    for row in projected:
        preserve_native_projection_identity(row)
    require(set(ids)-set(retired) <= {str(row.get('session_id') or '') for row in projected}, 'retained_occurrence_lost')
    projected = [{key: deepcopy(value) for key, value in row.items() if key in PUBLIC_FIELDS}
                 for row in projected]
    sources = {str(source.get('canonical_session_id')): source for source in demand['sessions']}
    for row in projected:
        # A prior public projection is never booking authority. Re-admit only
        # using this newly fetched exact-identity canonical capacity/profile DTO.
        row.pop('registration_url', None)
        row['public_direct_booking'] = False
        source = sources.get(str(row.get('canonical_session_id')), {})
        admission = session_admission(row, source, demand['generated_at'])
        skills = skills_session_admission(row, source, demand['generated_at']) if (skills_enabled or bls_skills_enabled or bls_bundle_enabled) else None
        if skills:
            policy = dict(schemaVersion='native-publication-scope.v1', enabled=True,
                          blsSkillsEnabled=bls_skills_enabled, blsBundleEnabled=bls_bundle_enabled,
                          _blsSkillsProof=demand.get('native_bls_skills_policy_proof'))
            ready = scope.bls_course_ready(policy, '509474', now, row['consumption_end_at']) or scope.bls_course_ready(policy, '210549', now, row['consumption_end_at'])
            allowed = set(c for group in scope.SKILLS_CONTEXTS.values() for c in group) if skills_enabled else set()
            if ready and skills['profileVersion'] == ready['profileVersion']:
                allowed.add('bls-skills')
            skills['skillsContexts'] = sorted(set(skills['skillsContexts']) & allowed)
            if not skills['skillsContexts']:
                skills = None
        heartsaver = heartsaver_session_admission(row, source, demand['generated_at'], demand.get('native_heartsaver_policy_proof'), now) if heartsaver_enabled else None
        if heartsaver:
            row.update(native_heartsaver_booking_admission=heartsaver, public_direct_booking=True,
                       registration_url='/register/?session='+str(row['session_id']))
        if skills:
            row.update(native_skills_booking_admission=skills, public_direct_booking=True,
                       registration_url=skills_registration_url(row))
        if admission:
            row.update(native_booking_admission=admission, public_direct_booking=True,
                       registration_url='/register/?session='+str(row['session_id']))
    privacy_check(projected)
    return {'build': {'source_mode': 'native_canonical_with_retained_occurrences',
                      'generated_at': demand['generated_at'],
                      'counts': {'retained_sessions': len(rows), 'released_native_sessions': len(retired), 'sessions_output': len(projected)}},
            'sessions': projected}


def prepare():
    require(policy_enabled(read(POLICY)), 'native_publication_disabled')
    demand = load_publication_demand(ROOT)
    output = retained_projection(read('docs/data/schedule_future.json'), demand, skills_enabled=read(POLICY).get('skillsEnabled', False), heartsaver_enabled=read(POLICY).get('heartsaverFullEnabled', False), bls_skills_enabled=read(POLICY).get('blsSkillsEnabled', False), bls_bundle_enabled=read(POLICY).get('blsBundleEnabled', False))
    write('data/sessions_current.json', output)
    write('docs/data/schedule_future.json', output)
    return output


def calendar_bounds(now):
    from scripts import build_live_availability_snapshot as live
    calendars = read('data/config/calendar_sources.json')
    _, snapshot, missing = live.find_local_snapshot()
    require(not missing and isinstance(snapshot, dict), 'current_calendar_snapshot_required')
    source = next(s for s in calendars['calendar_sources'] if s.get('calendar_source_key') == 'brian_do_not_schedule')
    return scope.inverse_bounds(read(POLICY), source, calendars, snapshot, now, live.event_time_validation)


def check_budget(expires, now, seconds=300):
    require(scope.instant(expires) - scope.instant(now) >= timedelta(seconds=seconds),
            'original_proof_has_insufficient_publication_budget')


def validate(*, now=None, margin=300):
    now = now or datetime.now(timezone.utc)
    policy = read(POLICY)
    require(policy_enabled(policy), 'native_publication_disabled')
    demand = load_publication_demand(ROOT)
    policy['_blsSkillsProof'] = demand.get('native_bls_skills_policy_proof')
    bounds = calendar_bounds(now)
    # A fresh publication timestamp never renews source observation timestamps.
    expiry = min(bounds['validUntil'], scope.instant(demand['generated_at']) + timedelta(minutes=15))
    heartsaver_proof = None
    if policy.get('heartsaverFullEnabled', False):
        heartsaver_proof = scope.validate_heartsaver_proof(demand.get('native_heartsaver_policy_proof'), now)
        expiry = min(expiry, scope.instant(heartsaver_proof['validUntil']))
    check_budget(expiry, now, margin)
    schedule = read('docs/data/schedule_future.json')
    privacy_check(schedule)
    expected_rows = {str(row['session_id']): row for row in retained_projection(schedule, demand, skills_enabled=policy.get('skillsEnabled', False), heartsaver_enabled=policy.get('heartsaverFullEnabled', False), bls_skills_enabled=policy.get('blsSkillsEnabled', False), bls_bundle_enabled=policy.get('blsBundleEnabled', False), now=now)['sessions']}
    for row in session_rows(schedule):
        expected = expected_rows[str(row['session_id'])]
        require(row.get('native_booking_admission') == expected.get('native_booking_admission')
                and row.get('native_skills_booking_admission') == expected.get('native_skills_booking_admission')
                and row.get('native_heartsaver_booking_admission') == expected.get('native_heartsaver_booking_admission')
                and row.get('public_direct_booking') == expected.get('public_direct_booking'),
                'native_admission_source_changed')
        if row.get('public_direct_booking') is True:
            admission = row.get('native_booking_admission') or row.get('native_heartsaver_booking_admission')
            if row.get('native_skills_booking_admission'):
                require(row.get('registration_url') == skills_registration_url(row), 'unadmitted_skills_registration_cta')
                check_budget(row['native_skills_booking_admission']['validUntil'], now, margin)
                continue
            require(isinstance(admission, dict) and row.get('registration_url') == '/register/?session='+str(row.get('session_id')), 'unadmitted_session_registration_cta')
            check_budget(admission['validUntil'], now, margin)
        else:
            require(not row.get('registration_url'), 'unadmitted_session_registration_cta')
    ids = {str(row['session_id']) for row in session_rows(schedule)}
    counts, originals, full_count, skills_count = {}, [], 0, 0
    for page_key in publication_pages(policy.get('skillsEnabled', False), policy.get('heartsaverFullEnabled', False), policy.get('pediatricExistingSessionEnabled',False)):
        counts[page_key] = validate_selector(page_key, ids, now=now)
        selector = read('docs/data/block-selector-availability/'+page_key+'.json')
        # Public authority.description is fixed implementation text, not user data.
        privacy_check({k: v for k, v in selector.items() if k != 'authority'})
        for day in selector['dates']:
            for slot in day['startTimes']:
                for offer in slot['courses']:
                    if page_key == 'bls' and str(offer.get('courseId')) in scope.BLS_PACKAGES:
                        validate_bls_offer(offer, schedule, policy, now, margin)
                        skills_count += 1
                        expiry = min(expiry, scope.instant(offer['validUntil']))
                        if offer.get('offerType') == 'dynamic_appointment':
                            originals.append(scope.instant(offer['calendarProofObservedAt']))
                        continue
                    if str(offer.get('courseId')) == pediatric.COURSE:
                        require(policy.get('pediatricExistingSessionEnabled') is True, 'pediatric_publication_disabled')
                        expected = pediatric.project({'pageKey':'heartsaver','offers':[]}, demand, policy, now)
                        match = next((o for o in expected['offers'] if o['session_id'] == offer.get('session_id')), None)
                        from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload
                        compact = public_selector_availability_payload(expected)
                        expected_offer = next((o for d in compact['dates'] for slot in d['startTimes'] for o in slot['courses'] if o['session_id'] == offer.get('session_id')), None)
                        require(match is not None and offer == expected_offer, 'pediatric_publication_proof_changed')
                        check_budget(offer['validUntil'], now, margin)
                        expiry = min(expiry, scope.instant(offer['validUntil']))
                        full_count += 1
                        continue
                    heartsaver = page_key == 'heartsaver' and str(offer.get('courseId')) in scope.HEARTSAVER
                    if heartsaver:
                        require(policy.get('heartsaverFullEnabled') is True, 'native_heartsaver_publication_disabled')
                        backend = scope.heartsaver_course_policy(heartsaver_proof, offer['courseId'], now, offer.get('occupiedUntil'))
                        require(backend is not None, 'native_heartsaver_course_not_ready')
                        if offer.get('offerType') == 'seated_class':
                            validate_heartsaver_seated_offer(offer, schedule, now, margin)
                            full_count += 1
                            expiry = min(expiry, scope.instant(offer['validUntil']))
                            continue
                        require(scope.instant(offer['policyProofObservedAt']) == scope.instant(heartsaver_proof['observedAt'])
                                and scope.instant(offer['validUntil']) <= scope.instant(heartsaver_proof['validUntil']), 'native_heartsaver_policy_proof_changed')
                    if page_key != 'bls' and offer.get('offerType') == 'seated_class':
                        validate_skills_seated_offer(offer, schedule, page_key, now, margin)
                        skills_count += 1
                        expiry = min(expiry, scope.instant(offer['validUntil']))
                        continue
                    if page_key == 'bls' and offer.get('offerType') == 'seated_class':
                        validate_seated_offer(offer, schedule, now, margin)
                        continue
                    require(offer.get('offerType') == 'dynamic_appointment', 'unadmitted_public_offer')
                    if page_key == 'bls' or heartsaver:
                        require(offer.get('authority') == 'native-full-course.v2'
                                and str(offer.get('courseId')) in (set(scope.HEARTSAVER) if heartsaver else scope.COURSES), 'unadmitted_public_offer')
                        full_count += 1
                    else:
                        require(offer.get('authority') == scope.SKILLS_AUTHORITY
                                and str(offer.get('courseId')) == '509474', 'unadmitted_public_offer')
                        skills_count += 1
                    url = urlsplit(offer.get('registrationUrl') or offer.get('appointmentUrl') or '')
                    require(not url.netloc and not url.scheme and url.path == '/register/skills-session/', 'external_dynamic_destination')
                    check_budget(offer['validUntil'], now, margin)
                    originals.append(scope.instant(offer['calendarProofObservedAt'] if heartsaver else offer['proofObservedAt']))
                    expiry = min(expiry, scope.instant(offer['validUntil']))
    require(not originals or min(originals) == bounds['observedAt'], 'calendar_original_proof_mismatch')
    return {'counts': counts['bls'], 'pageCounts': counts,
            'sourceProofObservedAt': min(bounds['observedAt'], scope.instant(demand['generated_at'])).isoformat(),
            'validUntil': expiry.isoformat(), 'nativeFullOffers': full_count, 'nativeSkillsOffers': skills_count}


def annotate_seated_offers(payload, schedule):
    rows = {str(row['session_id']): row for row in session_rows(schedule)}
    for offer in payload.get('offers', []):
        if offer.get('offerType') != 'seated_class':
            continue
        sid = str((offer.get('sourceAvailabilityBlock') or {}).get('sessionId') or '')
        row = rows.get(sid, {})
        if str(offer.get('courseId')) in scope.HEARTSAVER:
            admission = row.get('native_heartsaver_booking_admission') or {}
            require(row.get('public_direct_booking') is True and admission, 'unadmitted_heartsaver_seated_offer')
            offer.pop('appointmentDayId', None); offer.pop('matchedContainerId', None)
            instruction, cleanup = admission['instructionMinutes'], admission['cleanupMinutes']
            offer.update(authority='native-heartsaver-session-booking.v1', nativeScopeId=scope.SCOPE,
                coursePolicyKey=admission['coursePolicyKey'], session_id=sid, sourceSessionIds=[sid],
                capacity=admission['capacity'], remainingSeats=admission['remaining'], profileVersion=admission['profileVersion'],
                identityWitness=admission['identityWitness'], resource=':: Wilmington; Shipyard Blvd - B',
                durationMinutes=instruction, setupBufferMinutes=0, cleanupBufferMinutes=cleanup,
                schedulerConsumptionMinutes=instruction+cleanup, occupiedUntil=row['consumption_end_at'],
                proofObservedAt=admission['proofObservedAt'], validUntil=admission['validUntil'])
            continue
        if str(offer.get('courseId')) == '509474':
            admission = row.get('native_skills_booking_admission') or {}
            contexts = sorted(set(admission.get('skillsContexts', [])) & ({'bls-skills'} if payload.get('pageKey') == 'bls' else set(scope.SKILLS_CONTEXTS.get(payload.get('pageKey'), {}))))
            require(row.get('public_direct_booking') is True and contexts, 'unadmitted_skills_seated_offer')
            offer.pop('appointmentDayId', None); offer.pop('matchedContainerId', None)
            offer.update(authority='native-skills-seated.v1', nativeScopeId=scope.SCOPE,
                nativeOfferId='native-skills-seated:'+sid, session_id=sid, sourceSessionIds=[sid],
                capacity=2, remainingSeats=admission['remaining'], profileVersion=admission['profileVersion'],
                identityWitness=admission['identityWitness'], qualificationPolicy='skills-session-policy.v1', skillsContexts=contexts,
                durationMinutes=45, setupBufferMinutes=0, cleanupBufferMinutes=15, schedulerConsumptionMinutes=60,
                occupiedUntil=row['consumption_end_at'], proofObservedAt=admission['proofObservedAt'], validUntil=admission['validUntil'])
            continue
        admission = row.get('native_booking_admission')
        require(row.get('public_direct_booking') is True and isinstance(admission, dict), 'unadmitted_seated_offer')
        offer.update(authority='native-session-booking.v1', session_id=sid,
            capacity=admission['capacity'], remainingSeats=admission['remaining'],
            proofObservedAt=admission['proofObservedAt'], validUntil=admission['validUntil'])
    # Seated-only pages still carry a bounded native lease through finalization.
    leases = [offer['validUntil'] for offer in payload.get('offers', []) if offer.get('authority') in {'native-skills-seated.v1','native-heartsaver-session-booking.v1'}]
    if leases:
        payload['validUntil'] = max([payload.get('validUntil') or min(leases), *leases], key=scope.instant)
    return payload


def project_bls_offers(payload, schedule, policy, now):
    """Project choices, never sessions: both packages retain one physical pool."""
    if payload.get('pageKey') != 'bls':
        return payload
    projected = []
    emitted = set()
    for offer in payload.get('offers', []):
        if str(offer.get('courseId')) not in scope.BLS_PACKAGES:
            projected.append(offer)
            continue
        if offer.get('authority') not in {scope.SKILLS_AUTHORITY, 'native-skills-seated.v1'}:
            continue
        for cid in scope.BLS_PACKAGES:
            proof = scope.bls_course_ready(policy, cid, now, offer.get('occupiedUntil'))
            if not proof or offer.get('skillsContexts') != ['bls-skills']:
                continue
            if offer.get('profileVersion') != proof['profileVersion']:
                continue
            identity = (offer['nativeOfferId'], cid)
            if identity in emitted:
                continue
            emitted.add(identity)
            choice = dict(offer)
            calendar_observed = offer.get('calendarProofObservedAt', offer['proofObservedAt'])
            choice.update(scope.bls_offer_identity(choice, cid),
                courseName='Skills Session Only' if cid == '509474' else 'HeartCode BLS including online access',
                profileVersion=proof['profileVersion'], calendarProofObservedAt=calendar_observed,
                policyProofObservedAt=proof['observedAt'],
                proofObservedAt=min(scope.instant(calendar_observed), scope.instant(proof['observedAt'])).isoformat(),
                validUntil=min(scope.instant(offer['validUntil']), scope.instant(proof['validUntil'])).isoformat())
            choice['appointmentUrl'] = choice['registrationUrl']
            projected.append(choice)
    if any(str(o.get('courseId')) in scope.BLS_PACKAGES for o in payload.get('offers', [])):
        from scripts.apply_anchor_policy import _rebuild_dates
        _rebuild_dates(payload, projected)
    else:
        payload['offers'] = projected
    config = payload.get('pageConfig', {})
    if '_blsPublicOptions' in config:
        options = config.pop('_blsPublicOptions')
        config['course_options'] = [o for o in config['course_options'] if str(o.get('course_id')) not in scope.BLS_PACKAGES] + options
        config['allowed_course_ids'] = [str(o['course_id']) for o in config['course_options']]
    return payload


def validate_bls_offer(offer, schedule, policy, now, margin):
    cid = str(offer.get('courseId'))
    proof = scope.bls_course_ready(policy, cid, now, offer.get('occupiedUntil'))
    require(proof is not None, 'unadmitted_public_offer: native_bls_skills_course_not_ready')
    for key, value in scope.bls_offer_identity(offer, cid).items():
        require(offer.get(key) == value, 'native_bls_skills_identity_changed')
    require(offer.get('appointmentUrl') == offer['registrationUrl']
            and offer.get('profileVersion') == proof['profileVersion']
            and offer.get('qualificationPolicy') == scope.SKILLS_QUALIFICATION_POLICY
            and scope.instant(offer['policyProofObservedAt']) == scope.instant(proof['observedAt']),
            'native_bls_skills_policy_changed')
    calendar = scope.instant(offer['calendarProofObservedAt'])
    observed, lease = scope.instant(offer['proofObservedAt']), scope.instant(offer['validUntil'])
    require(observed == min(calendar, scope.instant(proof['observedAt']))
            and observed <= scope.instant(now) < lease <= min(calendar+timedelta(minutes=15), scope.instant(proof['validUntil'])),
            'native_bls_skills_original_proof_changed')
    if offer.get('offerType') == 'seated_class':
        sid = str(offer.get('session_id') or '')
        rows = [r for r in session_rows(schedule) if str(r.get('session_id')) == sid]
        require(len(rows) == 1, 'unadmitted_bls_skills_seated_offer')
        row = rows[0]; booking = row.get('native_skills_booking_admission') or {}
        local = scope.instant(row['start_at']).astimezone(scope.EASTERN)
        require(row.get('public_direct_booking') is True and 'bls-skills' in booking.get('skillsContexts', [])
                and offer.get('authority') == 'native-skills-seated.v1'
                and offer.get('nativeOfferId') == 'native-skills-seated:'+sid
                and offer.get('sourceSessionIds') == [sid] and offer.get('availabilityBlockId') == 'seated:'+sid
                and offer.get('date') == local.date().isoformat() and offer.get('startTime') == local.strftime('%H:%M')
                and offer.get('location') == row.get('location_name') and offer.get('instructor') == row.get('lead_instructor_name')
                and offer.get('capacity') == 2 and offer.get('remainingSeats') == booking.get('remaining')
                and offer.get('profileVersion') == booking.get('profileVersion')
                and offer.get('identityWitness') == booking.get('identityWitness')
                and calendar == scope.instant(booking['proofObservedAt'])
                and lease == min(scope.instant(booking['validUntil']), scope.instant(proof['validUntil']))
                and scope.instant(offer['occupiedUntil']) == scope.instant(row['consumption_end_at']),
                'native_bls_skills_seated_proof_changed')
    else:
        require(offer.get('offerType') == 'dynamic_appointment' and offer.get('authority') == scope.SKILLS_AUTHORITY,
                'unadmitted_bls_skills_offer')
    check_budget(lease, now, margin)


def validate_skills_seated_offer(offer, schedule, page_key, now, margin):
    sid = str(offer.get('session_id') or '')
    rows = [r for r in session_rows(schedule) if str(r.get('session_id')) == sid]
    require(len(rows) == 1, 'unadmitted_skills_seated_offer')
    row = rows[0]; booking = row.get('native_skills_booking_admission') or {}
    require(row.get('public_direct_booking') is True and
        offer.get('registrationUrl') == row.get('registration_url') == skills_registration_url(row), 'unadmitted_skills_seated_offer')
    for public, canonical in [('profileVersion','profileVersion'),('identityWitness','identityWitness'),
        ('remainingSeats','remaining'),('proofObservedAt','proofObservedAt'),('validUntil','validUntil')]:
        require(offer.get(public) == booking.get(canonical), 'skills_seated_proof_changed')
    require(offer.get('skillsContexts') == sorted(set(booking.get('skillsContexts', [])) & set(scope.SKILLS_CONTEXTS[page_key])), 'skills_context_changed')
    require(scope.instant(offer['occupiedUntil']) == scope.instant(row['consumption_end_at']), 'skills_identity_changed')
    check_budget(offer['validUntil'], now, margin)


def validate_seated_offer(offer, schedule, now, margin):
    sid = str(offer.get('session_id') or '')
    rows = [row for row in session_rows(schedule) if str(row.get('session_id')) == sid]
    require(len(rows) == 1, 'unadmitted_public_offer')
    row = rows[0]; admission = row.get('native_booking_admission') or {}
    local_start = scope.instant(row['start_at']).astimezone(scope.EASTERN)
    require(offer.get('authority') == 'native-session-booking.v1' and row.get('public_direct_booking') is True
        and str(offer.get('courseId')) in scope.COURSES and str(offer.get('courseId')) == str(row.get('course_id'))
        and offer.get('date') == local_start.date().isoformat() and offer.get('startTime') == local_start.strftime('%H:%M')
        and offer.get('location') == row.get('location_name') and offer.get('instructor') == row.get('lead_instructor_name')
        and offer.get('availabilityBlockId') == 'seated:'+sid
        and offer.get('registrationUrl') == offer.get('appointmentUrl') == row.get('registration_url') == '/register/?session='+sid
        and offer.get('capacity') == admission.get('capacity') and offer.get('remainingSeats') == admission.get('remaining')
        and type(offer.get('remainingSeats')) is int and offer['remainingSeats'] > 0
        and offer.get('proofObservedAt') == admission.get('proofObservedAt')
        and offer.get('validUntil') == admission.get('validUntil'), 'unadmitted_public_offer')
    observed, lease = scope.instant(offer['proofObservedAt']), scope.instant(offer['validUntil'])
    require(observed <= now < lease <= observed+timedelta(minutes=15), 'native_seated_original_proof_invalid')
    check_budget(lease, now, margin)


def validate_heartsaver_seated_offer(offer, schedule, now, margin):
    sid = str(offer.get('session_id') or '')
    rows = [r for r in session_rows(schedule) if str(r.get('session_id')) == sid]
    require(len(rows) == 1, 'unadmitted_heartsaver_seated_offer')
    row = rows[0]; booking = row.get('native_heartsaver_booking_admission') or {}
    expected = {'pageKey':'heartsaver', 'offers':[dict(offer, sourceAvailabilityBlock={'sessionId': sid})]}
    annotate_seated_offers(expected, schedule)
    for key in ['authority','nativeScopeId','coursePolicyKey','session_id','sourceSessionIds','capacity','remainingSeats',
                'profileVersion','identityWitness','resource','durationMinutes','setupBufferMinutes','cleanupBufferMinutes',
                'schedulerConsumptionMinutes','occupiedUntil','proofObservedAt','validUntil']:
        require(offer.get(key) == expected['offers'][0].get(key), 'heartsaver_seated_proof_changed')
    local = scope.instant(row['start_at']).astimezone(scope.EASTERN)
    require(str(offer.get('courseId')) == str(row.get('course_id')) == booking.get('publicCourseId')
        and offer.get('date') == local.date().isoformat() and offer.get('startTime') == local.strftime('%H:%M')
        and offer.get('location') == row.get('location_name') and offer.get('instructor') == row.get('lead_instructor_name')
        and offer.get('availabilityBlockId') == 'seated:'+sid
        and offer.get('registrationUrl') == offer.get('appointmentUrl') == row.get('registration_url') == '/register/?session='+sid,
        'unadmitted_heartsaver_seated_offer')
    check_budget(offer['validUntil'], now, margin)


def native_page_config(config, page_key='bls', *, skills_enabled=True, heartsaver_enabled=False, bls_skills_enabled=False, bls_bundle_enabled=False, pediatric_enabled=False):
    config = deepcopy(config)
    require(config.get('page_key') == page_key and page_key in PAGE_PATHS, 'unexpected_publication_page')
    if page_key == 'heartsaver' and pediatric_enabled:
        pediatric_option = next((deepcopy(o) for o in config.get('course_options',[]) if str(o.get('course_id')) == '351632'), None)
        require(pediatric_option is not None, 'pediatric_course_option_required')
        if heartsaver_enabled or skills_enabled:
            config = native_page_config(config, page_key, skills_enabled=skills_enabled, heartsaver_enabled=heartsaver_enabled)
        else:
            config.update(allowed_course_ids=[], course_options=[], include_seated_classes=False,
                compare_mode={'enabled':False}, show_all_enabled=False)
        pediatric_option.pop('price',None)
        config['course_options'].append(pediatric_option)
        config['default_course_id'] = config.get('default_course_id') if heartsaver_enabled or skills_enabled else '351632'
        config['native_pediatric_publication'] = True
        return config
    if page_key == 'heartsaver' and heartsaver_enabled:
        allowed = set(scope.HEARTSAVER) | ({'509474'} if skills_enabled else set())
        config.update(allowed_course_ids=sorted(allowed), include_seated_classes=True, native_heartsaver_publication=True,
                      default_course_id='209809', compare_mode={'enabled':False}, show_all_enabled=False)
        config['course_options'] = [row for row in config.get('course_options', []) if str(row.get('course_id')) in allowed]
        require({str(row['course_id']) for row in config['course_options']} == allowed, 'native_heartsaver_course_options_required')
        if skills_enabled:
            native_page_config(config, page_key, skills_enabled=True, heartsaver_enabled=False)
        config['subtitle'] = 'Instructor-led CPR, AED and First Aid training'
        config['meta_description'] = 'Choose instructor-led Heartsaver CPR AED or First Aid CPR AED in Wilmington, NC.'
        config['intro'] = 'Choose First Aid CPR AED if you need First Aid, or CPR AED for CPR and AED only.'
        if skills_enabled:
            config['intro'] += ' Already completed online coursework? Choose Skills Session Only and the matching context.'
        config['documentation_note'] = {'title':'Choose your Heartsaver course','body':config['intro'],'bullets':[]}
        config['delivery_help'] = [item for item in config.get('delivery_help',[]) if item.get('label') == 'IN-PERSON']
        return config
    if page_key != 'bls':
        require(page_key in scope.SKILLS_CONTEXTS, 'unsupported_native_skills_page')
        config.update(allowed_course_ids=['509474'], include_seated_classes=True,
                      default_course_id='509474', compare_mode={'enabled': False}, show_all_enabled=False)
        config['course_options'] = [row for row in config.get('course_options', []) if str(row.get('course_id')) == '509474']
        require(len(config['course_options']) == 1, 'native_skills_course_option_required')
        contexts = {c.get('key'): c.get('template_course_id') for c in config['course_options'][0].get('skills_contexts', [])}
        require(contexts == scope.SKILLS_CONTEXTS[page_key], 'native_skills_context_policy_mismatch')
        config['meta_description'] = 'Choose a verified in-person skills session in Wilmington, NC after completing the required online coursework.'
        config['intro'] = 'Already completed your online coursework? Choose Skills Session Only and the matching course context. Online coursework is not included.'
        config['documentation_note'] = {'title': 'Skills Session Only', 'body': config['intro'], 'bullets': []}
        return config
    config.update(allowed_course_ids=sorted(scope.COURSES), include_seated_classes=True)
    config['course_options'] = [row for row in config.get('course_options', [])
                                if str(row.get('course_id')) in scope.COURSES]
    # The narrow preview must not advertise an unadmitted bundle as available.
    config['meta_description'] = 'Choose instructor-led AHA BLS Provider or BLS Renewal in Wilmington, NC. View current verified availability and register online.'
    config['intro'] = 'New or expired card: choose BLS Provider. Current BLS card: choose Renewal.'
    config['documentation_note'] = {'title': 'Choose your instructor-led BLS course',
        'body': 'Current verified availability is shown for BLS Provider and BLS Renewal.',
        'bullets': ['BLS Provider is for new students or anyone returning after expiration.',
                    'BLS Renewal is for currently certified providers who qualify for the renewal format.']}
    for group in config.get('compare_mode', {}).get('groups', {}).values():
        group['course_ids'] = [c for c in group.get('course_ids', []) if str(c) in scope.COURSES]
    if bls_skills_enabled or bls_bundle_enabled:
        config['native_bls_skills_publication'] = True
        options = deepcopy(config.get('native_checkout_course_options', []))
        physical = next((o for o in options if str(o.get('course_id')) == '509474'), None)
        require(physical is not None, 'native_bls_skills_course_option_required')
        physical.update(scheduling_template_course_id='209806', skills_contexts=[
            {'key': 'bls-skills', 'label': 'BLS', 'template_course_id': '209806'}])
        config['allowed_course_ids'].append('509474')
        config['course_options'].append(physical)
        config['_blsPublicOptions'] = [o for o in options if
            (str(o.get('course_id')) == '509474' and bls_skills_enabled) or
            (str(o.get('course_id')) == '210549' and bls_bundle_enabled)]
        if bls_skills_enabled:
            config['intro'] += ' Choose Skills Session Only after completing online coursework.'
        if bls_bundle_enabled:
            config['intro'] += ' HeartCode BLS including online access includes online coursework and the in-person skills session.'
    return config


def check_page_outputs(config, page_key):
    """Check the complete configured write set before invoking any generator."""
    require(config.get('page_key') == page_key and config.get('render_html', True) is True,
            'unexpected_generator_output')
    paths = [config.get('output_path'), *config.get('alias_output_paths', []),
             'docs/data/block-selector-availability/'+page_key+'.json']
    if config.get('legacy_schedule_path'):
        paths.append(config['legacy_schedule_path'])
    require(len(paths) == len(set(paths)) and set(paths) == set(PAGE_PATHS[page_key]), 'unexpected_generator_output')
    defaults = ('data/audit/bls_block_schedule_pilot.json', 'data/audit/bls_block_schedule_pilot_report.md') if page_key == 'bls' else (
        'data/audit/'+page_key+'_block_schedule.json', 'data/audit/'+page_key+'_block_schedule_report.md')
    reports = (config.get('report_json_path', defaults[0]), config.get('report_md_path', defaults[1]))
    require(reports == defaults, 'unexpected_generator_report_path')
    return reports


def build(preview=False):
    original = (ROOT / POLICY).read_bytes()
    policy = read(POLICY)
    enabled = policy_enabled(policy)
    require(enabled or preview, 'native_publication_disabled')
    head = git('rev-parse', 'HEAD')
    try:
        if preview:
            write(POLICY, dict(policy, enabled=True))
        schedule = prepare()
        from scripts.build_live_availability_snapshot import run as build_availability
        from scripts.build_bls_block_schedule_pilot import write_page_outputs
        from scripts.block_start_time_selector import load_block_schedule_page_configs, build_block_schedule_page
        result = build_availability()
        require(not result['missing'], 'availability_inputs_missing')
        # BLS retains canonical remaining seats. Skills is independently gated,
        # restricted to course 509474 and its four existing context mappings.
        skills_enabled = policy.get('skillsEnabled', False)
        heartsaver_enabled = policy.get('heartsaverFullEnabled', False)
        pediatric_enabled = policy.get('pediatricExistingSessionEnabled', False)
        policy['_blsSkillsProof'] = load_publication_demand(ROOT).get('native_bls_skills_policy_proof')
        if preview:
            policy['enabled'] = True
        bls_skills_enabled = bool(scope.bls_course_ready(policy, '509474', datetime.now(timezone.utc)))
        bls_bundle_enabled = bool(scope.bls_course_ready(policy, '210549', datetime.now(timezone.utc)))
        configs = load_block_schedule_page_configs()
        targets = [(key, native_page_config(configs[key], key, skills_enabled=skills_enabled, heartsaver_enabled=heartsaver_enabled, bls_skills_enabled=bls_skills_enabled, bls_bundle_enabled=bls_bundle_enabled, pediatric_enabled=pediatric_enabled)) for key in publication_pages(skills_enabled, heartsaver_enabled, pediatric_enabled)]
        reports = {key: check_page_outputs(config, key) for key, config in targets}
        for key, config in targets:
            payload = annotate_seated_offers(build_block_schedule_page(config), schedule)
            payload = project_bls_offers(payload, schedule, policy, datetime.now(timezone.utc))
            payload = pediatric.project(payload, load_publication_demand(ROOT), policy, datetime.now(timezone.utc))
            page = write_page_outputs(payload, ROOT / reports[key][0], ROOT / reports[key][1], ROOT / config['output_path'])
            expected = {*PAGE_PATHS[key], *reports[key]}
            actual = {str(Path(p).relative_to(ROOT)) for p in page['output_paths']}
            require(actual == expected, 'unexpected_generator_output')
        evidence = validate()
        evidence.update(schemaVersion='native-publication-run.v1', sourceHead=head, preview=preview,
                        skillsEnabled=skills_enabled, heartsaverFullEnabled=heartsaver_enabled,
                        pediatricExistingSessionEnabled=pediatric_enabled,
                        blsSkillsEnabled=policy.get('blsSkillsEnabled', False), blsBundleEnabled=policy.get('blsBundleEnabled', False),
                        state='BUILT', generatedAt=datetime.now(timezone.utc).isoformat(),
                        sessionCounts=schedule['build']['counts'],
                        availabilityCounts={k: v for k, v in result['stats'].items() if type(v) is int},
                        files={p: sha256((ROOT / p).read_bytes()).hexdigest() for p in publication_paths(skills_enabled, heartsaver_enabled, pediatric_enabled)})
        write(REPORT, evidence)
        return evidence
    finally:
        (ROOT / POLICY).write_bytes(original)


def assert_manifest(report):
    require(report.get('schemaVersion') == 'native-publication-run.v1' and report.get('preview') is False,
            'production_manifest_required')
    require(set(report.get('files', {})) == set(publication_paths(report.get('skillsEnabled', False), report.get('heartsaverFullEnabled', False), report.get('pediatricExistingSessionEnabled',False))), 'publication_path_allowlist_mismatch')
    for path, expected in report['files'].items():
        require(sha256((ROOT / path).read_bytes()).hexdigest() == expected, 'publication_output_changed')


def publish():
    require(os.environ.get('GITHUB_REF') == 'refs/heads/main', 'main_required')
    policy = read(POLICY)
    require(policy_enabled(policy), 'native_publication_disabled')
    report = read(REPORT)
    assert_manifest(report)
    require(all(report.get(k, False) == policy.get(k, False) for k in ('blsSkillsEnabled','blsBundleEnabled')), 'bls_publication_gate_changed')
    require(report.get('skillsEnabled', False) == policy.get('skillsEnabled', False), 'skills_publication_gate_changed')
    require(report.get('heartsaverFullEnabled', False) == policy.get('heartsaverFullEnabled', False), 'heartsaver_publication_gate_changed')
    require(git('rev-parse', 'HEAD') == report['sourceHead'], 'source_head_changed')
    require(not git('diff', '--cached', '--name-only'), 'preexisting_staged_changes')
    require(not git('diff', '--name-only', '--', '.github', 'scripts', 'data/config', 'data/inventory'),
            'source_worktree_changed')
    # Do not rebase/cherry-pick an old proof onto a different source head.
    git('fetch', 'origin', 'main')
    require(git('rev-parse', 'origin/main') == report['sourceHead'], 'remote_main_advanced')
    validate(margin=300)
    paths = publication_paths(report.get('skillsEnabled', False), report.get('heartsaverFullEnabled', False), report.get('pediatricExistingSessionEnabled',False))
    git('add', '--', *paths)
    require(set(git('diff', '--cached', '--name-only').splitlines()) <= set(paths), 'staged_path_not_allowed')
    require(bool(git('diff', '--cached', '--name-only')), 'no_publication_change')
    git('commit', '-m', 'Publish first-party native availability')
    # A normal fast-forward push is the final race guard, never force/rebase.
    git('push', 'origin', 'HEAD:main')
    report.update(state='PUSHED_NOT_PROVEN', publicationHead=git('rev-parse', 'HEAD'))
    write(REPORT, report)


def observe():
    report = read(REPORT)
    assert_manifest(report)
    policy = read(POLICY)
    require(policy_enabled(policy) and report.get('skillsEnabled', False) == policy.get('skillsEnabled', False)
            and report.get('heartsaverFullEnabled', False) == policy.get('heartsaverFullEnabled', False),
            'publication_gate_changed')
    require(all(report.get(k, False) == policy.get(k, False) for k in ('blsSkillsEnabled','blsBundleEnabled')), 'bls_publication_gate_changed')
    require(report.get('publicationHead'), 'publication_commit_required')
    # HTTP hash proof of every changed public path, not a green Pages job alone.
    deadline = min(time.monotonic() + 240, time.monotonic() + max(0, (scope.instant(report['validUntil']) - datetime.now(timezone.utc)).total_seconds() - 60))
    while time.monotonic() < deadline:
        matched = True
        for path, expected in report['files'].items():
            request = urllib.request.Request('https://www.910cpr.com/' + path.removeprefix('docs/') + '?nativeProof=' + report['publicationHead'], headers={'Cache-Control': 'no-cache'})
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    matched = matched and sha256(response.read()).hexdigest() == expected
            except OSError:
                matched = False
        if matched:
            validate(margin=60)
            report.update(state='PROVEN', visibleProofAt=datetime.now(timezone.utc).isoformat())
            write(REPORT, report)
            return
        time.sleep(10)
    raise ValueError('visible_publication_missing_or_stale')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'build', 'validate', 'publish', 'observe'])
    parser.add_argument('--preview', action='store_true')
    args = parser.parse_args()
    require(not args.preview or args.action == 'build', 'preview_only_valid_for_build')
    if args.action == 'build':
        build(args.preview)
    else:
        globals()[args.action]()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Status artifact contains only an exception type. Arbitrary exception
        # text/URLs, calendar titles, credentials and private input never upload.
        write('debug/status/native_publication_failure.json', {'state': 'FAILED_OR_STALE', 'errorType': type(error).__name__, 'observedAt': datetime.now(timezone.utc).isoformat()})
        raise
