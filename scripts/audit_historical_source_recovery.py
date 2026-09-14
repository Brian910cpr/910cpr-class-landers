"""Read immutable Git sources for #229; emit aggregates, never source records.

This is a recovery audit, not publication eligibility or a schedule generator.
The existing public-location rule is reused; all candidate counts still need
current identity, cancellation/completion and public-content review.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

try:
    from scripts.public_class_eligibility import is_public_class_location
except ModuleNotFoundError:
    from public_class_eligibility import is_public_class_location

ROOT = Path(__file__).resolve().parents[1]
EASTERN = ZoneInfo('America/New_York')
PATTERN = 'f523c364ccbb29fffdf96fec1b4a915421f682bd'
REMOVAL = 'a7ff508d070ee7c23db0c955c04f05d03c4ef576'
SEO_CORE = 'd02a7a6fe7a398112cf71595e62fa3cc1d351745'
SEO_FINAL = '269e9fd7015128fd7652d57864623da1aaa2fd4a'


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def blob(ref: str, path: str) -> bytes:
    return git('show', f'{ref}:{path}')


def parse_date(value):
    if isinstance(value, datetime):
        result = value
    else:
        try:
            result = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        except ValueError:
            return None
    if result.tzinfo is not None:
        return result.astimezone(EASTERN)
    # An absent timezone is interpreted as Enrollware local wall time. Refuse
    # ambiguous/nonexistent DST times instead of choosing an undocumented fold.
    first, second = result.replace(tzinfo=EASTERN, fold=0), result.replace(tzinfo=EASTERN, fold=1)
    if first.utcoffset() != second.utcoffset():
        return None
    if first.astimezone(timezone.utc).astimezone(EASTERN).replace(tzinfo=None) != result:
        return None
    return first


def registration_id(value):
    try:
        url = urlparse(str(value))
        hostname = (url.hostname or '').lower()
        values = parse_qs(url.query).get('id', [])
        if (url.scheme in {'https', 'http'} and hostname.endswith('.enrollware.com')
                and url.path.rstrip('/') == '/enroll' and len(values) == 1
                and re.fullmatch(r'[0-9]+', values[0])):
            return values[0]
    except ValueError:
        pass
    return None


def normalized(row):
    return {
        'id': str(row.get('session_id') or ''),
        'course': str(row.get('course', row.get('course_name', '')) or ''),
        'start': parse_date(row.get('start', row.get('start_at'))),
        'end': parse_date(row.get('end', row.get('end_at'))),
        'location': str(row.get('location', row.get('location_name', row.get('location_display', ''))) or ''),
        'client': str(row.get('client') or '').strip(),
        'external_id': registration_id(row.get('register_url', row.get('registration_url'))),
        'students': row.get('students', row.get('enrolled_count')),
    }


def family_label(value):
    # A coarse audit bucket, not an authoritative Course Master mapping.
    for label, pattern in [('PALS', r'\bpals\b'), ('ACLS', r'\bacls\b'),
                           ('BLS', r'\bbls\b'), ('Heartsaver', r'heart\s*saver'),
                           ('USCG', r'\buscg\b'), ('First Aid', r'first\s+aid'),
                           ('CPR', r'\bcpr\b')]:
        if re.search(pattern, value, re.I):
            return label
    return 'Unclassified'


def workbook_rows(ref, path):
    import openpyxl  # Existing repository dependency; extraction only.
    book = openpyxl.load_workbook(io.BytesIO(blob(ref, path)), read_only=True, data_only=True)
    try:
        rows = book.active.iter_rows(values_only=True)
        headers = next(rows)
        mapped = defaultdict(list)
        for values in rows:
            row = dict(zip(headers, values))
            record = normalized({
                'session_id': row.get('ID'), 'course': row.get('Course'),
                'start': row.get('Start Date / Time'), 'end': row.get('End Date / Time'),
                'location': row.get('Location'), 'client': row.get('Client'),
                'register_url': row.get('Registration Link'), 'students': row.get('Students'),
            })
            mapped[record['id']].append(record)
        return mapped
    finally:
        book.close()


def exclusion(record, as_of, duplicate=False, external_conflict=False, provenance='matched'):
    if not re.fullmatch(r'[0-9]+', record['id']):
        return 'invalid_session_id'
    if duplicate or external_conflict:
        return 'duplicate_or_conflicting_identity'
    if not record['start'] or not record['end'] or record['end'] <= record['start']:
        return 'invalid_or_ambiguous_timing'
    if record['end'] >= as_of:
        return 'not_elapsed_at_cutoff'
    if provenance != 'matched':
        return 'workbook_provenance_unresolved'
    if record['client']:
        return 'client_present_review'
    if not is_public_class_location(record['location']):
        return 'non_public_location_review'
    if not record['external_id']:
        return 'invalid_registration_identity'
    return 'preliminary_public_candidate_requires_review'


def summarize(rows, page_ids, current_page_ids, as_of, workbook=None):
    records = [normalized(row) for row in rows]
    id_counts = Counter(r['id'] for r in records)
    external_to_ids = defaultdict(set)
    for record in records:
        if record['external_id']:
            external_to_ids[record['external_id']].add(record['id'])
    reasons, flags, by_year, courses = Counter(), Counter(), {}, {}
    source_ids = {r['id'] for r in records if r['id'].isdigit()}
    for record in records:
        provenance = 'matched' if workbook is None else 'missing'
        if workbook is not None:
            matches = workbook.get(record['id'], [])
            if len(matches) == 1:
                source = matches[0]
                fields = ('course', 'start', 'end', 'location', 'external_id')
                provenance = 'matched' if all(record[k] == source[k] for k in fields) else 'mismatch'
                for field in fields:
                    flags['workbook_mismatch_' + field] += record[field] != source[field]
                # Preserve the source Client field which the old JSON dropped.
                record['client'] = source['client']
        flags['workbook_' + provenance if workbook is not None else 'json_only_provenance'] += 1
        flags['client_present'] += bool(record['client'])
        flags['public_location_marker'] += is_public_class_location(record['location'])
        flags['missing_registration_identity'] += record['external_id'] is None
        try:
            enrollment = float(record['students'])
            flags['positive_enrollment'] += enrollment > 0
            flags['zero_enrollment'] += enrollment == 0
            flags['negative_enrollment'] += enrollment < 0
        except (ValueError, TypeError):
            flags['unknown_enrollment'] += 1
        reason = exclusion(record, as_of, id_counts[record['id']] > 1,
                           len(external_to_ids.get(record['external_id'], set())) > 1, provenance)
        reasons[reason] += 1
        year = str(record['start'].year) if record['start'] else 'unknown'
        counter = by_year.setdefault(year, Counter())
        counter['source_rows'] += 1
        counter[reason] += 1
        # Raw course strings may embed a client or person. Emit a digest and
        # controlled family label only; exact labels remain in the source blob.
        digest = hashlib.sha256(record['course'].encode('utf-8')).hexdigest()
        course = courses.setdefault(digest, {'family_bucket': family_label(record['course']),
                                            'source_rows': 0, 'by_year': Counter(), 'reasons': Counter()})
        course['source_rows'] += 1
        course['by_year'][year] += 1
        course['reasons'][reason] += 1
    assert sum(reasons.values()) == len(rows)
    return {
        'source_rows': len(rows), 'unique_session_ids': len(source_ids),
        'unique_registration_ids': len(external_to_ids),
        'registration_ids_with_multiple_session_ids': sum(len(v) > 1 for v in external_to_ids.values()),
        'exclusive_classification': dict(sorted(reasons.items())), 'overlapping_flags': dict(sorted(flags.items())),
        'by_year': dict(sorted(by_year.items())), 'by_course_label_sha256': dict(sorted(courses.items())),
        'urls': {'legacy_numeric_html_count': len(page_ids), 'source_ids_with_legacy_html': len(source_ids & page_ids),
                 'legacy_html_without_source_id': len(page_ids - source_ids),
                 'source_ids_without_legacy_html': len(source_ids - page_ids),
                 'legacy_paths_in_current_tree': len(page_ids & current_page_ids),
                 'preservable_legacy_url_percent': round(100 * len(source_ids & page_ids) / len(page_ids), 4) if page_ids else None},
    }, records


def reconcile_identities(historical_rows, current_rows, orphan_html=None):
    """Compare source identities without approving an alias or publishing rows.

    Registration links bridge the short-report/long-registration ID namespaces.
    Matching a link does not prove identical class facts, completion or privacy.
    """
    historical = [normalized(row) for row in historical_rows]
    current = [normalized(row) for row in current_rows]
    old_ids = Counter(row['id'] for row in historical)
    new_ids = Counter(row['id'] for row in current)
    old_links, new_links = defaultdict(list), defaultdict(list)
    for records, index in ((historical, old_links), (current, new_links)):
        for record in records:
            if record['external_id']:
                index[record['external_id']].append(record)
    dispositions, changed_fields, statuses = Counter(), Counter(), Counter()
    pair_flags, difference_sets = Counter(), Counter()
    status_allowlist = {'past', 'future', 'scheduled', 'completed', 'cancelled', 'canceled', 'active'}
    for row in current_rows:
        status = str(row.get('session_status') or '').strip().lower()
        statuses[status if status in status_allowlist else 'missing' if not status else 'unrecognized'] += 1
    for record in historical:
        external = record['external_id']
        matches = new_links.get(external, [])
        if not re.fullmatch(r'[0-9]+', record['id']):
            reason = 'invalid_historical_session_id'
        elif not external:
            reason = 'invalid_historical_registration_identity'
        elif old_ids[record['id']] != 1 or len(old_links[external]) != 1:
            reason = 'ambiguous_historical_identity'
        elif not matches:
            reason = 'registration_identity_absent_from_current'
        elif len(matches) != 1 or new_ids[matches[0]['id']] != 1:
            reason = 'ambiguous_current_identity'
        elif not re.fullmatch(r'[0-9]+', matches[0]['id']):
            reason = 'invalid_current_session_id'
        else:
            match = matches[0]
            pair_flags['unique_registration_pairs'] += 1
            differences = [field for field in ('course', 'start', 'end', 'location')
                           if record[field] != match[field]]
            changed_fields.update(differences)
            difference_sets['+'.join(differences) or 'none'] += 1
            invalid = [not r['start'] or not r['end'] or r['end'] <= r['start'] for r in (record, match)]
            pair_flags['invalid_historical_timing'] += invalid[0]
            pair_flags['invalid_current_timing'] += invalid[1]
            pair_flags['start_or_end_differs'] += 'start' in differences or 'end' in differences
            if any(invalid):
                reason = 'shared_identity_invalid_timing'
            else:
                reason = 'shared_identity_facts_changed' if differences else 'shared_identity_facts_match'
        dispositions[reason] += 1

    class RegistrationLinks(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.ids = set()

        def handle_starttag(self, tag, attrs):
            if tag == 'a':
                for name, value in attrs:
                    if name == 'href':
                        external = registration_id(value)
                        if external:
                            self.ids.add(external)

    orphan_counts, orphan_details = Counter(), {}
    for path, content in sorted((orphan_html or {}).items()):
        parser = RegistrationLinks()
        parser.feed(content)
        parser.close()
        old_count = new_count = 0
        if not parser.ids:
            reason = 'no_registration_link'
        elif len(parser.ids) != 1:
            reason = 'multiple_registration_identities'
        else:
            external = next(iter(parser.ids))
            old_count, new_count = len(old_links.get(external, [])), len(new_links.get(external, []))
            if (old_count > 1 or new_count > 1
                    or (old_count == 1 and old_ids[old_links[external][0]['id']] != 1)
                    or (new_count == 1 and new_ids[new_links[external][0]['id']] != 1)):
                reason = 'ambiguous_source_registration_identity'
            elif old_count == 1:
                reason = 'historical_source_link_match_requires_alias_review'
            elif new_count == 1:
                reason = 'current_source_link_match_requires_historical_facts_review'
            else:
                reason = 'registration_identity_absent_from_both_sources'
        orphan_counts[reason] += 1
        # Reproducible exception keys without publishing a potentially private
        # session ID, raw title, registration link or source page content.
        orphan_details[hashlib.sha256(path.encode('utf-8')).hexdigest()] = {
            'html_sha256': hashlib.sha256(content.encode('utf-8')).hexdigest(),
            'disposition': reason, 'distinct_registration_links': len(parser.ids),
            'historical_source_matches': old_count, 'current_source_matches': new_count,
        }
    assert sum(dispositions.values()) == len(historical_rows)
    assert sum(statuses.values()) == len(current_rows)
    return {
        'historical_rows': len(historical_rows), 'current_rows': len(current_rows),
        'exclusive_historical_dispositions': dict(sorted(dispositions.items())),
        'overlapping_changed_fields_in_unique_pairs': dict(sorted(changed_fields.items())),
        'overlapping_unique_pair_flags': dict(sorted(pair_flags.items())),
        'unique_pair_difference_sets': dict(sorted(difference_sets.items())),
        'current_source_status_labels': dict(sorted(statuses.items())),
        'current_only_registration_identities': len(set(new_links) - set(old_links)),
        'orphan_html_count': len(orphan_details),
        'orphan_dispositions': dict(sorted(orphan_counts.items())),
        'orphans_by_path_sha256': orphan_details,
        'publication_authorized_count': None,
        'limits': [
            'Identity and fact equality are not canonical registry, completion, cancellation or public-safety approval.',
            'Current source status labels may be generated from time; they are not independent completion evidence.',
            'Course differences compare exact source label strings, not semantic Course Master equivalence.',
            'Historical Client provenance and all R1 privacy/timing/mapping gates remain required.',
            'No source record, raw label, location, participant, client or registration URL is emitted.',
            'Orphan link matches require historical fact and alias/content review; no alias is authorized.',
            'No public generator, live canonical query, current inventory, deployment or GSC action is performed.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--current-ref', required=True)
    parser.add_argument('--as-of', required=True, help='Explicit ISO timestamp with offset')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--identity-only', action='store_true',
                        help='Reconcile historical/current JSON identities and orphan HTML links only')
    args = parser.parse_args()
    as_of = datetime.fromisoformat(args.as_of)
    if as_of.tzinfo is None:
        parser.error('--as-of requires a timezone offset')
    current = git('rev-parse', '--verify', args.current_ref + '^{commit}').decode().strip()
    if args.identity_only:
        historical_path, current_path = 'data/schedule.json', 'data/schedule_all.json'
        historical = json.loads(blob(REMOVAL, historical_path))
        current_doc = json.loads(blob(current, current_path))
        historical = historical if isinstance(historical, list) else historical['sessions']
        current_rows = current_doc if isinstance(current_doc, list) else current_doc['sessions']
        ids = {normalized(row)['id'] for row in historical}
        paths = git('ls-tree', '-r', '--name-only', REMOVAL, '--', 'docs/classes').decode().splitlines()
        orphan_paths = [path for path in paths if re.fullmatch(r'docs/classes/[0-9]+\.html', path)
                        and Path(path).stem not in ids]
        orphans = {path: blob(REMOVAL, path).decode('utf-8-sig') for path in orphan_paths}
        report = reconcile_identities(historical, current_rows, orphans)
        report.update({'schema_version': 1, 'mode': 'identity_reconciliation', 'as_of': as_of.isoformat(),
                       'sources': [
                           {'commit': ref, 'path': path, 'blob': git('rev-parse', f'{ref}:{path}').decode().strip()}
                           for ref, path in [(REMOVAL, historical_path), (current, current_path)]
                       ]})
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        print(json.dumps({'output': args.output.as_posix(), 'historical_rows': len(historical),
                          'current_rows': len(current_rows), 'orphan_html_count': len(orphans)}))
        return
    specs = [('original_pattern', PATTERN, 'data/schedule.json', None),
             ('historical_corpus', REMOVAL, 'data/schedule.json', 'raw/Class Report.xlsx'),
             ('seo_core', SEO_CORE, 'docs/data/schedule_future.json', None),
             ('seo_final', SEO_FINAL, 'docs/data/schedule_future.json', None),
             ('current_archive_source', current, 'data/schedule_all.json', None),
             ('current_public', current, 'docs/data/schedule_future.json', None)]
    trees = {}
    for _, ref, _, _ in specs:
        if ref not in trees:
            trees[ref] = set(git('ls-tree', '-r', '--name-only', ref).decode().splitlines())
    def pages(ref):
        return {Path(p).stem for p in trees[ref] if re.fullmatch(r'docs/classes/[0-9]+\.html', p)}
    report = {'schema_version': 1, 'as_of': as_of.isoformat(), 'current_commit': current,
              'publication_authorized_count': None, 'sources': {}, 'recovered_assets': []}
    union_ids, union_external, all_paths = set(), set(), set()
    identities = {}
    for name, ref, path, workbook_path in specs:
        doc = json.loads(blob(ref, path))
        rows = doc if isinstance(doc, list) else doc['sessions']
        summary, records = summarize(rows, pages(ref), pages(current), as_of,
                                     workbook_rows(ref, workbook_path) if workbook_path else None)
        summary.update({'commit': ref, 'path': path, 'blob': git('rev-parse', f'{ref}:{path}').decode().strip(),
                        'workbook_path': workbook_path})
        report['sources'][name] = summary
        identities[name] = {r['external_id'] for r in records if r['external_id']}
        union_ids.update(r['id'] for r in records if r['id'].isdigit())
        union_external.update(r['external_id'] for r in records if r['external_id'])
        all_paths.update(pages(ref))
        for asset in ['scripts/build_landers.py', 'scripts/build_schedule.py', 'scripts/build_index_and_sitemap.py',
                      'scripts/public_class_eligibility.py', path, workbook_path]:
            if asset and asset in trees[ref]:
                report['recovered_assets'].append({'commit': ref, 'path': asset,
                    'blob': git('rev-parse', f'{ref}:{asset}').decode().strip()})
    report['union'] = {'session_ids': len(union_ids), 'registration_ids': len(union_external),
                       'legacy_numeric_urls': len(all_paths), 'legacy_urls_with_any_source_id': len(all_paths & union_ids),
                       'legacy_urls_without_any_source_id': len(all_paths - union_ids)}
    report['identity_overlap'] = {
        'historical_registration_ids_in_current_archive': len(identities['historical_corpus'] & identities['current_archive_source']),
        'current_archive_registration_ids_not_in_historical': len(identities['current_archive_source'] - identities['historical_corpus']),
        'historical_registration_ids_not_in_current_archive': len(identities['historical_corpus'] - identities['current_archive_source']),
    }
    report['limits'] = [
        'Candidate is not public-safe approval or evidence the class was taught; enrollment is not completion.',
        'JSON-only sources lack independent workbook reconciliation; candidate counts are provisional.',
        'Snapshots overlap. Union IDs are inventory identities, not a deduplicated current canonical class registry.',
        'Client and non-public locations require separate review; no numerical pilot cap is imposed.',
        'No participant, client, instructor, location, raw course label, registration URL or row is emitted.',
        'No HTML content/privacy audit, live HTTP check, archive generation, deployment or GSC submission occurred.',
        'Current options require #228 canonical projection and #140 occupancy/freshness proof before publication.',
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'output': args.output.as_posix(), 'sources': len(specs), 'union': report['union']}))


if __name__ == '__main__':
    main()
