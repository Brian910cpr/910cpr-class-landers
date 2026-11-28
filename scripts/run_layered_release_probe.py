"""Dry-run the existing V2 producer and customer renderer; never publish."""
import json
import os
import subprocess
from contextlib import nullcontext
from unittest.mock import patch
from pathlib import Path
from collections import Counter
from datetime import date, datetime, timezone
from scripts.block_start_time_selector import build_block_schedule_page, load_block_schedule_page_configs, apply_final_live_availability_guard
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload, public_reconciliation_issues, render_html
from scripts import layered_release_oracle as oracle
from scripts.canonical_scheduling_demand import load_publication_demand
from scripts.validate_layered_occupancy_projection import OccupancyGate, REQUIRED_PAGES
ROOT=Path(__file__).resolve().parents[1]

REQUIRED_PAGE_KEYS = REQUIRED_PAGES


def public_issue_summary(issues):
    """Artifacts and logs are public-repository outputs, not restricted traces."""
    safe = public_reconciliation_issues(issues)
    counts = Counter(row['reason'] for row in safe)
    by_date = {}
    for row in safe:
        date = row.get('start') or 'unscoped'
        by_date.setdefault(date, Counter())[row['reason']] += 1
    return dict(counts), {date: dict(counts) for date, counts in by_date.items()}


PUBLIC_REJECTION_CODES = frozenset({
    "conflict_or_transition", "commitment_coverage_unknown",
    "short_skills_duration_exceeds_limit", "instructor_not_qualified",
    "course_location_not_allowed", "outside_explicit_availability",
    "lead_time", "off_grid_start", "full_course_already_paid_seated",
    "full_family_already_paid_seated", "full_course_repeat_within_24_hours",
    "full_course_count_unknown", "full_family_count_unknown",
    "course_family_not_allowed_by_availability",
    "location_not_allowed_by_public_policy", "missing_owned_appointment_url",
    "expired_coverage_proof", "nonpublic_occupied_not_joinable",
    "confirmed_zero_existing_booking_choice_retired",
    "seated_instructor_mismatch", "existing_course_day_anchor",
    "anchored_day_requires_attached_offer", "expired_or_missing_scoped_lease",
})


def public_rejection_counts(counts):
    """Keep only allowlisted categories, never source-bearing reason strings."""
    safe = Counter()
    for reason, count in (counts or {}).items():
        if type(count) is not int or count <= 0:
            continue
        category = str(reason).partition(":")[0]
        safe[category if category in PUBLIC_REJECTION_CODES else "other_rejection"] += count
    return dict(safe)


def aggregate_page_proof(payload, feed):
    """No offered times, source metadata, or unreviewed payload fields leave CI."""
    counts = payload.get("counts") or {}
    roles = Counter()
    for day in feed.get("dates", []):
        for slot in day.get("startTimes", []):
            for course in slot.get("courses", []):
                role = ("seated" if course.get("offerType") == "seated_class"
                        else "barnacle" if course.get("scheduleRole") == "barnacle"
                        else "open")
                roles[role] += 1
    issue_counts, _ = public_issue_summary(payload.get("reconciliationIssues", []))
    return {
        "calculation_issue_counts": issue_counts,
        "counts": {key: counts[key] for key in
                   ("input_windows", "evaluated_windows", "failed_windows")
                   if type(counts.get(key)) is int and counts[key] >= 0},
        "offer_roles": dict(roles),
        "rejection_reasons": public_rejection_counts(payload.get("rejectionReasonCounts")),
        "synthesis_blocked_date_count": len(payload.get("synthesisBlockedDates") or []),
    }


def coverage_passed(pages):
    """Window accounting only; not proof the customer can see the right choices."""
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



# Comparator only: the protected runner must independently build and attest the
# expected scope and tuples before it may use this result. This does not enable
# release or payment, and the runner deliberately remains unproven.
VALID_ZERO_REASONS = frozenset({
    "no_qualified_coverage", "outside_lead_time", "all_hard_blocked",
    "repeat_gap", "no_legal_bookend", "nonpublic_not_joinable",
    "no_authorized_route", "container_unavailable",
})
OFFER_ROLES = frozenset({"open", "barnacle", "seated"})
OFFER_CAPABILITIES = frozenset({"request_only", "verified_booking"})


def compare_expected_outcomes(required_scopes, expected, observed, *,
                              expected_epoch, observed_epoch):
    """Compare restricted normalized offers, returning only fixed aggregate counts.

    Scope: (page, local_date, instructor_key, course_key).
    Offer: (start_utc, end_utc, room_key, role, capability).
    Expected scope values: {"offers": [...], "zero_reason": optional code}.
    Observed scope values: lists of offers, including explicit empty lists.
    Scope and epoch must be supplied by a trusted independent source adapter.
    Matching inputs here are not evidence that the adapter is independent.
    """
    result = dict(status="unproven", missing_scope_count=0,
                  unexpected_scope_count=0, missing_offer_count=0,
                  unexpected_offer_count=0, invalid_scope_count=0,
                  invalid_offer_count=0, duplicate_offer_count=0)
    if (not isinstance(expected_epoch, str) or not expected_epoch.strip()
            or expected_epoch != observed_epoch or not required_scopes
            or not isinstance(expected, dict) or not isinstance(observed, dict)):
        return result

    def valid_scope(scope):
        if not (isinstance(scope, tuple) and len(scope) == 4
                and all(isinstance(part, str) and part.strip() for part in scope)
                and scope[0] in REQUIRED_PAGE_KEYS):
            return False
        try:
            return date.fromisoformat(scope[1]).isoformat() == scope[1]
        except ValueError:
            return False

    def offer_counts(rows, scope):
        if not isinstance(rows, (list, tuple)):
            result["invalid_offer_count"] += 1
            return Counter()
        counts = Counter()
        for row in rows:
            if (not isinstance(row, (list, tuple)) or len(row) != 5
                    or not all(isinstance(part, str) and part.strip() for part in row)
                    or row[3] not in OFFER_ROLES or row[4] not in OFFER_CAPABILITIES):
                result["invalid_offer_count"] += 1
                continue
            try:
                start, end = map(oracle.instant, row[:2])
                if end <= start or start.astimezone(oracle.ET).date().isoformat() != scope[1]:
                    raise ValueError("invalid bounds")
                key = (start.astimezone(timezone.utc), end.astimezone(timezone.utc), *row[2:])
            except (ValueError, OverflowError):
                result["invalid_offer_count"] += 1
                continue
            counts[key] += 1
        result["duplicate_offer_count"] += sum(n - 1 for n in counts.values())
        return counts

    if not isinstance(required_scopes, (set, frozenset, list, tuple)):
        return result
    if not all(valid_scope(scope) for scope in required_scopes):
        result["invalid_scope_count"] += 1
        return result
    required = set(required_scopes)
    if len(required) != len(required_scopes):
        result["invalid_scope_count"] += len(required_scopes) - len(required)
    if {scope[0] for scope in required} != REQUIRED_PAGE_KEYS:
        return result
    for collection in (expected, observed):
        result["missing_scope_count"] += len(required - collection.keys())
        result["unexpected_scope_count"] += len(collection.keys() - required)
    for scope in required & expected.keys() & observed.keys():
        entry = expected[scope]
        if not isinstance(entry, dict) or "offers" not in entry:
            result["invalid_scope_count"] += 1
            continue
        wanted = offer_counts(entry["offers"], scope)
        actual = offer_counts(observed[scope], scope)
        reason = entry.get("zero_reason")
        if ((not wanted and (not isinstance(reason, str) or reason not in VALID_ZERO_REASONS))
                or (wanted and reason is not None)):
            result["invalid_scope_count"] += 1
        result["missing_offer_count"] += sum((wanted - actual).values())
        result["unexpected_offer_count"] += sum((actual - wanted).values())
    result["status"] = ("mismatch" if any(value for key, value in result.items()
                                          if key != "status") else "matched")
    return result


def run(oracle_file=None):
    output=ROOT/'data/runtime/audit_previews/v2_release_probe'
    output.mkdir(parents=True,exist_ok=True)
    policy_path=ROOT/'data/config/layered_scheduling_policy.json'
    original=policy_path.read_bytes()
    policy=json.loads(original);policy['mode']='active_local_v2'
    result=dict(observed_at=datetime.now(timezone.utc).isoformat(),published=False,pages={},coverage_passed=False,
                outcome_status='unproven',release_passed=False)
    try:
        configs = load_block_schedule_page_configs()
        frozen = None
        if oracle_file is not None:
            try:
                manifest = json.loads(Path(oracle_file).read_text(encoding="utf-8"))
                hashes = oracle.freeze_inputs(ROOT)
                frozen = oracle.configure(manifest, hashes, configs, REQUIRED_PAGE_KEYS,
                                          Path(oracle_file).parent / "authorities")
            except (ValueError, KeyError, TypeError, OSError, AttributeError, OverflowError):
                # Private authority files, names, paths and errors never leave CI.
                result["outcome_status"] = "invalid_independent_manifest"
        if frozen is not None:
            now, required, expected = frozen
            from scripts import block_start_time_selector as selector
            reference = selector.selector_reference_datetime
            clock = patch.object(selector, "selector_reference_datetime",
                lambda explicit=None: reference(now if explicit is None else explicit))
        else:
            clock = nullcontext()
        feeds, html_pages = {}, {}
        policy_path.write_text(json.dumps(policy),encoding='utf-8')
        snapshot=json.loads((ROOT/'data/audit/live_availability_snapshot_preview.json').read_text())
        result['calendar_coverage_count']=len(snapshot.get('layered_commitment_coverage',[]))
        canonical=load_publication_demand(ROOT)
        gate=OccupancyGate(canonical, active=True)
        result['canonical_session_count']=len(canonical.get('sessions',[]))
        with clock:
            for key, config in configs.items():
                payload=apply_final_live_availability_guard(build_block_schedule_page(config))
                gate.observe(key, payload)
                feed=public_selector_availability_payload(payload)
                (output/(key+'.json')).write_text(json.dumps(feed,ensure_ascii=False),encoding='utf-8')
                html=render_html(payload).replace('<body>','<body><aside>READ-ONLY RELEASE PROBE: not published.</aside>',1)
                (output/(key+'.html')).write_text(html,encoding='utf-8')
                if key in REQUIRED_PAGE_KEYS:
                    result['pages'][key] = aggregate_page_proof(payload, feed)
                    feeds[key], html_pages[key] = feed, html
        gate.finish(load_publication_demand(ROOT))
        result['canonical_projection']=gate.summary()
        result['calculation_completed']=True
        result['coverage_passed']=coverage_passed(result['pages'])
        if frozen is not None:
            try:
                if oracle.freeze_inputs(ROOT, policy_bytes=original) != hashes:
                    result["outcome_status"] = "inputs_changed_during_replay"
                else:
                    observed = oracle.observed_outcomes(ROOT, feeds, html_pages, configs, manifest, now, required)
                    comparison = compare_expected_outcomes(required, expected, observed,
                        expected_epoch=manifest["epoch"], observed_epoch=oracle.epoch_for(now, hashes))
                    result["local_replay_comparison"] = comparison
                    result["outcome_status"] = ("local_replay_matched" if comparison["status"] == "matched"
                        else comparison["status"])
            except (ValueError, KeyError, TypeError, OSError, AttributeError, OverflowError, subprocess.SubprocessError):
                result["outcome_status"] = "unresolved_customer_preview"
        # A local match is not hosted route/privacy/checkout proof. No activation.
    except Exception:
        if oracle_file is None:
            raise
        result["outcome_status"] = "preview_failed"
    finally:
        policy_path.write_bytes(original)
        (output/'proof.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    if not result.get("release_passed"):
        raise RuntimeError("V2 independent customer outcome is unproven; publication remains stopped")

if __name__=='__main__':run(os.getenv("LAYERED_INDEPENDENT_ORACLE_FILE"))

