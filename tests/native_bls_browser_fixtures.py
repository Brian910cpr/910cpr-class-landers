"""Disposable synthetic fixtures shared by browser and non-browser checks."""
from datetime import timedelta
import json
from pathlib import Path
import subprocess
from urllib.parse import parse_qs, urlsplit

from tests.test_native_bls_publication_runner import NativeBlsRunnerTests
from scripts import run_native_publication as runner
from scripts.block_start_time_selector import seated_class_selector_offers
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload, render_html
from scripts.layered_publication_adapter import finalize

ROOT = Path(__file__).resolve().parents[1]


def fixture(skills=True, bundle=True):
    return NativeBlsRunnerTests().fixture(skills, bundle)


def offers(feed):
    return [row for day in feed['dates'] for slot in day['startTimes'] for row in slot['courses']]


def selection(url):
    return {key: values[0] for key, values in parse_qs(urlsplit(url).query).items()}


def generic_model(case, feed, chosen, **kwargs):
    packet = dict(now=case.now.isoformat(), feed=feed, selection=chosen, **kwargs)
    result = subprocess.run(['node', str(ROOT / 'tests/helpers/native-bls-browser-model.mjs')],
                            input=json.dumps(packet), text=True, capture_output=True, check=True, cwd=ROOT)
    return json.loads(result.stdout)


def seated_fixture():
    case, payload = fixture()
    start = case.at(11, '11:00')
    sid = 'lw-11111111-1111-4111-8111-111111111111'
    source = dict(canonical_session_id='canonical-skills', external_class_id=sid, external_course_id='509474',
        source='landerware_event', registration_backend='landerware', registration_authority='landerware-generated-session.v1',
        session_status='scheduled', registration_status='open', visibility='public', workspace_projection_status='current',
        count_available=True, active_registration_count=1, canonical_registered_count=0, held_seat_count=1, unreconciled_reserved_count=0,
        start_at=start.isoformat(), end_at=(start+timedelta(minutes=45)).isoformat(), consumption_start_at=start.isoformat(),
        consumption_end_at=(start+timedelta(minutes=60)).isoformat(), location_name=':: Wilmington; Shipyard Blvd',
        lead_instructor_name='Brian Ennis', course_name='Skills Session Only',
        native_skills_booking_admission=dict(schemaVersion='native-skills-session-booking.v1', publicCourseId='509474',
            profileKey='native_skills_shared', profileVersion=2, capacity=2, remaining=1, sourceSessionId=sid,
            identityWitness='a'*32, qualificationPolicy=runner.scope.SKILLS_QUALIFICATION_POLICY,
            skillsContexts=['cpr-aed', 'first-aid-cpr-aed', 'arc-blended', 'hsi-blended', 'bls-skills']))
    demand = dict(generated_at=case.now.isoformat(), sessions=[source], native_bls_skills_policy_proof=case.native_policy['_blsSkillsProof'])
    schedule = runner.retained_projection({'sessions': []}, demand, bls_skills_enabled=True, bls_bundle_enabled=True, now=case.now)
    payload['offers'] = seated_class_selector_offers(schedule_future_payload=schedule, selected_courses=case.courses,
        selected_course_ids={'509474'}, course_rules={}, native_policy=case.native_policy, reference_now=case.now)
    payload = runner.annotate_seated_offers(payload, schedule)
    payload = runner.project_bls_offers(payload, schedule, case.native_policy, case.now)
    return case, finalize(payload, case.now), sid
