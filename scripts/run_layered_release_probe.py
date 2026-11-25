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
    # Include the effective V2 policy after the disposable active-mode override.
    # Otherwise a mid-replay policy mutation would evade the source checksum.
    'data/config/layered_scheduling_policy.json',
    # These sources participate in travel, class-occupancy and native-skills decisions.
    # Keep them immutable across all eight families and both comparison worktrees.
    'data/config/travel_time_rules.json',
    'data/config/anchor_schedule_policy.json',
    'data/config/native_skills_activation.json',
    'data/config/calendar_sources.json',
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
_ROUTE_SOURCE_CATEGORIES = frozenset({
    "canonical_positive", "canonical_other", "legacy_inventory",
    "calendar_physical_or_unknown", "other_source", "scope_unassigned",
    "scope_selected_instructor", "scope_shared_resource",
    "interval_overlaps_window", "interval_outside_window",
})
_IDENTITY_COLLISION_CATEGORIES = frozenset(["identity_canonical","identity_legacy","identity_calendar","identity_other","identity_generated_unassigned","identity_cross_namespace","identity_same_namespace","identity_distinct_geometry","identity_same_geometry"])
# Actual selector keys returned by load_block_schedule_page_configs(): normalize_key
# changes the configured hyphenated USCG page to underscores in the replay output.
# The comparator must match actual runtime keys, not the raw config map's keys.
EXPECTED_FAMILIES = frozenset({
    "bls", "acls", "pals", "heartsaver", "uscg_first_aid_cpr_aed",
    "hsi", "arc", "family_cpr",
})


def _reason_category(reason):
    """Public artifact may contain reason *categories*, never freeform source details."""
    category = str(reason).split(":", 1)[0].lower()
    return category if _SAFE_REASON.fullmatch(category) else "unclassified"


def _window_issue_category(issue):
    """Map private per-window exception text to a fixed nonidentifying taxonomy."""
    value = str(issue.get("reason") or "").casefold()
    # Match fixed exception prefixes before inspecting the freeform suffix.
    # Identity values can contain arbitrary source text; never echo them.
    if value.startswith(("duplicate source id:", "duplicate durable source id",
                         "duplicate availability source identity")):
        return "duplicate_source_identity"
    if value.startswith(("invalid course duration:", "invalid evidenced course duration override:")):
        return "course_duration_policy_invalid"
    if value.startswith("invalid slot grid"):
        return "slot_grid_policy_invalid"
    if value.startswith("unresolved zero-duration occupancy"):
        return "unresolved_occupied_bounds"
    if "unresolved_occupied_bounds" in value:
        return "unresolved_occupied_bounds"
    if "travel" in value:
        return "travel_assumption_unverified"
    if "coverage" in value:
        return "commitment_coverage_unverified"
    if "instructor" in value:
        return "instructor_unverified"
    if "location" in value or "room" in value or "resource" in value:
        return "resource_unverified"
    if "duration" in value or "interval" in value:
        return "interval_unverified"
    return "other_window_error"


def coverage_complete(pages):
    """A diagnostic comparison can run on partial coverage; release cannot."""
    if set(pages) != EXPECTED_FAMILIES:
        return False
    for row in pages.values():
        counts = row.get("counts")
        if not isinstance(counts, dict):
            return False
        total, evaluated, failed = (counts.get(k) for k in
                                    ("input_windows", "evaluated_windows", "failed_windows"))
        if any(type(n) is not int or n < 0 for n in (total, evaluated, failed)):
            return False
        if total == 0 or evaluated != total or failed != 0:
            return False
    return True


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
        "diagnostic_passed": proof.get("diagnostic_passed") is True,
        "release_passed": (proof.get("diagnostic_passed") is True and
                           coverage_complete(proof.get("pages") or {})),
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
            "failed_window_issue_categories": row.get("failed_window_issue_categories") or {},
            "failed_route_source_categories": {key: count for key, count in
                (row.get("failed_route_source_categories") or {}).items()
                if key in _ROUTE_SOURCE_CATEGORIES and type(count) is int and count >= 0},
            "failed_identity_collision_categories": {key: count for key, count in
                (row.get("failed_identity_collision_categories") or {}).items()
                if key in _IDENTITY_COLLISION_CATEGORIES and type(count) is int and count >= 0},
            "synthesis_blocked_day_count": len(row.get("synthesis_blocked_dates") or []),
            "day_count": len(per_day),
            "next_three_days": counts_by_day[:3],
            "ninety_day_offer_counts": counts_by_day,
        }
    return safe



def compare_safe_summaries(main, draft):
    """Compare aggregate actual-engine replays; reject different sources or clocks.

    Main and draft must each be run against the identical captured inputs.
    This utility never treats a green calculation as hosted/public booking proof.
    """
    fields = ("source_snapshot_sha256", "replay_clock_utc", "horizon_start",
              "horizon_end", "horizon_days")
    for report in (main, draft):
        if (report.get("published") is not False or
                report.get("source_snapshot_unchanged") is not True or
                report.get("calculation_completed") is not True or
                report.get("diagnostic_passed") is not True):
            raise ValueError("Main/draft comparison requires completed, unpublished, frozen replays")
        if any(field not in report for field in fields):
            raise ValueError("Main/draft comparison missing snapshot or horizon evidence")
    if any(main[field] != draft[field] for field in fields):
        raise ValueError("Main/draft comparison source, clock or horizon mismatch")
    if not re.fullmatch(r"[0-9a-f]{64}", str(main["source_snapshot_sha256"])):
        raise ValueError("Main/draft comparison requires a valid SHA-256 fingerprint")
    clock = datetime.fromisoformat(main["replay_clock_utc"].replace("Z", "+00:00"))
    if clock.utcoffset() != timedelta(0):
        raise ValueError("Main/draft comparison requires an aware UTC clock")
    if main["horizon_days"] != 90:
        raise ValueError("Main/draft comparison requires the full 90-day horizon")
    try:
        first_day = datetime.fromisoformat(main["horizon_start"]).date()
    except (TypeError, ValueError) as exc:
        raise ValueError("Main/draft comparison has invalid calendar bounds") from exc
    # A matching but stale 90-day window is not valid proof for this
    # replay clock; both engines must cover the current ET horizon.
    if first_day != clock.astimezone(ZoneInfo("America/New_York")).date():
        raise ValueError("Main/draft horizon does not start on the replay clock's ET day")
    if (first_day + timedelta(days=89)).isoformat() != main["horizon_end"]:
        raise ValueError("Mismatched main/draft 90-day bounds")
    if (set(main.get("pages") or {}) != EXPECTED_FAMILIES or
            set(draft.get("pages") or {}) != EXPECTED_FAMILIES):
        raise ValueError("Main/draft comparison requires all eight exact public course families")

    families = {}
    for family in sorted(EXPECTED_FAMILIES):
        left = main["pages"][family].get("ninety_day_offer_counts")
        right = draft["pages"][family].get("ninety_day_offer_counts")
        if not isinstance(left, list) or not isinstance(right, list) or len(left) != 90 or len(right) != 90:
            raise ValueError("Main/draft comparison requires complete 90-day daily counts")
        aggregate = {role: {"main": 0, "draft": 0, "delta": 0} for role in _ROLES}
        changed_days = 0
        for index, (before_day, after_day) in enumerate(zip(left, right)):
            day = before_day.get("date")
            if (day != after_day.get("date") or day != (first_day + timedelta(days=index)).isoformat()):
                raise ValueError("Main/draft comparison day alignment failed")
            if day < main["horizon_start"] or day > main["horizon_end"]:
                raise ValueError("Main/draft comparison day outside bounded horizon")
            changed = False
            for role in _ROLES:
                a, b = before_day.get(role), after_day.get(role)
                if any(type(value) is not int or value < 0 for value in (a, b)):
                    raise ValueError("Main/draft comparison requires nonnegative integer offer counts")
                aggregate[role]["main"] += a
                aggregate[role]["draft"] += b
                changed |= a != b
            changed_days += int(changed)
        for values in aggregate.values():
            values["delta"] = values["draft"] - values["main"]
        coverage = {}
        for label, report in (("main", main), ("draft", draft)):
            counts = report["pages"][family].get("counts") or {}
            coverage[label] = {
                key: counts.get(key) if type(counts.get(key)) is int and counts[key] >= 0 else None
                for key in ("input_windows", "evaluated_windows", "failed_windows")
            }
        families[family] = {"offer_roles": aggregate, "days_with_different_counts": changed_days,
                            "window_coverage": coverage}
    return {"published": False, "same_source_verified": True,
            "registration_or_checkout_proven": False,
            "main_release_passed": main.get("release_passed") is True and coverage_complete(main["pages"]),
            "draft_release_passed": draft.get("release_passed") is True and coverage_complete(draft["pages"]),
            "source_snapshot_sha256": main["source_snapshot_sha256"],
            "replay_clock_utc": main["replay_clock_utc"],
            "horizon_start": main["horizon_start"], "horizon_end": main["horizon_end"],
            "horizon_days": 90, "families": families}

def run(*, replay_clock_utc: datetime | None = None):
    output=ROOT/'data/runtime/audit_previews/v2_release_probe'
    output.mkdir(parents=True,exist_ok=True)
    policy_path=ROOT/'data/config/layered_scheduling_policy.json'
    original=policy_path.read_bytes()
    policy=json.loads(original);policy['mode']='active_local_v2'
    frozen_now = replay_clock_utc if replay_clock_utc is not None else datetime.now(timezone.utc)
    if frozen_now.tzinfo is None or frozen_now.utcoffset() != timedelta(0):
        raise ValueError('Read-only replay requires an aware UTC clock')
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
            result['pages'][key]=dict(
                failed_route_source_categories=dict(Counter(category
                    for issue in (payload.get('layeredDiagnostics') or {}).get('issues', [])
                    for category in set(issue.get('route_source_categories') or [])
                    if category in _ROUTE_SOURCE_CATEGORIES)),
                failed_identity_collision_categories=dict(Counter(category
                    for issue in (payload.get('layeredDiagnostics') or {}).get('issues', [])
                    for category in set(issue.get('identity_collision_categories') or [])
                    if category in _IDENTITY_COLLISION_CATEGORIES)),
                failed_window_issue_categories=dict(Counter(_window_issue_category(issue) for issue in
                    (payload.get('layeredDiagnostics') or {}).get('issues', []))),
                calculation_issue_counts=dict(Counter(issue.get('code') or 'unclassified'
                    for issue in payload.get('reconciliationIssues',[]))),day_patterns=patterns,counts=payload.get('counts'),offer_roles=dict(Counter(o.get('scheduleRole') or o.get('offerType') for o in offers)),rejection_reasons=payload.get('rejectionReasonCounts'),synthesis_blocked_dates=payload.get('synthesisBlockedDates'),model=payload.get('schedulingModel'),valid_until=feed.get('validUntil'))
        result['source_snapshot_unchanged'] = source_fingerprint() == fingerprint
        if not result['source_snapshot_unchanged']:
            raise RuntimeError('Read-only V2 source changed during replay; no publication')
        result['calculation_completed']=True
        result['diagnostic_passed'] = (result['source_snapshot_unchanged'] and
            set(result['pages']) == EXPECTED_FAMILIES and all(
                isinstance(row.get('counts'), dict) and
                type(row['counts'].get('input_windows')) is int and
                type(row['counts'].get('evaluated_windows')) is int and
                0 < row['counts']['evaluated_windows'] <= row['counts']['input_windows']
                for row in result['pages'].values()))
        result['release_passed'] = (result['diagnostic_passed'] and
                                    coverage_complete(result['pages']))
    finally:
        policy_path.write_bytes(original)
        (output/'proof.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    if not result.get("diagnostic_passed"):
        raise RuntimeError("V2 could not evaluate current source windows; publication remains stopped")

if __name__=='__main__':run()
