import json
import os
from pathlib import Path
import tempfile
import textwrap
import unittest
from unittest.mock import patch
from tests.test_layered_publication_adapter import LayeredPublicationTests


class RefreshRenderTests(unittest.TestCase):
    def test_actual_refresh_step_with_relative_config_and_v2_counts(self):
        repo=Path(__file__).resolve().parents[1]
        workflow=(repo/'.github/workflows/refresh-admin-availability.yml').read_text()
        section=workflow.split('      - name: Rebuild selector feeds and their matching customer pages',1)[1]
        shell=textwrap.dedent(section.split('        run: |',1)[1].split('\n      - name:',1)[0])
        code=shell.split("python - <<'PY'",1)[1].split('\nPY',1)[0]
        case=LayeredPublicationTests();case.setUp();case.add(11,'12:00','13:00',count=1)
        payload=case.payload()
        self.assertNotIn('rejectedOfferCount',payload['counts'])
        original=Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);docs=root/'docs'
            config=dict(output_path='docs/bls.html',alias_output_paths=['docs/BLS.html'],
                        legacy_schedule_path='docs/old.html',title='Fixture')
            try:
                os.chdir(root)
                with patch('scripts.block_start_time_selector.load_block_schedule_page_configs',return_value={'bls':config}), \
                     patch('scripts.block_start_time_selector.build_block_schedule_page',return_value=payload), \
                     patch('scripts.build_bls_block_schedule_pilot.apply_final_live_availability_guard',side_effect=lambda p:p), \
                     patch('scripts.build_bls_block_schedule_pilot.selector_availability_path',return_value=docs/'bls.json'), \
                     patch('scripts.build_bls_block_schedule_pilot.ROOT',root):
                    exec(compile(code,'production-refresh-step','exec'),{})
                for name in ['bls.html','BLS.html','old.html','bls.json']:
                    self.assertTrue((docs/name).exists(),name)
                self.assertEqual((docs/'bls.html').read_bytes(),(docs/'BLS.html').read_bytes())
                self.assertIn('/bls.html',(docs/'old.html').read_text())
                self.assertTrue(json.loads((docs/'bls.json').read_text())['dates'])
            finally:
                os.chdir(original)
