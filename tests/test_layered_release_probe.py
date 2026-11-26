import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts import run_layered_release_probe as probe

class ProbeTests(unittest.TestCase):
    def test_failed_calculation_restores_shadow_policy_and_records_no_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            policy=root/'data/config/layered_scheduling_policy.json';policy.parent.mkdir(parents=True)
            original=b'{"mode":"shadow"}';policy.write_bytes(original)
            snap=root/'data/audit/live_availability_snapshot_preview.json';snap.parent.mkdir(parents=True);snap.write_text('{"layered_commitment_coverage":[]}')
            canonical=root/'data/runtime/canonical_scheduling_demand.json';canonical.parent.mkdir(parents=True);canonical.write_text('{"sessions":[]}')
            def fail(key):
                self.assertIsInstance(key,dict)
                self.assertEqual(json.loads(policy.read_bytes())["mode"],"active_local_v2")
                raise ValueError("invalid source")
            with patch.object(probe,'ROOT',root),patch.object(probe,'load_block_schedule_page_configs',return_value={'bls':{}}),patch.object(probe,'build_block_schedule_page',side_effect=fail):
                with self.assertRaises(ValueError):probe.run()
            self.assertEqual(policy.read_bytes(),original)
            result=json.loads((root/'data/runtime/audit_previews/v2_release_probe/proof.json').read_text())
            self.assertFalse(result['published']);self.assertNotIn('calculation_completed',result)

    def test_partial_window_evaluation_is_not_release_proof(self):
        def page(inputs, evaluated, failed):
            return {'counts': dict(input_windows=inputs,
                                   evaluated_windows=evaluated,
                                   failed_windows=failed)}
        complete = page(147, 147, 0)
        pages = {key: complete for key in probe.REQUIRED_PAGE_KEYS}
        self.assertTrue(probe.coverage_release_passed(pages))
        self.assertTrue(probe.coverage_release_passed(dict(pages, acls=page(0, 0, 0))))
        self.assertFalse(probe.coverage_release_passed(dict(pages, acls=page(147, 136, 11))))
        self.assertFalse(probe.coverage_release_passed(dict(pages, bls=page(147, 136, 0))))
        self.assertFalse(probe.coverage_release_passed({key: page(0, 0, 0) for key in pages}))
        self.assertFalse(probe.coverage_release_passed(dict(pages, bls={'counts': {}})))
        self.assertFalse(probe.coverage_release_passed({'bls': complete}))
        self.assertFalse(probe.coverage_release_passed({}))

    def test_proof_summary_does_not_emit_private_source_details(self):
        raw = [
            {'reason': 'missing directional travel rule: private-home->primary',
             'instructor': 'private-person', 'source_id': 'private-id',
             'start': '2026-11-26T12:34:00-05:00'},
            {'reason': 'invalid source private-id'},
        ]
        counts, by_date = probe.public_issue_summary(raw)
        self.assertEqual(counts, {'missing_directional_travel_rule': 1,
                                  'availability_coverage_unknown': 1})
        self.assertEqual(by_date, {
            '2026-11-26': {'missing_directional_travel_rule': 1},
            'unscoped': {'availability_coverage_unknown': 1},
        })
        serialized = json.dumps([counts, by_date])
        for private in ('private-home', 'private-person', 'private-id', '12:34'):
            self.assertNotIn(private, serialized)
