"""Read-only coverage checkpoint. Never infer free space from blank graph cells.

No generators, credentials, booking requests or source mutations. Public feeds
carry window-level failures separately from candidate rejection counts.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ('bls', 'heartsaver', 'acls', 'pals', 'arc', 'hsi', 'uscg_first_aid_cpr_aed', 'family_cpr')


WINDOW_DIAGNOSTIC_LIMIT = 50


def window_diagnostics(issues, family=None):
    """Allowlisted issue context only; issues are not necessarily failed windows."""
    records, seen = [], set()
    for issue in issues:
        row = {'family': family if family in FAMILIES else None,
               'reason': 'unclassified_reconciliation_issue'}
        for field in ('start', 'end'):
            try:
                value = datetime.fromisoformat(str(issue.get(field, '')).replace('Z', '+00:00'))
                if value.tzinfo is not None:
                    row[field] = value.isoformat()
                    if field == 'start':
                        row['date'] = value.astimezone(ZoneInfo('America/New_York')).date().isoformat()
            except (ValueError, TypeError, OverflowError):
                pass  # Missing/invalid bounds stay absent, never inferred.
        reason = issue.get('reason')
        prefix = 'missing directional travel rule: '
        if isinstance(reason, str) and reason.startswith(prefix):
            locations = reason[len(prefix):].split('->')
            if len(locations) == 2 and all(0 < len(v) <= 200 and all(c.isprintable() for c in v) for v in locations):
                row.update(reason='missing_directional_travel_rule', fromLocation=locations[0], toLocation=locations[1])
        elif reason == 'unresolved_occupied_bounds':
            row['reason'] = reason
        key = json.dumps(row, sort_keys=True)
        if key not in seen:
            seen.add(key)
            if len(records) < WINDOW_DIAGNOSTIC_LIMIT:
                records.append(row)
    return {'records': records, 'limit': WINDOW_DIAGNOSTIC_LIMIT,
            'uniqueIssueContexts': len(seen), 'truncated': len(seen) > len(records),
            'dateTimezone': 'America/New_York'}


def summarize(payload, day, now=None, family=None):
    rows = [(d['date'], t['startTime'], c) for d in payload.get('dates', [])
            for t in d.get('startTimes', []) for c in t.get('courses', [])]
    failures = payload.get('reconciliationIssues', [])
    now = now or datetime.now(timezone.utc)
    try:
        expiry = datetime.fromisoformat(str(payload.get('validUntil', '')).replace('Z', '+00:00'))
        expired = expiry.tzinfo is None or expiry <= now
    except ValueError:
        expired = True
    return {
        'generatedAt': payload.get('generatedAt'), 'validUntil': payload.get('validUntil'),
        'publicPage': payload.get('publicPage'), 'counts': payload.get('counts'),
        'actualOffers': len(rows), 'actualDates': len({d for d, _, _ in rows}),
        'dynamicOffers': sum(c.get('offerType') != 'seated_class' for _, _, c in rows),
        'seatedOffers': sum(c.get('offerType') == 'seated_class' for _, _, c in rows),
        'publicationExpired': expired,
        'perCourse': dict(Counter(str(c['courseId']) for _, _, c in rows)),
        'day': day, 'dayOffers': len([r for r in rows if r[0] == day]),
        'dayTimes': sorted({t for d, t, _ in rows if d == day}),
        'dayPerCourse': dict(Counter(str(c['courseId']) for d, _, c in rows if d == day)),
        'failedWindowReasons': dict(Counter(i.get('reason', 'unknown') for i in failures)),
        'reconciliationWindowDiagnostics': window_diagnostics(failures, family),
        'dayFailedWindows': sum(str(i.get('start', '')).startswith(day) for i in failures),
        'coverageAlert': bool((payload.get('counts') or {}).get('failed_windows')),
    }


def continuity_incident(feeds):
    """Remaining seated classes do not downgrade lost appointment availability."""
    failures = []
    for family, feed in feeds.items():
        if family in ('bls', 'heartsaver') and feed['dynamicOffers'] == 0:
            failures.append(dict(family=family, reason='missing_dynamic_appointments'))
        elif feed['dynamicOffers'] > 0 and feed['publicationExpired']:
            failures.append(dict(family=family, reason='expired_dynamic_appointments'))
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
        return family, dict(summarize(json.loads(raw), args.day, family=family), sha256=hashlib.sha256(raw).hexdigest())
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
            sha256=hashlib.sha256(raw).hexdigest(),
            dayCellResults=dict(Counter(c['result'] for c in landscape['cells'] if c['date'] == args.day)),
            sourcePages={k: dict(generatedAt=v.get('generatedAt'), counts=v.get('counts'),
                rejectionReasonCounts=v.get('rejectionReasonCounts')) for k,v in landscape['sourcePages'].items()}),
        limitations=['Sequential HTTP reads may straddle publication; timestamps and hashes retained.',
            'Failed windows are not candidate rejections; nonzero failed_windows is an explicit coverage alert.',
            'Counts do not prove legal free-window coverage, browser rendering, or recurring health.'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:{f:v[f] for f in ('actualOffers','actualDates','dayOffers','dayTimes','dayFailedWindows','coverageAlert')}
        for k,v in feeds.items()}, indent=2))
    if incident:
        print('::error title=P0 public booking outage::' +
              ', '.join(f"{f['family']}: {f['reason']}" for f in incident['failures']) +
              '. Immediate recovery required; remaining seated classes do not resolve this failure.')
    return int(any(v['coverageAlert'] for v in feeds.values()) or bool(incident))


if __name__ == '__main__':
    raise SystemExit(main())
