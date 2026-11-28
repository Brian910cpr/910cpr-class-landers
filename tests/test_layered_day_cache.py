import copy
import tempfile
import unittest
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch
from tests.test_layered_publication_adapter import LayeredPublicationTests
from scripts.layered_day_cache import cached_calculate, pack, unpack
from scripts.layered_scheduling_engine import stamp
from scripts.layered_selector_adapter import aware


class DayCacheTests(unittest.TestCase):
    def test_effective_owner_intake_preserves_cross_day_repeat_on_cache_hit(self):
        f = self.f
        f.policy['require_verified_day_gravity'] = True
        f.window(12)
        f.add_intake(11, start='2026-10-11T10:00:00-04:00',
                     end='2026-10-11T12:30:00-04:00')
        f.sources = f.attribute()
        self.assertEqual(f.sources[0]['instructor'], 'Brian Ennis')
        cold, warm = self.run_cache(), self.run_cache()
        self.assertEqual(cold['incremental_cache']['hits'], 0)
        self.assertEqual(warm['incremental_cache']['hits'], 3)
        self.assertEqual(self.decisions(warm), self.decisions(cold))
        adjacent = next(row for row in warm['reports'] if row['availability_window'].endswith('-12-00:00'))
        self.assertTrue(any(r['course'] == '359474' and
            'full_course_repeat_within_24_hours' in r.get('reasons', [])
            for r in adjacent['rejected']))
        self.assertTrue(any(r['course'] == '359474' and r['start'].hour > 10
                            for r in adjacent['accepted']))

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

    def test_real_cache_dispositions_protect_all_frozen_windows(self):
        from scripts import layered_publication_adapter as adapter
        from scripts.validate_layered_occupancy_projection import (
            expected_public_windows, validate_engine_coverage, validate_window_dispositions)
        f = self.f
        f.add(11, "12:00", "13:00", count=1, visibility="private", session_status="scheduled")
        expected = expected_public_windows({"rows": f.windows}, now=f.now,
            windows=lambda snapshot: snapshot["rows"], eligible=lambda w: True,
            interval=lambda w: (w["start"], w["end"]),
            source_id=lambda w, i: w["source_availability_window"], resource=f.room)
        shadow = adapter.build_shadow

        def selectively_close(windows, *args, **kwargs):
            if windows[0]["source_availability_window"] == f.windows[1]["source_availability_window"]:
                raise ValueError("missing directional travel rule: synthetic test")
            return shadow(windows, *args, **kwargs)

        with patch.object(adapter, "build_shadow", side_effect=selectively_close):
            for result in (self.run_cache(), self.run_cache()):
                self.assertEqual(len(result["reports"]), 1)
                self.assertEqual(len(result["closed_windows"]), 1)
                validate_engine_coverage(result["reports"])
                validate_window_dispositions(expected, result["reports"], result["closed_windows"], [])
                with self.assertRaisesRegex(ValueError, "neither evaluated nor closed"):
                    validate_window_dispositions(expected, [], result["closed_windows"], [])
        report, = result["reports"]
        self.assertTrue(any(b["canonical_source_ids"] for b in report["normalized_occupancy"]))
        self.assertEqual({c["start"].astimezone(f.now.tzinfo).strftime("%H:%M")
                          for c in report["accepted"] if c["course"] == "210549"}, {"11:00", "13:00"})

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

    def test_cached_instants_preserve_elapsed_duration_across_dst(self):
        for start,end in (
            ('2026-11-01T01:30:00-04:00','2026-11-01T01:30:00-05:00'),
            ('2026-03-08T01:30:00-05:00','2026-03-08T03:30:00-04:00'),
        ):
            with self.subTest(start=start):
                original=dict(start=stamp(start),instruction_end=stamp(end))
                restored=unpack(pack(original))
                self.assertEqual(restored['instruction_end']-restored['start'],
                                 timedelta(hours=1))
                self.assertEqual(pack(restored),pack(original))

    def test_lead_expiry_uses_elapsed_hours_across_spring_forward(self):
        f=self.f
        f.policy['lead_minutes']=1440
        f.windows=f.windows[:1];f.coverage=f.coverage[:1]
        f.windows[0].update(start='2026-03-08T09:00:00-04:00',
                            end='2026-03-08T14:00:00-04:00')
        f.coverage[0].update(start=f.windows[0]['start'],end=f.windows[0]['end'],
            observed_at='2026-03-07T12:00:00Z',valid_until='2026-03-07T16:00:00Z',
            freshness_minutes=240)
        f.now=aware('2026-03-07T07:30:00-05:00')
        first=self.run_cache()
        self.assertTrue(any(aware(c['start']).strftime('%H:%M')=='09:00'
                            for c in first['reports'][0]['accepted']))
        self.assertEqual(self.run_cache()['incremental_cache']['hits'],1)
        f.now=aware('2026-03-07T08:01:00-05:00')
        next_result=self.run_cache()
        self.assertEqual(next_result['incremental_cache']['hits'],0)
        self.assertFalse(any(aware(c['start']).strftime('%H:%M')=='09:00'
                             for c in next_result['reports'][0]['accepted']))

    def test_booking_moved_to_another_day_rebuilds_both_days(self):
        f=self.f;f.add(11,'12:00','13:00',count=1);self.run_cache()
        f.sources=[];f.add(14,'12:00','13:00',count=1)
        result=self.run_cache()
        self.assertEqual({r['date'] for r in result['incremental_cache']['rebuilt']},{'2026-10-11','2026-10-14'})
        self.assertEqual(self.decisions(result),self.decisions(f.calculation()))

    def test_repeat_context_rebuilds_adjacent_day_without_importing_route(self):
        f=self.f;f.policy['require_verified_day_gravity']=True
        f.window(12)
        self.run_cache()
        row=f.add(11,'12:00','13:00',cid='359474',count=1,visibility='private')
        changed=self.run_cache()
        self.assertEqual({r['date'] for r in changed['incremental_cache']['rebuilt']},
                         {'2026-10-11','2026-10-12'})
        report=next(r for r in changed['reports'] if r['availability_window'].startswith('Brian Ennis-12-'))
        self.assertFalse(any(c['course']=='359474' and
            aware(c['start']).strftime('%H:%M')=='11:30' for c in report['accepted']))
        self.assertTrue(any(c['course']=='359474' and
            aware(c['start']).strftime('%H:%M')=='12:30' for c in report['accepted']))
        self.assertTrue(any(c['course']=='329495' and
            aware(c['start']).strftime('%H:%M')=='11:30' for c in report['accepted']))
        self.assertFalse(any(s['id']==row['source_event_id'] for s in report['normalized_occupancy']))
        self.assertEqual(self.decisions(changed),self.decisions(f.calculation()))
        f.sources=[]; removed=self.run_cache()
        self.assertEqual({r['date'] for r in removed['incremental_cache']['rebuilt']},
                         {'2026-10-11','2026-10-12'})

    def test_course_claim_conflict_clears_adjacent_repeat_and_keeps_cache_parity(self):
        f=self.f
        f.policy['require_verified_day_gravity']=True
        f.window(12)
        f.add(11,'12:00','13:00',cid='359474',count=1,visibility='private')
        def before_repeat(result):
            report=next(r for r in result['reports'] if r['availability_window'].startswith('Brian Ennis-12-'))
            return any(c['course']=='359474' and aware(c['start']).strftime('%H:%M')=='11:30'
                       for c in report['accepted'])
        self.assertFalse(before_repeat(self.run_cache()))
        other=f.add(11,'12:00','13:00',cid='209809',count=1,visibility='private')
        other['source_event_id']='distinct-canonical-overlap'
        result=self.run_cache()
        self.assertTrue(before_repeat(result))
        self.assertEqual(self.decisions(result),self.decisions(f.calculation()))
        self.assertEqual({r['date'] for r in result['incremental_cache']['rebuilt']},
                         {'2026-10-11','2026-10-12'})

    def test_offsite_route_scope_parity_and_cache_invalidation(self):
        f=self.f
        f.windows=f.windows[:1];f.coverage=f.coverage[:1]
        source=dict(source_event_id='synthetic-offsite', start=f.at(14,'09:00').isoformat(),
            end=f.at(14,'10:00').isoformat(), instructor='Brian Ennis',
            location='fixture-unmapped-offsite', resource='fixture-unmapped-offsite',
            source_file='canonical_class_sessions', visibility='private',
            active_registration_count=1, count_available=True)
        f.sources=[source]
        distant=self.run_cache()
        self.assertEqual(distant['counts']['failed_windows'],0)
        self.assertEqual(len(distant['projected_sources']),1)
        self.assertEqual(self.decisions(distant),self.decisions(f.calculation()))
        source.update(start=f.at(12,'09:00').isoformat(),end=f.at(12,'10:00').isoformat())
        near=self.run_cache()
        self.assertEqual(near['incremental_cache']['hits'],0)
        self.assertEqual(near['counts']['failed_windows'],1)
        self.assertEqual(near['counts']['failed_windows'],f.calculation()['counts']['failed_windows'])
        self.assertTrue(any('missing directional travel rule' in row['reason'] for row in near['issues']))
        self.assertEqual(self.run_cache()['incremental_cache']['hits'],1)
        source.update(instructor='Unrelated Instructor')
        independent=self.run_cache()
        self.assertEqual(independent['counts']['failed_windows'],0)
        self.assertEqual(self.decisions(independent),self.decisions(f.calculation()))

    def test_long_explicit_route_extends_offsite_scope(self):
        f=self.f
        f.windows=f.windows[:1];f.coverage=f.coverage[:1]
        f.policy['travel_minutes']={f.room+'->fixture-known-far-route':3000}
        f.sources=[dict(source_event_id='synthetic-offsite-far',start=f.at(14,'09:00').isoformat(),
            end=f.at(14,'10:00').isoformat(),instructor='Brian Ennis',
            location='fixture-unmapped-offsite',resource='fixture-unmapped-offsite',
            source_file='canonical_class_sessions',visibility='private',
            active_registration_count=1,count_available=True)]
        result=cached_calculate(f.windows,f.sources,f.courses,f.policy,f.resources,f.now,
            lambda w:(w['start'],w['end']),lambda w,c:True,f.coverage,f.policy['travel_minutes'],
            cache_dir=Path(self.directory.name))
        self.assertEqual(result['counts']['failed_windows'],1)
        self.assertEqual(result['counts']['failed_windows'],f.calculation()['counts']['failed_windows'])
        self.assertEqual(len(result['projected_sources']),1)

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
