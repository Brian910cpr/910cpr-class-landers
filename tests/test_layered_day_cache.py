import copy
import tempfile
import unittest
from pathlib import Path
from datetime import timedelta
from tests.test_layered_publication_adapter import LayeredPublicationTests
from scripts.layered_day_cache import cached_calculate, pack


class DayCacheTests(unittest.TestCase):
    def decisions(self, result):
        return [[(c['course'],c['start'],c['end'],c['mode']) for c in r['accepted']] for r in result['reports']]
    def setUp(self):
        self.f=LayeredPublicationTests();self.f.setUp();self.f.window(14)
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)

    def run_cache(self):
        f=self.f
        return cached_calculate(f.windows,f.sources,f.courses,f.policy,f.resources,f.now,
            lambda w:(w['start'],w['end']),lambda w,c:True,f.coverage,
            cache_dir=Path(self.directory.name),horizon_days=90)

    def test_unchanged_reuses_and_paid_growth_rebuilds_only_affected_scope(self):
        f=self.f;f.add(11,'12:00','13:00',count=1)
        first=self.run_cache();self.assertEqual(len(first['incremental_cache']['rebuilt']),2)
        self.assertEqual(self.run_cache()['incremental_cache']['hits'],2)
        f.add(11,'13:00','14:00',count=1)
        second=self.run_cache()
        self.assertEqual(second['incremental_cache']['hits'],1)
        self.assertEqual([r['date'] for r in second['incremental_cache']['rebuilt']],['2026-10-11'])
        self.assertEqual(self.decisions(second),self.decisions(f.calculation()))

    def test_removed_or_moved_booking_invalidates_old_scope_and_keeps_inputs(self):
        f=self.f;row=f.add(11,'12:00','13:00',count=None)
        self.run_cache();original=copy.deepcopy(f.sources)
        self.run_cache();self.assertEqual(f.sources,original)
        f.sources=[]
        changed=self.run_cache();self.assertEqual(changed['incremental_cache']['hits'],1)
        self.assertEqual(self.decisions(changed),self.decisions(f.calculation()))

    def test_expired_proof_cannot_be_reused(self):
        self.run_cache();self.f.now+=timedelta(hours=2)
        result=self.run_cache()
        self.assertEqual(result['incremental_cache']['hits'],0)
        self.assertTrue(all(not r['accepted'] for r in result['reports']))

    def test_corrupt_cache_is_recomputed(self):
        self.run_cache()
        for path in Path(self.directory.name).glob('*.json'):path.write_text('broken')
        self.assertEqual(self.run_cache()['incremental_cache']['hits'],0)

    def test_booking_moved_to_another_day_rebuilds_both_days(self):
        f=self.f;f.add(11,'12:00','13:00',count=1);self.run_cache()
        f.sources=[];f.add(14,'12:00','13:00',count=1)
        result=self.run_cache()
        self.assertEqual({r['date'] for r in result['incremental_cache']['rebuilt']},{'2026-10-11','2026-10-14'})
        self.assertEqual(self.decisions(result),self.decisions(f.calculation()))

    def test_horizon_excludes_windows_after_ninety_days(self):
        f=self.f;window=copy.deepcopy(f.windows[0]);start=f.now+timedelta(days=95)
        window.update(start=start.isoformat(),end=(start+timedelta(hours=2)).isoformat(),source_availability_window='outside-horizon')
        f.windows.append(window)
        self.assertEqual(self.run_cache()['counts']['input_windows'],2)

    def test_cross_midnight_commitment_invalidates_both_intersecting_days(self):
        f=self.f;f.window(12);self.run_cache()
        row=f.add(11,'23:30','23:59',count=None)
        row['end']=f.at(12,'00:30').isoformat()
        result=self.run_cache()
        self.assertEqual({r['date'] for r in result['incremental_cache']['rebuilt']},{'2026-10-11','2026-10-12'})
        self.assertEqual(result['incremental_cache']['hits'],1)
        self.assertEqual(f.sources[0]['active_registration_count'],None)
