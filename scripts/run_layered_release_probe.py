"""Dry-run the existing V2 producer and customer renderer; never publish."""
import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
from scripts.block_start_time_selector import build_block_schedule_page, load_block_schedule_page_configs, apply_final_live_availability_guard
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload, public_reconciliation_issues, render_html
ROOT=Path(__file__).resolve().parents[1]

REQUIRED_PAGE_KEYS = frozenset({'bls', 'heartsaver', 'acls', 'pals', 'arc', 'hsi',
                                'uscg_first_aid_cpr_aed', 'family_cpr'})


def public_issue_summary(issues):
    """Artifacts and logs are public-repository outputs, not restricted traces."""
    safe = public_reconciliation_issues(issues)
    counts = Counter(row['reason'] for row in safe)
    by_date = {}
    for row in safe:
        date = row.get('start') or 'unscoped'
        by_date.setdefault(date, Counter())[row['reason']] += 1
    return dict(counts), {date: dict(counts) for date, counts in by_date.items()}


def coverage_release_passed(pages):
    """Require complete window evaluation; partial coverage is not a release pass."""
    if not pages or not REQUIRED_PAGE_KEYS.issubset(pages):
        return False
    total_windows = 0
    for row in pages.values():
        counts = row.get('counts') or {}
        values = [counts.get(key) for key in
                  ('input_windows', 'evaluated_windows', 'failed_windows')]
        if any(type(value) is not int or value < 0 for value in values):
            return False
        inputs, evaluated, failed = values
        if failed or evaluated != inputs:
            return False
        total_windows += inputs
    return total_windows > 0


def run():
    output=ROOT/'data/runtime/audit_previews/v2_release_probe'
    output.mkdir(parents=True,exist_ok=True)
    policy_path=ROOT/'data/config/layered_scheduling_policy.json'
    original=policy_path.read_bytes()
    policy=json.loads(original);policy['mode']='active_local_v2'
    result=dict(observed_at=datetime.now(timezone.utc).isoformat(),published=False,pages={})
    try:
        policy_path.write_text(json.dumps(policy),encoding='utf-8')
        snapshot=json.loads((ROOT/'data/audit/live_availability_snapshot_preview.json').read_text())
        result['calendar_coverage_count']=len(snapshot.get('layered_commitment_coverage',[]))
        canonical=json.loads((ROOT/'data/runtime/canonical_scheduling_demand.json').read_text())
        result['canonical_generated_at']=canonical.get('generated_at')
        result['canonical_session_count']=len(canonical.get('sessions',[]))
        for key, config in load_block_schedule_page_configs().items():
            payload=apply_final_live_availability_guard(build_block_schedule_page(config))
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
            issue_counts, issues_by_date = public_issue_summary(payload.get('reconciliationIssues', []))
            result['pages'][key]=dict(calculation_issue_counts=issue_counts,calculation_issues_by_date=issues_by_date,day_patterns=patterns,counts=payload.get('counts'),offer_roles=dict(Counter(o.get('scheduleRole') or o.get('offerType') for o in offers)),rejection_reasons=payload.get('rejectionReasonCounts'),synthesis_blocked_dates=payload.get('synthesisBlockedDates'),model=payload.get('schedulingModel'),valid_until=feed.get('validUntil'))
        result['calculation_completed']=True
        result['release_passed']=coverage_release_passed(result['pages'])
    finally:
        policy_path.write_bytes(original)
        (output/'proof.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    if not result.get("release_passed"):
        raise RuntimeError("V2 window coverage is incomplete or unproven; publication remains stopped")

if __name__=='__main__':run()
