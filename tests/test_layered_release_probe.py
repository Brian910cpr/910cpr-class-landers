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
                self.assertEqual(json.loads(policy.read_bytes())["mode"],"active_local_v2")
                raise ValueError("invalid source")
            with patch.object(probe,'ROOT',root),patch.object(probe,'load_block_schedule_page_configs',return_value={'bls':{}}),patch.object(probe,'build_block_schedule_page',side_effect=fail):
                with self.assertRaises(ValueError):probe.run()
            self.assertEqual(policy.read_bytes(),original)
            result=json.loads((root/'data/runtime/audit_previews/v2_release_probe/proof.json').read_text())
            self.assertFalse(result['published']);self.assertNotIn('calculation_completed',result)
