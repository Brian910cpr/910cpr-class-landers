"""Dry-run the existing V2 producer and customer renderer; never publish."""
import json
import hashlib
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import re
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


_SAFE_REASON = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_ROLES = ("anchor", "barnacle", "open")


def _reason_category(reason):
    """Public artifact may contain reason *categories*, never freeform source details."""
    category = str(reason).split(":", 1)[0].lower()
    return category if _SAFE_REASON.fullmatch(category) else "unclassified"


def public_safe_summary(proof):
    """Aggregate a real frozen replay without emitting source identities or slot times.

    This is one side of the requested main-versus-draft comparison, not a
    production deployment, public bookability, or end-to-end checkout proof.
    """
    if not proof.get("source_snapshot_unchanged") or not proof.get("source_snapshot_sha256"):
        raise ValueError("Cannot summarize an unfrozen source replay")
    clock = datetime.fromisoformat(str(proof["replay_clock_utc"]).replace("Z", "+00:00"))
    if clock.tzinfo is None:
        raise ValueError("Replay clock must be timezone-aware")
    first_day = clock.astimezone(ZoneInfo("America/New_York")).date()
    horizon = [(first_day + timedelta(days=i)).isoformat() for i in range(90)]
    safe = {
        "published": False,
        "calculation_completed": bool(proof.get("calculation_completed")),
        "release_passed": bool(proof.get("release_passed")),
        "source_snapshot_unchanged": True,
        "source_snapshot_sha256": proof["source_snapshot_sha256"],
        "replay_clock_utc": proof["replay_clock_utc"],
        "canonical_session_count": proof.get("canonical_session_count"),
        "calendar_coverage_count": proof.get("calendar_coverage_count"),
        "horizon_days": 90,
        "horizon_start": horizon[0],
        "horizon_end": horizon[-1],
        "pages": {},
    }
    for key, row in proof.get("pages", {}).items():
        per_day = row.get("day_patterns") or {}
        counts_by_day = []
        for day in horizon:
            roles = {role: 0 for role in _ROLES}
            for course in per_day.get(day, {}).values():
                for role in _ROLES:
                    roles[role] += len(course.get(role, []))
            counts_by_day.append({"date": day, **roles})
        reasons = {}
        for reason, count in (row.get("rejection_reasons") or {}).items():
            cat = _reason_category(reason)
            reasons[cat] = reasons.get(cat, 0) + int(count)
        uncertainty = {}
        # These are calendar-collision reconciliation *codes*, not the
        # failed/unknown availability-window reasons in counts["failed_windows"].
        for reason, count in (row.get("calculation_issue_counts") or {}).items():
            cat = _reason_category(reason)
            uncertainty[cat] = uncertainty.get(cat, 0) + int(count)
        safe["pages"][key] = {
            "counts": row.get("counts"),
            "offer_roles": row.get("offer_roles"),
            "rejection_reason_categories": reasons,
            "reconciliation_issue_code_categories": uncertainty,
            "synthesis_blocked_day_count": len(row.get("synthesis_blocked_dates") or []),
            "day_count": len(per_day),
            "next_three_days": counts_by_day[:3],
            "ninety_day_offer_counts": counts_by_day,
        }
    return safe


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
            result['pages'][key]=dict(calculation_issue_counts=dict(Counter(issue.get('code') or 'unclassified' for issue in payload.get('reconciliationIssues',[]))),day_patterns=patterns,counts=payload.get('counts'),offer_roles=dict(Counter(o.get('scheduleRole') or o.get('offerType') for o in offers)),rejection_reasons=payload.get('rejectionReasonCounts'),synthesis_blocked_dates=payload.get('synthesisBlockedDates'),model=payload.get('schedulingModel'),valid_until=feed.get('validUntil'))
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
