import copy
import tempfile
import unittest
from pathlib import Path
from datetime import timedelta
from tests.test_layered_publication_adapter import LayeredPublicationTests
from scripts.layered_day_cache import cached_calculate, pack, scoped_sources
from scripts.layered_selector_adapter import aware


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

    def test_fall_back_cache_does_not_reuse_expired_proof_in_second_hour(self):
        f=self.f
        f.windows=f.windows[:1];f.coverage=f.coverage[:1]
        f.windows[0].update(start='2026-11-03T09:00:00-05:00',end='2026-11-03T15:00:00-05:00')
        f.coverage[0].update(start=f.windows[0]['start'],end=f.windows[0]['end'],
            observed_at='2026-11-01T05:40:00Z',valid_until='2026-11-01T05:55:00Z',freshness_minutes=15)
        f.now=aware('2026-11-01T01:45:00-04:00')
        self.assertTrue(self.run_cache()['reports'][0]['accepted'])
        f.now=aware('2026-11-01T01:05:00-05:00')
        result=self.run_cache()
        self.assertEqual(result['incremental_cache']['hits'],0)
        self.assertFalse(result['reports'][0]['accepted'])

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
        # The third window begins within 48 hours of the crossing interval;
        # its repeat/travel context must also be re-evaluated.
        self.assertEqual({r['date'] for r in result['incremental_cache']['rebuilt']},{'2026-10-11','2026-10-12','2026-10-14'})
        self.assertEqual(result['incremental_cache']['hits'],0)
        self.assertEqual(f.sources[0]['active_registration_count'],None)

    def test_scope_includes_adjacent_day_repeat_context(self):
        f=self.f
        prior=f.add(10,'17:00','19:30',cid='359474',count=1)
        later=f.add(12,'07:00','09:30',cid='359474',count=1)
        distant=f.add(20,'12:00','14:30',cid='359474',count=1)
        self.assertEqual(scoped_sources(f.sources, f.at(11,'08:00'),
                         f.at(11,'18:00'), 0), [prior,later])
        self.assertNotIn(distant, scoped_sources(f.sources,f.at(11,'08:00'),f.at(11,'18:00'),0))
        self.assertEqual(self.decisions(self.run_cache()), self.decisions(f.calculation()))

    def test_admitted_hold_expiry_caps_offer_lease_and_invalidates_cache(self):
        f=self.f
        f.windows=f.windows[:1];f.coverage=f.coverage[:1]
        f.policy['require_verified_day_gravity']=True
        lease=dict(source_event_id='synthetic-hold',kind='hold',course_id='359474',
            instructor='Brian Ennis',resource=f.room,location_resolution='location_resource_map',
            start=f.at(11,'12:00').isoformat(),end=f.at(11,'14:30').isoformat(),
            source_file='landerware_public_orders',checkout_hold_status='admitted',
            hold_admission_attested=True,checkout_hold_capacity_claimed=True,
            checkout_hold_resource_verified=True,checkout_hold_id='fixture-hold',
            checkout_order_id='fixture-order',hold_admitted_at=f.at(5,'11:50').isoformat(),
            hold_expires_at=f.at(5,'12:05').isoformat())
        f.sources=[lease]
        before=self.run_cache()
        self.assertEqual(before['counts']['failed_windows'],0,before['issues'])
        self.assertEqual(before['reports'][0]['valid_until'],aware(lease['hold_expires_at']))
        self.assertEqual(self.run_cache()['incremental_cache']['hits'],1)
        f.now=aware(lease['hold_expires_at'])
        after=self.run_cache()
        self.assertEqual(after['incremental_cache']['hits'],0)
        self.assertEqual(self.decisions(after),self.decisions(f.calculation()))
        self.assertFalse(after['reports'][0]['normalized_occupancy'])
        self.assertTrue(any(c['mode']=='free' for c in after['reports'][0]['accepted']))

    def test_cached_projection_keeps_canonical_first(self):
        f=self.f
        canonical=f.add(11,'12:00','13:00',count=1)
        mirror=dict(canonical,source_file='legacy',source_event_id='fixture-mirror',
                    count_available=False,active_registration_count=None)
        f.sources=[mirror,canonical]
        cached=self.run_cache()
        self.assertEqual(cached['projected_sources'],f.calculation()['projected_sources'])
        self.assertEqual(cached['projected_sources'][0]['source_file'],'canonical_class_sessions')
