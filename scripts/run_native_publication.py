"""Bounded first-party publication. Never imports an external session fetcher.

Historical occurrence geometry is retained conservatively. Canonical demand owns
counts and new native sessions; absence/uncertainty never means zero occupancy.
Only six explicit public paths may be committed by this runner.
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
from scripts.canonical_scheduling_demand import load_publication_demand, resolve_canonical_demand
from scripts.validate_public_refresh_output import validate_selector, session_rows

ROOT = Path(__file__).resolve().parents[1]
POLICY = 'data/config/native_publication_scope.json'
REPORT = 'debug/status/native_publication.json'
PATHS = ('docs/data/schedule_future.json', 'docs/bls.html', 'docs/BLS.html',
         'docs/bls-schedule.html', 'docs/data/block-selector-availability/bls.json',
         'docs/assets/resolved-selector-availability.js')
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
uncertainty_scope'''.split())
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
            and type(policy.get('enabled')) is bool and policy.get('scopeId') == scope.SCOPE,
            'invalid_native_publication_policy')
    return policy['enabled']


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


def retained_projection(retained, demand):
    rows = session_rows(retained)
    require(isinstance(retained, dict) and isinstance(retained.get('sessions'), list), 'retained_occurrences_required')
    ids = [str(row.get('session_id') or '') for row in rows]
    require(all(ids) and len(set(ids)) == len(ids), 'retained_occurrence_identity_invalid')
    # Preserve every retained occurrence, including unknown, private/closed and
    # moved geometry as conservative occupancy. The engine also reads the entire
    # canonical demand separately, so private and offsite commitments still block.
    projected, _ = resolve_canonical_demand(rows, demand['sessions'])
    require(set(ids) <= {str(row.get('session_id') or '') for row in projected}, 'retained_occurrence_lost')
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
        if admission:
            row.update(native_booking_admission=admission, public_direct_booking=True,
                       registration_url='/register/?session='+str(row['session_id']))
    privacy_check(projected)
    return {'build': {'source_mode': 'native_canonical_with_retained_occurrences',
                      'generated_at': demand['generated_at'],
                      'counts': {'retained_sessions': len(rows), 'sessions_output': len(projected)}},
            'sessions': projected}


def prepare():
    require(policy_enabled(read(POLICY)), 'native_publication_disabled')
    demand = load_publication_demand(ROOT)
    output = retained_projection(read('docs/data/schedule_future.json'), demand)
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
    demand = load_publication_demand(ROOT)
    bounds = calendar_bounds(now)
    # A fresh publication timestamp never renews source observation timestamps.
    expiry = min(bounds['validUntil'], scope.instant(demand['generated_at']) + timedelta(minutes=15))
    check_budget(expiry, now, margin)
    schedule = read('docs/data/schedule_future.json')
    privacy_check(schedule)
    expected_rows = {str(row['session_id']): row for row in retained_projection(schedule, demand)['sessions']}
    for row in session_rows(schedule):
        expected = expected_rows[str(row['session_id'])]
        require(row.get('native_booking_admission') == expected.get('native_booking_admission')
                and row.get('public_direct_booking') == expected.get('public_direct_booking'),
                'native_admission_source_changed')
        if row.get('public_direct_booking') is True:
            admission = row.get('native_booking_admission')
            require(isinstance(admission, dict) and row.get('registration_url') == '/register/?session='+str(row.get('session_id')), 'unadmitted_session_registration_cta')
            check_budget(admission['validUntil'], now, margin)
        else:
            require(not row.get('registration_url'), 'unadmitted_session_registration_cta')
    ids = {str(row['session_id']) for row in session_rows(schedule)}
    counts = validate_selector('bls', ids, now=now)
    selector = read('docs/data/block-selector-availability/bls.json')
    # Public authority.description is fixed implementation text, not user data.
    privacy_check({k: v for k, v in selector.items() if k != 'authority'})
    originals = []
    for day in selector['dates']:
        for slot in day['startTimes']:
            for offer in slot['courses']:
                if offer.get('offerType') == 'seated_class':
                    validate_seated_offer(offer, schedule, now, margin)
                    continue
                require(offer.get('offerType') == 'dynamic_appointment'
                        and offer.get('authority') == 'native-full-course.v2'
                        and str(offer.get('courseId')) in scope.COURSES,
                        'unadmitted_public_offer')
                url = urlsplit(offer.get('registrationUrl') or offer.get('appointmentUrl') or '')
                require(not url.netloc and not url.scheme and url.path == '/register/skills-session/', 'external_dynamic_destination')
                if offer.get('authority') == 'native-full-course.v2':
                    check_budget(offer['validUntil'], now, margin)
                    originals.append(scope.instant(offer['proofObservedAt']))
    require(not originals or min(originals) == bounds['observedAt'], 'calendar_original_proof_mismatch')
    return {'counts': counts, 'sourceProofObservedAt': min(bounds['observedAt'], scope.instant(demand['generated_at'])).isoformat(),
            'validUntil': expiry.isoformat(), 'nativeFullOffers': len(originals)}


def annotate_seated_offers(payload, schedule):
    rows = {str(row['session_id']): row for row in session_rows(schedule)}
    for offer in payload.get('offers', []):
        if offer.get('offerType') != 'seated_class':
            continue
        sid = str((offer.get('sourceAvailabilityBlock') or {}).get('sessionId') or '')
        row = rows.get(sid, {})
        admission = row.get('native_booking_admission')
        require(row.get('public_direct_booking') is True and isinstance(admission, dict), 'unadmitted_seated_offer')
        offer.update(authority='native-session-booking.v1', session_id=sid,
            capacity=admission['capacity'], remainingSeats=admission['remaining'],
            proofObservedAt=admission['proofObservedAt'], validUntil=admission['validUntil'])
    return payload


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


def native_page_config(config):
    config = deepcopy(config)
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
    return config


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
        # Full-course native admission only. Existing classes remain scheduler
        # blockers; no seated, skills or bundle CTA is implied by this rollout.
        config = native_page_config(load_block_schedule_page_configs()['bls'])
        payload = annotate_seated_offers(build_block_schedule_page(config), schedule)
        page = write_page_outputs(payload, ROOT / config['report_json_path'],
                                  ROOT / config['report_md_path'], ROOT / config['output_path'])
        public_paths = {str(Path(p).relative_to(ROOT)) for p in page['output_paths'] if Path(p).is_relative_to(ROOT / 'docs')}
        require(public_paths == set(PATHS) - {'docs/data/schedule_future.json', 'docs/assets/resolved-selector-availability.js'}, 'unexpected_generator_output')
        evidence = validate()
        evidence.update(schemaVersion='native-publication-run.v1', sourceHead=head, preview=preview,
                        state='BUILT', generatedAt=datetime.now(timezone.utc).isoformat(),
                        sessionCounts=schedule['build']['counts'],
                        availabilityCounts={k: v for k, v in result['stats'].items() if type(v) is int},
                        files={p: sha256((ROOT / p).read_bytes()).hexdigest() for p in PATHS})
        write(REPORT, evidence)
        return evidence
    finally:
        (ROOT / POLICY).write_bytes(original)


def assert_manifest(report):
    require(report.get('schemaVersion') == 'native-publication-run.v1' and report.get('preview') is False,
            'production_manifest_required')
    require(set(report.get('files', {})) == set(PATHS), 'publication_path_allowlist_mismatch')
    for path, expected in report['files'].items():
        require(sha256((ROOT / path).read_bytes()).hexdigest() == expected, 'publication_output_changed')


def publish():
    require(os.environ.get('GITHUB_REF') == 'refs/heads/main', 'main_required')
    require(policy_enabled(read(POLICY)), 'native_publication_disabled')
    report = read(REPORT)
    assert_manifest(report)
    require(git('rev-parse', 'HEAD') == report['sourceHead'], 'source_head_changed')
    require(not git('diff', '--cached', '--name-only'), 'preexisting_staged_changes')
    require(not git('diff', '--name-only', '--', '.github', 'scripts', 'data/config', 'data/inventory'),
            'source_worktree_changed')
    # Do not rebase/cherry-pick an old proof onto a different source head.
    git('fetch', 'origin', 'main')
    require(git('rev-parse', 'origin/main') == report['sourceHead'], 'remote_main_advanced')
    validate(margin=300)
    git('add', '--', *PATHS)
    require(set(git('diff', '--cached', '--name-only').splitlines()) <= set(PATHS), 'staged_path_not_allowed')
    require(bool(git('diff', '--cached', '--name-only')), 'no_publication_change')
    git('commit', '-m', 'Publish first-party native availability')
    # A normal fast-forward push is the final race guard, never force/rebase.
    git('push', 'origin', 'HEAD:main')
    report.update(state='PUSHED_NOT_PROVEN', publicationHead=git('rev-parse', 'HEAD'))
    write(REPORT, report)


def observe():
    report = read(REPORT)
    assert_manifest(report)
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
