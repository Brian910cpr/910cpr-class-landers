import json
import re
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
REPORT=json.loads((ROOT/'data/audit/hx_historical_location_authority_review_redacted.json').read_text(encoding='utf-8'))


def test_inventory_is_complete_redacted_and_frequency_reconciled():
    assert REPORT['unresolved_before'] == {'rows':4258,'distinct':142}
    assert len(REPORT['inventory']) == 142
    assert sum(x['occurrence_count'] for x in REPORT['inventory']) == 4258
    email=re.compile(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}',re.I)
    assert not any(email.search(x['source_label']) for x in REPORT['inventory'])
    assert all(x['course_families'] and x['date_range'] and x['source_metadata'] for x in REPORT['inventory'])


def test_proposed_locations_are_archive_only_and_not_public():
    proposed=[x['proposed_canonical_record'] for x in REPORT['inventory'] if 'proposed_canonical_record' in x]
    assert len(proposed) == 126
    assert all(x['public'] is False and x['historical_only'] is True and x['scheduling_status']=='archive_only' for x in proposed)
    assert REPORT['safe_aliases_to_existing'] == 0
