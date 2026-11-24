"""Read-only coverage checkpoint. Never infer free space from blank graph cells.

No generators, credentials, booking requests or source mutations. Public feeds
carry window-level failures separately from candidate rejection counts.
"""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import hashlib
import json
import re
from pathlib import Path
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ('bls', 'heartsaver', 'acls', 'pals', 'arc', 'hsi', 'uscg_first_aid_cpr_aed', 'family_cpr')


_PUBLIC_ISSUE_REASONS = frozenset({"missing_directional_travel_rule", "availability_coverage_unknown"})


def safe_issue_reason(issue):
    """Do not propagate unapproved raw diagnostic text into observer artifacts."""
    reason = issue.get("reason") if isinstance(issue, dict) else None
    return reason if isinstance(reason, str) and reason in _PUBLIC_ISSUE_REASONS else "restricted"


def public_diagnostics_safe(issues):
    """Fail closed if a public selector exposes operational issue metadata.

    Public issue entries can carry only a coarse reason code and an optional
    Eastern date. Never echo a rejected raw issue into observer artifacts.
    """
    if not isinstance(issues, list):
        return False
    for issue in issues:
        if not isinstance(issue, dict) or not set(issue).issubset({"reason", "start"}):
            return False
        if safe_issue_reason(issue) == "restricted":
            return False
        if "start" in issue and (
            not isinstance(issue["start"], str)
            or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", issue["start"]) is None
        ):
            return False
    return True



def public_landscape_diagnostics_safe(payload):
    """Audit the actual publicly hosted admin-named JSON without logging private values."""
    if not isinstance(payload, dict):
        return False
    if not set(payload).issubset({
        "schemaVersion", "generatedAt", "builtAt", "buildId", "pageId",
        "timezone", "window", "timeGrid", "courses", "lanes", "laneCells",
        "cells", "sourcePages", "reconciliationIssues", "dailyTruth",
        "authority", "note",
    }):
        return False

    def rows_with_fields(rows, allowed):
        return isinstance(rows, list) and all(
            isinstance(row, dict) and set(row).issubset(allowed) for row in rows
        )

    if not rows_with_fields(payload.get("cells", []), {
        "date", "startTime", "courseId", "courseFamily", "pageKey",
        "result", "reasons",
    }):
        return False
    allowed_reasons = {
        "public_selectable", "dynamic_appointment", "seated_class",
        "synthetic_offer", "ORPHAN_SYNTHETIC_OFFER",
        "RECONCILIATION_REQUIRED", "availability_restricted",
    }
    for cell in payload.get("cells", []):
        if not isinstance(cell.get("reasons", []), list) or not all(
            isinstance(reason, str) and reason in allowed_reasons
            for reason in cell.get("reasons", [])
        ):
            return False

    if not rows_with_fields(payload.get("laneCells", []), {
        "date", "startTime", "laneId", "result", "sourceLabel",
        "items", "reasons",
    }):
        return False
    for row in payload.get("laneCells", []):
        if row.get("laneId") not in ("brian", "enrollware"):
            return False
        if not rows_with_fields(row.get("items", []), {"title"}):
            return False
        if any(item.get("title") != "Occupied interval" for item in row.get("items", [])):
            return False
        if row.get("sourceLabel") not in ("Unavailable time", "Committed class"):
            return False

    daily = payload.get("dailyTruth", {})
    if not isinstance(daily, dict):
        return False
    for day, facts in daily.items():
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", day) is None or not isinstance(facts, dict):
            return False
        if set(facts) != {"hardBlocks", "classes"}:
            return False
        if not rows_with_fields(facts["hardBlocks"], {"label", "start", "end"}):
            return False
        if not rows_with_fields(facts["classes"], {"courseName", "start", "end", "registeredCount"}):
            return False
        if any(x.get("label") != "Unavailable time" for x in facts["hardBlocks"]):
            return False
        if any(x.get("courseName") != "Committed class"
               or x.get("registeredCount") != "Restricted" for x in facts["classes"]):
            return False

    issues = payload.get("reconciliationIssues", [])
    if not rows_with_fields(issues, {"date", "code", "reason", "blocksSynthesis"}):
        return False
    for issue in issues:
        if issue.get("reason") != "Availability requires operational review":
            return False
        if issue.get("code") not in (
            "ORPHAN_SYNTHETIC_OFFER", "HARD_BLOCK_COLLISION",
            "RECONCILIATION_REQUIRED", "AVAILABILITY_COVERAGE_UNKNOWN",
        ):
            return False

    pages = payload.get("sourcePages", {})
    if not isinstance(pages, dict):
        return False
    for family, row in pages.items():
        if family not in FAMILIES or not isinstance(row, dict):
            return False
        if not set(row).issubset({
            "generatedAt", "schedulingModel", "counts", "rejectionReasonCounts",
            "layeredLandscape",
        }):
            return False
        if not isinstance(row.get("rejectionReasonCounts"), dict) or not set(
            row["rejectionReasonCounts"]
        ).issubset({"restricted"}):
            return False
        landscape = row.get("layeredLandscape", {})
        if not isinstance(landscape, dict) or not set(landscape).issubset({
            "sources", "occupiedBlocks", "offersAreAlternatives", "availabilityIsNotAClass",
        }):
            return False
        if not rows_with_fields(landscape.get("sources", []), {"role", "start", "end"}):
            return False
        if not rows_with_fields(landscape.get("occupiedBlocks", []), {"start", "end"}):
            return False
    return True



def public_shipyard_alias_check(payload):
    """Audit displayed offers only; never copy operational room IDs into public evidence."""
    checked = 0
    for date in payload.get('dates', []):
        for start in date.get('startTimes', []):
            for course in start.get('courses', []):
                location = course.get('location', '')
                if not isinstance(location, str):
                    return False, checked
                if 'Shipyard Blvd' in location:
                    checked += 1
                    if location != 'Wilmington; Shipyard Blvd':
                        return False, checked
    return True, checked


def lead_window_status(day, cutoff):
    """Only classify the clock cutoff; never infer a free instructor or outage."""
    if cutoff is None:
        return 'unknown'
    eastern = ZoneInfo('America/New_York')
    start_day = datetime.fromisoformat(day).date()
    start = datetime.combine(start_day, datetime.min.time(), tzinfo=eastern).astimezone(timezone.utc)
    end = datetime.combine(start_day + timedelta(days=1), datetime.min.time(),
                           tzinfo=eastern).astimezone(timezone.utc)
    if cutoff <= start:
        return 'outside_lead_window'
    if cutoff >= end:
        return 'entire_day_inside_lead_window'
    return 'partly_inside_lead_window'


def live_dynamic_offer(course, now):
    """A feed-wide maximum lease cannot prove an individual appointment is live."""
    if course.get("offerType") != "dynamic_appointment":
        return False
    raw = course.get("validUntil")
    if not isinstance(raw, str):
        return False
    try:
        expiry = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return expiry.tzinfo is not None and expiry > now
    except (ValueError, OverflowError):
        return False


def summarize(payload, day, now=None):
    rows = [(d['date'], t['startTime'], c) for d in payload.get('dates', [])
            for t in d.get('startTimes', []) for c in t.get('courses', [])]
    raw_failures = payload.get('reconciliationIssues', [])
    diagnostics_safe = public_diagnostics_safe(raw_failures)
    failures = (raw_failures if isinstance(raw_failures, list) else [None])
    # Preserve the count and failure signal even for a malformed issue row.
    failures = [i if isinstance(i, dict) else {} for i in failures]
    now = now or datetime.now(timezone.utc)
    # Use the policy that the public feed actually carries. A missing or invalid
    # lead is UNKNOWN, not a license to treat an empty day as healthy or blocked.
    raw_lead = payload.get('minimumLeadHours')
    lead_hours = (raw_lead if isinstance(raw_lead, (int, float)) and
                  not isinstance(raw_lead, bool) and 0 <= raw_lead <= 24 * 365 else None)
    lead_cutoff = now + timedelta(hours=lead_hours) if lead_hours is not None else None
    shipyard_alias_safe, shipyard_offers_checked = public_shipyard_alias_check(payload)
    # Public offers are date-scoped in Eastern local time. Do not infer an open
    # instructor day from an empty public date, nor conflate partial coverage
    # failures with an expired dynamic-feed lease.
    next_days = [(datetime.fromisoformat(day).date() + timedelta(days=n)).isoformat()
                 for n in range(3)]
    next_three_days = {
        date: {
            'publishedOffers': sum(d == date for d, _, _ in rows),
            'publishedTimes': sorted({t for d, t, _ in rows if d == date}),
            'perCourse': dict(Counter(str(c['courseId']) for d, _, c in rows if d == date)),
            'failedWindows': sum(str(i.get('start', '')).startswith(date) for i in failures),
            'failedWindowReasons': dict(Counter(
                safe_issue_reason(i) for i in failures
                if str(i.get('start', '')).startswith(date))),
        }
        for date in next_days
    }
    for next_date, detail in next_three_days.items():
        detail['leadWindowStatus'] = lead_window_status(next_date, lead_cutoff)
    # A healthy lead cutoff and a global failed-window alert can coexist.
    # Preserve the global fail-closed gate while attributing which date is affected.
    day_failed_windows = sum(str(i.get('start', '')).startswith(day) for i in failures)
    global_coverage_alert = bool((payload.get('counts') or {}).get('failed_windows'))
    coverage_alert_scope = ('includes_observed_day' if day_failed_windows else
                            'other_or_unscoped_windows' if global_coverage_alert else 'none')
    try:
        expiry = datetime.fromisoformat(str(payload.get('validUntil', '')).replace('Z', '+00:00'))
        expired = expiry.tzinfo is None or expiry <= now
    except ValueError:
        expired = True
    dynamic_rows = [r for r in rows if r[2].get('offerType') != 'seated_class']
    live_rows = [r for r in dynamic_rows if not expired and live_dynamic_offer(r[2], now)]
    for date, detail in next_three_days.items():
        detail['liveDynamicOffers'] = sum(r[0] == date for r in live_rows)
        detail['expiredOrMalformedDynamicOffers'] = (
            sum(r[0] == date for r in dynamic_rows) - detail['liveDynamicOffers'])
    return {
        'generatedAt': payload.get('generatedAt'), 'validUntil': payload.get('validUntil'),
        'publicPage': payload.get('publicPage'), 'counts': payload.get('counts'),
        'actualOffers': len(rows), 'actualDates': len({d for d, _, _ in rows}),
        'dynamicOffers': len(dynamic_rows),
        'liveDynamicOffers': len(live_rows),
        'expiredOrMalformedDynamicOffers': len(dynamic_rows) - len(live_rows),
        'seatedOffers': sum(c.get('offerType') == 'seated_class' for _, _, c in rows),
        'publicationExpired': expired,
        'perCourse': dict(Counter(str(c['courseId']) for _, _, c in rows)),
        'minimumLeadHours': lead_hours,
        'leadCutoffAtEastern': (lead_cutoff.astimezone(ZoneInfo('America/New_York')).isoformat()
                                if lead_cutoff is not None else None),
        'dayLeadWindowStatus': lead_window_status(day, lead_cutoff),
        'day': day, 'dayOffers': len([r for r in rows if r[0] == day]),
        'dayTimes': sorted({t for d, t, _ in rows if d == day}),
        'dayPerCourse': dict(Counter(str(c['courseId']) for d, _, c in rows if d == day)),
        'nextThreeDays': next_three_days,
        'failedWindowReasons': dict(Counter(safe_issue_reason(i) for i in failures)),
        'dayFailedWindows': day_failed_windows,
        'dayCoverageAlert': bool(day_failed_windows),
        'coverageAlert': global_coverage_alert,
        'coverageAlertScope': coverage_alert_scope,
        'publicDiagnosticsSafe': diagnostics_safe,
        'publicShipyardAliasSafe': shipyard_alias_safe,
        'shipyardOffersChecked': shipyard_offers_checked,
    }


def continuity_incident(feeds):
    """Remaining seated classes do not downgrade lost appointment availability."""
    failures = []
    for family, feed in feeds.items():
        if family in ('bls', 'heartsaver') and feed['dynamicOffers'] == 0:
            failures.append(dict(family=family, reason='missing_dynamic_appointments'))
        elif feed['dynamicOffers'] > 0 and feed['publicationExpired']:
            failures.append(dict(family=family, reason='expired_dynamic_appointments'))
        elif feed['expiredOrMalformedDynamicOffers']:
            failures.append(dict(family=family, reason='invalid_individual_appointment_leases'))
    return dict(priority='P0', status='active_booking_outage', failures=failures,
        recovery_owner='Codex',
        next_action='Begin immediate source/lease/publication recovery; refresh or restore a validated release, '
                    'preserve occupancy and safety rules, then verify rendered appointment choices and booking links.') if failures else None


def parse_arguments(argv=None, now=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--continuity', action='store_true',
        help='Alert for expired dynamic inventory or absent BLS/Heartsaver appointments; never retire seated classes')
    parser.add_argument('--day', help='Diagnostic date; defaults to today in America/New_York')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.day is None:
        args.day = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo('America/New_York')).date().isoformat()
    return args


def main():
    observed = datetime.now(timezone.utc)
    args = parse_arguments(now=observed)
    stamp = observed.isoformat()
    def read(family):
        path = f'data/block-selector-availability/{family}.json'
        raw = ((urlopen(f'https://www.910cpr.com/{path}?coverage={stamp}', timeout=30).read())
               if args.live else (ROOT / 'docs' / path).read_bytes())
        return family, dict(summarize(json.loads(raw), args.day, observed), sha256=hashlib.sha256(raw).hexdigest())
    with ThreadPoolExecutor(max_workers=4) as pool:
        feeds = dict(pool.map(read, FAMILIES))
    incident = continuity_incident(feeds) if args.continuity else None
    path = 'data/admin/scheduling_landscape.json'
    raw = (urlopen(f'https://www.910cpr.com/{path}?coverage={stamp}', timeout=30).read()
           if args.live else (ROOT / 'docs' / path).read_bytes())
    landscape = json.loads(raw)
    report = dict(observedAt=stamp, mode='live-read-only' if args.live else 'local-pinned', families=feeds,
        incident=incident,
        landscape=dict(buildId=landscape.get('buildId'), builtAt=landscape.get('builtAt'),
            publicDiagnosticsSafe=public_landscape_diagnostics_safe(landscape),
            sha256=hashlib.sha256(raw).hexdigest(),
            dayCellResults=dict(Counter(c['result'] for c in landscape['cells'] if c['date'] == args.day)),
            sourcePages={k: dict(generatedAt=v.get('generatedAt'), counts=v.get('counts'),
                rejectionReasonCounts=v.get('rejectionReasonCounts')) for k,v in landscape['sourcePages'].items()}),
        limitations=['Sequential HTTP reads may straddle publication; timestamps and hashes retained.',
            'Failed windows are not candidate rejections; nonzero failed_windows is an explicit coverage alert.',
            'Published offer counts do not prove a qualified instructor was available or a booking URL works.',
            'Counts do not prove legal free-window coverage, browser rendering, or recurring health.'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: dict(
        {f: v[f] for f in ('actualOffers','actualDates','liveDynamicOffers','expiredOrMalformedDynamicOffers','dayOffers','dayTimes','dayFailedWindows','dayCoverageAlert','coverageAlert','coverageAlertScope','publicDiagnosticsSafe', 'publicShipyardAliasSafe', 'shipyardOffersChecked', 'minimumLeadHours', 'leadCutoffAtEastern', 'dayLeadWindowStatus')},
        nextThreeDayOffers={day: item['publishedOffers'] for day, item in v['nextThreeDays'].items()})
        for k,v in feeds.items()}, indent=2))
    if incident:
        print('::error title=P0 public booking outage::' +
              ', '.join(f"{f['family']}: {f['reason']}" for f in incident['failures']) +
              '. Immediate recovery required; remaining seated classes do not resolve this failure.')
    unresolved_coverage = [
        f"{family}: {feed['coverageAlertScope']} (observed-day failures={feed['dayFailedWindows']})"
        for family, feed in feeds.items() if feed['coverageAlert']
    ]
    if unresolved_coverage:
        print('::error title=Unresolved scheduling coverage windows::' +
              '; '.join(unresolved_coverage) +
              '. The global safety gate remains red even when same-day zero offers are explained by lead time.')
    unsafe_families = [family for family, feed in feeds.items() if not feed['publicDiagnosticsSafe']]
    if unsafe_families:
        print('::error title=Public selector diagnostic privacy gate::' +
              ', '.join(unsafe_families) +
              ' returned sensitive or unapproved issue structure; inspect restricted evidence and regenerate sanitized publication.')
    # This independent live-host gate is specific to the recently repaired
    # ACLS/PALS Shipyard public DTO. Zero matching offers means no alias proof,
    # not a green claim about hosted registration or a fabricated class.
    unsafe_shipyard = [family for family in ('acls', 'pals')
                       if not feeds[family]['publicShipyardAliasSafe']]
    if unsafe_shipyard:
        print('::error title=Public Shipyard location alias regression::' +
              ', '.join(unsafe_shipyard) +
              ' exposed a non-approved Shipyard location. Inspect hosted offers; preserve the internal resource only server-side.')
    landscape_safe = public_landscape_diagnostics_safe(landscape)
    if not landscape_safe:
        print('::error title=Public scheduling landscape privacy gate::'
              ' Public diagnostic contains restricted structure; repair publication and verify actual host.')
    return int(any(v['coverageAlert'] for v in feeds.values()) or bool(incident)
               or bool(unsafe_families) or bool(unsafe_shipyard) or not landscape_safe)


if __name__ == '__main__':
    raise SystemExit(main())
