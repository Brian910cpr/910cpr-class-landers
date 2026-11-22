"""Dry-run the existing V2 producer and customer renderer; never publish."""
import json
import hashlib
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
from scripts.block_start_time_selector import build_block_schedule_page, load_block_schedule_page_configs, apply_final_live_availability_guard
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload, render_html
ROOT=Path(__file__).resolve().parents[1]
# Freeze the exact source/config bytes read by each course-family calculation.
SOURCE_PATHS = (
    'data/runtime/canonical_scheduling_demand.json',
    'data/audit/live_availability_snapshot_preview.json',
    'data/sessions_current.json',
    'docs/data/schedule_future.json',
    'data/inventory/appointment_containers.json',
    'data/inventory/course_consumption_rules.json',
    'data/config/course_catalog.json',
    'data/config/people_catalog.json',
    'data/config/location_resource_map.json',
    'data/config/public_location_policy.json',
    'data/config/public_offer_policy.json',
    'data/config/block_schedule_pages.json',
)

def source_fingerprint(root=ROOT):
    digest = hashlib.sha256()
    for relative in SOURCE_PATHS:
        data = (root / relative).read_bytes()
        digest.update(relative.encode('utf-8') + b'\0')
        digest.update(data + b'\0')
    return digest.hexdigest()

def run():
    output=ROOT/'data/runtime/audit_previews/v2_release_probe'
    output.mkdir(parents=True,exist_ok=True)
    policy_path=ROOT/'data/config/layered_scheduling_policy.json'
    original=policy_path.read_bytes()
    policy=json.loads(original);policy['mode']='active_local_v2'
    frozen_now = datetime.now(timezone.utc)
    result=dict(observed_at=frozen_now.isoformat(), replay_clock_utc=frozen_now.isoformat(),
                published=False, source_snapshot_unchanged=False, pages={})
    try:
        policy_path.write_text(json.dumps(policy),encoding='utf-8')
        fingerprint = source_fingerprint()
        result['source_snapshot_sha256'] = fingerprint
        snapshot=json.loads((ROOT/'data/audit/live_availability_snapshot_preview.json').read_text())
        result['calendar_coverage_count']=len(snapshot.get('layered_commitment_coverage',[]))
        canonical=json.loads((ROOT/'data/runtime/canonical_scheduling_demand.json').read_text())
        result['canonical_generated_at']=canonical.get('generated_at')
        result['canonical_session_count']=len(canonical.get('sessions',[]))
        for key, config in load_block_schedule_page_configs().items():
            payload=apply_final_live_availability_guard(build_block_schedule_page(config, replay_now=frozen_now))
            if source_fingerprint() != fingerprint:
                raise RuntimeError('Read-only V2 input drifted between course families; no publication')
            feed=public_selector_availability_payload(payload)
            (output/(key+'.json')).write_text(json.dumps(feed,ensure_ascii=False),encoding='utf-8')
            html=render_html(payload).replace('<body>','<body><aside>READ-ONLY RELEASE PROBE: not published.</aside>',1)
            (output/(key+'.html')).write_text(html,encoding='utf-8')
            offers=payload.get('offers',[])
            patterns={}
            for day in feed.get('dates',[]):
                courses={}
                for slot in day.get('startTimes',[]):
                    for course in slot.get('courses',[]):
                        role='anchor' if course.get('offerType')=='seated_class' else ('barnacle' if course.get('scheduleRole')=='barnacle' else 'open')
                        courses.setdefault(course['courseId'],dict(anchor=[],barnacle=[],open=[]))[role].append(slot['startTime'])
                patterns[day['date']]=courses
            result['pages'][key]=dict(calculation_issue_counts=dict(Counter(issue.get('reason') or 'unclassified' for issue in payload.get('reconciliationIssues',[]))),day_patterns=patterns,counts=payload.get('counts'),offer_roles=dict(Counter(o.get('scheduleRole') or o.get('offerType') for o in offers)),rejection_reasons=payload.get('rejectionReasonCounts'),synthesis_blocked_dates=payload.get('synthesisBlockedDates'),model=payload.get('schedulingModel'),valid_until=feed.get('validUntil'))
        result['source_snapshot_unchanged'] = source_fingerprint() == fingerprint
        if not result['source_snapshot_unchanged']:
            raise RuntimeError('Read-only V2 source changed during replay; no publication')
        result['calculation_completed']=True
        result['release_passed']=result['source_snapshot_unchanged'] and all(
            not (row['counts'].get('input_windows',0)>0 and row['counts'].get('evaluated_windows',0)==0)
            for row in result['pages'].values())
    finally:
        policy_path.write_bytes(original)
        (output/'proof.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    if not result.get("release_passed"):
        raise RuntimeError("V2 could not evaluate current source windows; publication remains stopped")

if __name__=='__main__':run()
