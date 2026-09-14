"""Local, aggregate-only checkpoints for the #229 owner monitor (no publication)."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

RECOVERY = 'data/audit/issue229_source_recovery_r1.json'
IDENTITY = 'data/audit/issue229_identity_reconciliation_r2.json'
OUTPUT = 'data/audit/issue229_archive_rebuild_status.json'
PHASES = ('SOURCE_RECOVERY', 'IDENTITY_RECONCILIATION', 'ELIGIBILITY_REVIEW',
          'GENERATION', 'VALIDATION', 'SITEMAP', 'DEPLOY', 'GOOGLE_DISCOVERY')
STATES = ('RUNNING', 'BLOCKED', 'CHECKPOINT_COMPLETE')
BLOCKERS = ('ELIGIBILITY_REVIEW', 'CURRENT_INVENTORY_GATE', 'VALIDATION_FAILED',
            'SOURCE_UNAVAILABLE', 'OPERATOR_REVIEW')
COUNTERS = ('eligible_pages', 'pages_generated', 'pages_validated',
            'pages_failed_validation', 'sitemap_urls_generated', 'pages_published')
EVIDENCE_KEYS = ('eligibility', 'validation', 'deployment', 'gsc')
GSC_COUNTS = ('discovered', 'indexed', 'class_impressions', 'class_clicks')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def timestamp(value):
    require(isinstance(value, str), 'Timestamp must be an ISO string')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.utcoffset() is not None, 'Timestamp requires an offset')
    return parsed


def count(value, nullable=False):
    require((nullable and value is None) or (type(value) is int and 0 <= value <= 2**53-1),
            'Counts must be nonnegative safe integers; unknown is null')
    return value


def exact_keys(value, expected):
    require(isinstance(value, dict) and set(value) == set(expected), 'Unexpected or missing fields')


def evidence(ref):
    exact_keys(ref, ('commit', 'path'))
    require(isinstance(ref['commit'], str) and re.fullmatch(r'[0-9a-f]{40}', ref['commit']),
            'Evidence requires an immutable commit')
    require(isinstance(ref['path'], str) and re.fullmatch(r'data/audit/[a-zA-Z0-9_-]+\.(?:json|md)', ref['path']),
            'Evidence must reference an aggregate audit artifact')


def validate_counters(metrics, refs):
    exact_keys(metrics, COUNTERS)
    for name, value in metrics.items():
        count(value, nullable=name == 'eligible_pages')
    eligible = metrics['eligible_pages']
    generated = metrics['pages_generated']
    require(eligible is None or refs['eligibility'] is not None, 'Eligibility requires reviewed evidence')
    require(not generated or eligible is not None, 'Generation cannot precede eligibility')
    require(eligible is None or generated <= eligible, 'Generated exceeds full eligible corpus')
    require(metrics['pages_validated'] + metrics['pages_failed_validation'] <= generated,
            'Validation partition exceeds generated pages')
    require(metrics['sitemap_urls_generated'] <= metrics['pages_validated'], 'Sitemap exceeds validated pages')
    require(metrics['pages_published'] <= metrics['pages_validated'], 'Published exceeds validated pages')
    require(not metrics['pages_validated'] or refs['validation'] is not None, 'Validation requires evidence')
    require(not metrics['pages_published'] or refs['deployment'] is not None, 'Publication requires deployment evidence')


def validate(status):
    exact_keys(status, ('schema_version', 'issue', 'run_id', 'revision', 'phase', 'state', 'blockers',
                       'last_checkpoint_at', 'expected_checkpoint_seconds', 'producer_mode', 'provenance',
                       'baseline', 'metrics', 'evidence', 'gsc', 'events'))
    require(status['schema_version'] == 1 and status['issue'] == 229, 'Unsupported status contract')
    require(re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}', status['run_id']) is not None, 'Invalid run ID')
    count(status['revision'])
    require(status['phase'] in PHASES and status['state'] in STATES, 'Invalid phase/state')
    require(isinstance(status['blockers'], list) and all(b in BLOCKERS for b in status['blockers']), 'Invalid blocker')
    require(bool(status['blockers']) == (status['state'] == 'BLOCKED'), 'Blocked state requires explicit blocker codes')
    timestamp(status['last_checkpoint_at'])
    require(status['expected_checkpoint_seconds'] == 300 and status['producer_mode'] == 'local_checkpoints',
            'Unsupported heartbeat contract')
    p = status['provenance']
    exact_keys(p, ('repository', 'branch', 'commit', 'pr', 'sources'))
    require(p['repository'] == 'Brian910cpr/910cpr-class-landers', 'Wrong repository')
    require(isinstance(p['branch'], str) and re.fullmatch(r'codex/[a-zA-Z0-9/_-]{1,120}', p['branch']), 'Invalid branch')
    require(isinstance(p['commit'], str) and re.fullmatch(r'[0-9a-f]{40}', p['commit']), 'Invalid code commit')
    if p['pr'] is not None:
        require(type(p['pr']) is int and p['pr'] > 0, 'Invalid PR number')
    require(isinstance(p['sources'], list) and len(p['sources']) == 2, 'Two source audit references required')
    for ref in p['sources']:
        evidence(ref)
    b = status['baseline']
    exact_keys(b, ('source_rows_recovered', 'html_urls_recovered', 'preliminary_candidates',
                   'non_candidate_rows', 'excluded_private_ambiguous_rows', 'not_elapsed_rows',
                   'classification', 'identity_rows_reconciled', 'orphan_html_unresolved'))
    for key in set(b) - {'classification'}:
        count(b[key])
    exact_keys(b['classification'], ('client_present_review', 'invalid_or_ambiguous_timing',
                                   'non_public_location_review', 'not_elapsed_at_cutoff',
                                   'preliminary_public_candidate_requires_review', 'workbook_provenance_unresolved'))
    for value in b['classification'].values():
        count(value)
    require(sum(b['classification'].values()) == b['source_rows_recovered'], 'Source classification does not reconcile')
    require(b['preliminary_candidates'] == b['classification']['preliminary_public_candidate_requires_review'], 'Candidate mismatch')
    require(b['not_elapsed_rows'] == b['classification']['not_elapsed_at_cutoff'], 'Not-elapsed mismatch')
    require(b['non_candidate_rows'] == b['source_rows_recovered'] - b['preliminary_candidates'], 'Non-candidate mismatch')
    require(b['excluded_private_ambiguous_rows'] == b['non_candidate_rows'] - b['not_elapsed_rows'], 'Review partition mismatch')
    require(b['identity_rows_reconciled'] == b['source_rows_recovered'], 'Identity source mismatch')
    exact_keys(status['evidence'], EVIDENCE_KEYS)
    for ref in status['evidence'].values():
        if ref is not None:
            evidence(ref)
    validate_counters(status['metrics'], status['evidence'])
    require(status['metrics']['eligible_pages'] is None or status['metrics']['eligible_pages'] <= b['source_rows_recovered'],
            'Eligibility exceeds recovered source corpus')
    if PHASES.index(status['phase']) >= PHASES.index('GENERATION'):
        require(status['metrics']['eligible_pages'] is not None, 'Resolve eligibility before generation phases')
    gsc = status['gsc']
    exact_keys(gsc, (*GSC_COUNTS, 'observed_at', 'window_start', 'window_end'))
    for key in GSC_COUNTS:
        count(gsc[key], nullable=True)
    if any(gsc[key] is not None for key in GSC_COUNTS):
        require(status['evidence']['gsc'] is not None, 'Google metrics require evidence')
        require(timestamp(gsc['window_start']) <= timestamp(gsc['window_end']) <= timestamp(gsc['observed_at']),
                'Invalid Google measurement window')
    else:
        require(all(gsc[key] is None for key in ('observed_at', 'window_start', 'window_end')), 'Unknown Google metrics have no observation')
    if gsc['observed_at'] is not None:
        require(timestamp(gsc['observed_at']) <= timestamp(status['last_checkpoint_at']), 'Google observation is in the future')
    require(isinstance(status['events'], list) and 1 <= len(status['events']) <= 100, 'Invalid event rail')
    previous = timestamp(status['last_checkpoint_at'])
    for event in status['events']:
        exact_keys(event, ('phase', 'state', 'at', 'revision', 'metrics'))
        require(event['phase'] in PHASES and event['state'] in STATES, 'Invalid event phase/state')
        count(event['revision'])
        require(event['revision'] <= status['revision'], 'Event revision exceeds current revision')
        at = timestamp(event['at'])
        require(at <= previous, 'Event rail must be newest first')
        previous = at
        validate_counters(event['metrics'], status['evidence'])
    require(status['events'][0] == event_for(status), 'Latest event must match current checkpoint')
    return status


def event_for(status):
    return {key: deepcopy(status[key]) for key in ('phase', 'state', 'revision', 'metrics')} | {'at': status['last_checkpoint_at']}


def initial(recovery, identity, provenance, at, run_id):
    require(recovery['publication_authorized_count'] is None and identity['publication_authorized_count'] is None,
            'Initial feed is for the unapproved recovery baseline')
    source = recovery['sources']['historical_corpus']
    categories = deepcopy(source['exclusive_classification'])
    total, preliminary = source['source_rows'], categories['preliminary_public_candidate_requires_review']
    require(sum(identity['exclusive_historical_dispositions'].values()) == total, 'Identity partition does not reconcile')
    status = {
        'schema_version': 1, 'issue': 229, 'run_id': run_id, 'revision': 0,
        'phase': 'ELIGIBILITY_REVIEW', 'state': 'BLOCKED',
        'blockers': ['ELIGIBILITY_REVIEW', 'CURRENT_INVENTORY_GATE'],
        'last_checkpoint_at': at, 'expected_checkpoint_seconds': 300, 'producer_mode': 'local_checkpoints',
        'provenance': deepcopy(provenance),
        'baseline': {'source_rows_recovered': total, 'html_urls_recovered': source['urls']['legacy_numeric_html_count'],
                     'preliminary_candidates': preliminary, 'non_candidate_rows': total - preliminary,
                     'excluded_private_ambiguous_rows': total - preliminary - categories['not_elapsed_at_cutoff'],
                     'not_elapsed_rows': categories['not_elapsed_at_cutoff'], 'classification': categories,
                     'identity_rows_reconciled': identity['historical_rows'], 'orphan_html_unresolved': identity['orphan_html_count']},
        'metrics': {key: None if key == 'eligible_pages' else 0 for key in COUNTERS},
        'evidence': dict.fromkeys(EVIDENCE_KEYS),
        'gsc': dict.fromkeys((*GSC_COUNTS, 'observed_at', 'window_start', 'window_end')), 'events': [],
    }
    status['events'] = [event_for(status)]
    # Imported evidence is a checkpoint observation now, not an invented historical heartbeat.
    for phase in ('IDENTITY_RECONCILIATION', 'SOURCE_RECOVERY'):
        status['events'].append(event_for(status) | {'phase': phase, 'state': 'CHECKPOINT_COMPLETE'})
    return validate(status)


def advance(status, update, at):
    validate(status)
    exact_keys(update, ('expected_revision', 'phase', 'state', 'blockers', 'metrics', 'evidence', 'gsc'))
    require(type(update['expected_revision']) is int and update['expected_revision'] == status['revision'], 'Checkpoint revision conflict')
    require(timestamp(at) >= timestamp(status['last_checkpoint_at']), 'Checkpoint time cannot regress')
    require(update['phase'] in PHASES and PHASES.index(update['phase']) >= PHASES.index(status['phase']), 'Phase cannot regress within a run')
    result = deepcopy(status)
    for key in ('phase', 'state', 'blockers', 'metrics', 'evidence', 'gsc'):
        result[key] = deepcopy(update[key])
    exact_keys(result['metrics'], COUNTERS)
    for key, prior in status['metrics'].items():
        current = result['metrics'][key]
        count(current, nullable=key == 'eligible_pages')
        require(prior is None or current is not None and current >= prior, 'Counts cannot regress within a run; create a new run for changed corpus')
        if key == 'eligible_pages' and prior is not None:
            require(current == prior, 'Changed eligibility requires a new run')
    for key, ref in status['evidence'].items():
        require(ref is None or result['evidence'].get(key) == ref, 'Evidence replacement requires a new run')
    result['revision'] += 1
    result['last_checkpoint_at'] = at
    result['events'] = [event_for(result), *result['events']][:100]
    return validate(result)


def health(status, now):
    validate(status)
    age = (timestamp(now) - timestamp(status['last_checkpoint_at'])).total_seconds()
    if age < 0:
        return 'CLOCK_MISMATCH'
    if status['state'] == 'RUNNING' and age > status['expected_checkpoint_seconds']:
        return 'STALLED'
    return status['state']


@contextmanager
def writer_lock(output):
    lock = output.with_name(output.name + '.lock')
    with lock.open('x', encoding='utf-8') as handle:
        handle.write(str(os.getpid()))
    try:
        yield
    finally:
        lock.unlink()


def write_atomic(output, status):
    validate(status)
    payload = (json.dumps(status, indent=2, sort_keys=True) + '\n').encode('utf-8')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix=output.name + '.', suffix='.tmp', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def git(*args):
    return subprocess.check_output(['git', *args])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('init', 'checkpoint', 'check'))
    parser.add_argument('--output', type=Path, default=Path(OUTPUT))
    parser.add_argument('--source-ref', default='HEAD')
    parser.add_argument('--run-id')
    parser.add_argument('--pr', type=int)
    parser.add_argument('--update', type=Path)
    parser.add_argument('--at', help='Explicit clock for reproducible local checks; defaults to current UTC')
    args = parser.parse_args()
    at = args.at or datetime.now(timezone.utc).isoformat()
    root = Path(git('rev-parse', '--show-toplevel').decode().strip()).resolve()
    output = args.output.resolve()
    require(output.is_relative_to(root / 'data' / 'audit'), 'Operational feed must stay under repository data/audit, never docs/')
    if args.mode == 'check':
        status = json.loads(output.read_text(encoding='utf-8'))
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        with writer_lock(output):
            if args.mode == 'init':
                require(not output.exists(), 'Existing status must not be overwritten; use a distinct run/output')
                require(args.run_id is not None, '--run-id is required')
                ref = git('rev-parse', '--verify', args.source_ref + '^{commit}').decode().strip()
                sources = [json.loads(git('show', f'{ref}:{path}')) for path in (RECOVERY, IDENTITY)]
                provenance = {'repository': 'Brian910cpr/910cpr-class-landers',
                              'branch': git('branch', '--show-current').decode().strip(),
                              'commit': git('rev-parse', 'HEAD').decode().strip(), 'pr': args.pr,
                              'sources': [{'commit': ref, 'path': path} for path in (RECOVERY, IDENTITY)]}
                status = initial(*sources, provenance, at, args.run_id)
            else:
                require(args.update is not None, '--update is required')
                status = advance(json.loads(output.read_text(encoding='utf-8')),
                                 json.loads(args.update.read_text(encoding='utf-8')), at)
            for ref in [*status['provenance']['sources'], *status['evidence'].values()]:
                if ref is not None:
                    git('cat-file', '-e', f"{ref['commit']}:{ref['path']}")
            write_atomic(output, status)
    print(json.dumps({'issue': 229, 'run_id': status['run_id'], 'revision': status['revision'],
                      'health': health(status, at), 'phase': status['phase']}))


if __name__ == '__main__':
    main()
