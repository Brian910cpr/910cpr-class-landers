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
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ('bls', 'heartsaver', 'acls', 'pals', 'arc', 'hsi', 'uscg_first_aid_cpr_aed', 'family_cpr')


def summarize(payload, day):
    rows = [(d['date'], t['startTime'], c) for d in payload.get('dates', [])
            for t in d.get('startTimes', []) for c in t.get('courses', [])]
    failures = payload.get('reconciliationIssues', [])
    return {
        'generatedAt': payload.get('generatedAt'), 'validUntil': payload.get('validUntil'),
        'publicPage': payload.get('publicPage'), 'counts': payload.get('counts'),
        'actualOffers': len(rows), 'actualDates': len({d for d, _, _ in rows}),
        'perCourse': dict(Counter(str(c['courseId']) for _, _, c in rows)),
        'day': day, 'dayOffers': len([r for r in rows if r[0] == day]),
        'dayTimes': sorted({t for d, t, _ in rows if d == day}),
        'dayPerCourse': dict(Counter(str(c['courseId']) for d, _, c in rows if d == day)),
        'failedWindowReasons': dict(Counter(i.get('reason', 'unknown') for i in failures)),
        'dayFailedWindows': sum(str(i.get('start', '')).startswith(day) for i in failures),
        'coverageAlert': bool((payload.get('counts') or {}).get('failed_windows')),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--day', default='2026-10-14')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).isoformat()
    def read(family):
        path = f'data/block-selector-availability/{family}.json'
        raw = ((urlopen(f'https://www.910cpr.com/{path}?coverage={stamp}', timeout=30).read())
               if args.live else (ROOT / 'docs' / path).read_bytes())
        return family, dict(summarize(json.loads(raw), args.day), sha256=hashlib.sha256(raw).hexdigest())
    with ThreadPoolExecutor(max_workers=4) as pool:
        feeds = dict(pool.map(read, FAMILIES))
    path = 'data/admin/scheduling_landscape.json'
    raw = (urlopen(f'https://www.910cpr.com/{path}?coverage={stamp}', timeout=30).read()
           if args.live else (ROOT / 'docs' / path).read_bytes())
    landscape = json.loads(raw)
    report = dict(observedAt=stamp, mode='live-read-only' if args.live else 'local-pinned', families=feeds,
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
    return int(any(v['coverageAlert'] for v in feeds.values()))


if __name__ == '__main__':
    raise SystemExit(main())
