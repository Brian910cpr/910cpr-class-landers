import copy
import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from scripts.layered_publication_adapter import calculate, publish, project_sources, finalize
from scripts.layered_selector_adapter import aware
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload, render_html
from scripts.apply_anchor_policy import finalize_selector_payload

ROOT = Path(__file__).resolve().parents[1]


class LayeredPublicationTests(unittest.TestCase):
    def setUp(self):
        self.policy=json.loads((ROOT/'data/config/layered_scheduling_policy.json').read_text())
        self.policy.update(mode='active_local_v2',lead_minutes=0)
        self.resources=json.loads((ROOT/'data/config/location_resource_map.json').read_text())
        self.page=json.loads((ROOT/'data/config/block_schedule_pages.json').read_text())['pages']['heartsaver']
        self.courses=[dict(course_id=cid,course_family=family,kind=kind,clean_course_name=name,
                          blended_classroom_skills='blended' if kind=='skills' else 'classroom')
            for cid,family,kind,name in [('210549','BLS','skills','AHA HeartCode BLS Skills'),
                ('329495','Heartsaver','skills','Heartsaver Blended Skills'),
                ('209809','Heartsaver','full','Heartsaver Full Classroom'),
                ('359474','BLS','full','BLS Renewal')]]
        self.now=aware('2026-10-05T12:00:00-04:00')
        self.windows=[];self.sources=[];self.coverage=[]
        self.room=self.policy['primary_resource']
        self.window(11)

    def at(self,day,clock): return aware(f'2026-10-{day:02d}T{clock}:00-04:00')

    def window(self,day,start='00:00',end='00:00',name='Brian Ennis',next_day=True):
        row=dict(instructor_name=name,person_id=self.policy['brian_person_id'] if 'Brian' in name else 'other',
            location_name=':: Wilmington; Shipyard Blvd',source_availability_window=f'{name}-{day}-{start}',
            start=self.at(day,start).isoformat(),end=self.at(day+int(next_day),end).isoformat())
        self.windows.append(row)
        self.coverage.append(dict(status='known_complete',instructor=name,location=self.room,
            start=row['start'],end=row['end'],observed_at=self.now.isoformat(),
            valid_until=(self.now+timedelta(minutes=60)).isoformat(),source='explicit_fixture_complete_calendar'))
        return row

    def add(self,day,start,end,cid='210549',name='Brian Ennis',count=None,**extra):
        row=dict(source_event_id=f'fixture-{day}-{start}-{name}',start=self.at(day,start).isoformat(),
            end=self.at(day,end).isoformat(),instructor=name,course_id=cid,resource=self.room,
            location_resolution='location_resource_map',source_file='canonical_class_sessions',
            active_registration_count=count,count_available=count is not None,**extra)
        self.sources.append(row);return row

    def calculation(self):
        return calculate(self.windows,self.sources,self.courses,self.policy,self.resources,self.now,
            lambda w:(w['start'],w['end']),lambda w,c:True,self.coverage,self.policy.get('travel_minutes'))

    def payload(self,seated=()):
        return publish(self.calculation(),self.page,self.courses,self.windows,self.now,
            lambda w,s,c:('fixture-day','fixture-container',f'https://fixture.test/enroll?appointmentDayId=fixture-day&courseId={c}&startTime={s:%H:%M}',None),
            lambda s,c:[],seated)

    def starts(self,cid='209809',day=None):
        return {o['startTime'] for o in self.payload()['offers'] if o['courseId']==cid and (day is None or o['date']==f'2026-10-{day:02d}')}

    def test_repeated_skills_growth_and_full_class_enlarges_block(self):
        self.add(11,'12:00','13:00')
        for cid in ['210549','329495']: self.assertEqual(self.starts(cid),{'11:00','13:00'})
        self.add(11,'13:00','14:00','329495')
        for cid in ['210549','329495']: self.assertEqual(self.starts(cid),{'11:00','14:00'})
        self.add(11,'11:00','12:00')
        self.add(11,'14:00','16:30','209809',count=1)
        for cid in ['210549','329495']: self.assertEqual(self.starts(cid),{'10:00','16:30'})
        self.assertEqual(len(self.calculation()['reports'][0]['blocks']),1)

    def test_oct11_13_14_full_heartsaver_from_shared_room_edges(self):
        self.add(11,'17:00','19:00','359474',count=1)
        self.window(13,'07:45','15:00',next_day=False)
        self.window(13,'17:30','00:00')
        self.add(13,'14:00','18:00','359474',name='Amy',count=None)
        self.window(14,'17:30','00:00')
        self.add(14,'17:30','19:30','329495')
        self.assertEqual(self.starts(day=11),{'14:30','19:00'})
        self.assertEqual(self.starts(day=13),{'11:30','18:00'})
        self.assertEqual(self.starts(day=14),{'19:30'})
        self.assertTrue(all(o['schedulerConsumptionMinutes']==150 for o in self.payload()['offers'] if o['courseId']=='209809'))

    def test_oct12_conflicts_eliminate_full_class_edges(self):
        self.windows=[];self.coverage=[];self.window(12)
        self.add(12,'09:00','11:00','359474',name='Michelle')
        self.add(12,'12:00','13:00','210549')
        self.add(12,'17:00','19:00','359474',name='Michelle')
        for a,b in [('06:30','07:45'),('09:00','11:00'),('15:00','17:30'),('17:00','18:00'),('18:00','23:59')]:
            self.add(12,a,b,source_file_override='calendar')
            self.sources[-1]['source_file']='live_availability_snapshot.blocked'
        self.assertEqual(self.starts(),set())
        self.assertTrue(self.calculation()['reports'][0]['rejected'])

    def test_positive_count_changes_keep_occupied_edges_and_zero_does_not_free_room(self):
        row=self.add(11,'12:00','13:00',count=1)
        before=self.starts('329495');row['active_registration_count']=2
        self.assertEqual(self.starts('329495'),before)
        seated=dict(session_id=row['source_event_id'],date='2026-10-11',startTime='12:00',
            courseId='210549',courseName='existing',offerType='seated_class')
        row['active_registration_count']=0
        self.assertFalse(any(o.get('offerType')=='seated_class' for o in self.payload([seated])['offers']))
        self.assertEqual(self.starts('329495'),before)
        row['count_available']=False
        self.assertTrue(any(o.get('offerType')=='seated_class' for o in self.payload([seated])['offers']))
        self.assertIsNone(self.calculation()['projected_sources'][0]['active_registration_count'])

    def test_unknown_bounds_are_scoped_and_stale_coverage_fails_closed(self):
        self.window(13)
        bad=self.add(11,'12:00','12:00',cid='unknown')
        bad['uncertainty_scope']=dict(start=self.at(11,'00:00').isoformat(),end=self.at(12,'00:00').isoformat())
        self.assertFalse(self.starts(day=11));self.assertTrue(self.starts(day=13))
        self.coverage[-1]['valid_until']=self.now.isoformat()
        self.assertFalse(self.starts(day=13))
        self.assertTrue(self.calculation()['issues'])

    def test_incomplete_proof_does_not_sterilize_another_instructor(self):
        self.window(11,name='Michelle')
        self.coverage=self.coverage[1:]
        offers=self.payload()['offers']
        self.assertFalse(any(o['instructor']=='Brian Ennis' for o in offers))
        self.assertTrue(any(o['instructor']=='Michelle' for o in offers))

    def test_unknown_offsite_travel_affects_only_own_instructor(self):
        self.window(11,name='Michelle')
        self.sources.append(dict(source_event_id='offsite',start=self.at(11,'09:00').isoformat(),
            end=self.at(11,'11:00').isoformat(),instructor='Brian Ennis',location='offsite',course_id='210549'))
        offers=self.payload()['offers']
        self.assertFalse(any(o['instructor']=='Brian Ennis' for o in offers))
        self.assertTrue(any(o['instructor']=='Michelle' for o in offers))

    def test_known_directional_travel_changes_edges_and_actual_room_collision_rejects(self):
        self.sources.append(dict(source_event_id='offsite',start=self.at(11,'09:00').isoformat(),
            end=self.at(11,'11:00').isoformat(),instructor='Brian Ennis',location='offsite',course_id='210549'))
        self.policy['travel_minutes']={self.room+'->offsite':30,'offsite->'+self.room:30}
        self.assertEqual(self.starts('210549'),{'07:30','11:30'})
        self.add(11,'12:00','13:00',name='Michelle')
        self.assertNotIn('11:30',self.starts('210549'))

    def test_paid_full_family_limit_preserves_both_skills_and_other_family(self):
        self.add(11,'12:00','14:30','209809',count=1)
        self.assertFalse(self.starts('209809'))
        self.assertTrue(self.starts('359474'))
        self.assertEqual(self.starts('329495'),{'11:00','14:30'})

    def test_missing_owned_url_rejects_calculated_offer(self):
        self.add(11,'12:00','13:00')
        payload=publish(self.calculation(),self.page,self.courses,self.windows,self.now,
            lambda *args:(None,None,None,'no_matching_appointment_container'),lambda *args:[])
        self.assertFalse(payload['offers'])
        self.assertIn('missing_owned_appointment_url',payload['rejectionReasonCounts'])

    def test_distinct_full_formats_share_family_without_daywide_suppression(self):
        alternative = dict(self.courses[2], course_id='fixture-distinct-full-format',
                           clean_course_name='Fixture distinct Heartsaver format')
        self.courses.append(alternative)
        for count in (1, None):
            with self.subTest(count=count):
                self.sources=[]
                self.add(11,'12:00','14:30','209809',count=count)
                report=self.calculation()['reports'][0]
                choices=[c for c in report['accepted'] if c['course']==alternative['course_id']]
                self.assertTrue(choices)
                self.assertTrue(all(c['end'] <= self.at(11,'12:00') or
                                    c['start'] >= self.at(11,'14:30') for c in choices))
                self.assertFalse([c for c in report['accepted'] if c['course']=='209809'])
                self.assertEqual(self.sources[0]['active_registration_count'], count)

    def test_zero_length_source_resolves_course_metadata_not_free_time(self):
        row=self.add(11,'12:00','12:00')
        row['duration_minutes']=60
        self.assertEqual(self.starts('329495'),{'11:00','13:00'})

    def test_overnight_full_offer_preserves_next_date_end_and_free_day_thinning(self):
        self.add(11,'20:00','21:30','359474')
        self.windows[0]['end']=self.at(12,'06:00').isoformat()
        self.coverage[0]['end']=self.windows[0]['end']
        full=[o for o in self.payload()['offers'] if o['courseId']=='209809' and o['startTime']=='21:30'][0]
        self.assertTrue(full['occupiedUntil'].startswith('2026-10-12T00:00'))
        self.sources=[]
        self.assertIn('00:00',self.starts('210549'))
        self.assertNotIn('00:30',self.starts('210549'))
        self.windows=[];self.coverage=[];self.window(11,'03:00','05:00',next_day=False)
        self.assertEqual(self.starts('210549'),{'03:00','03:30','04:00'})

    def test_feed_trace_and_finalizer_keep_v2_edges_not_legacy_date_gate(self):
        self.add(11,'17:00','19:00','359474')
        payload=self.payload()
        # Finalizer is re-used by landscape. Freeze its clock, not the source evidence.
        with patch('scripts.layered_publication_adapter.finalize',side_effect=lambda p:finalize(p,self.now)):
            result=finalize_selector_payload(payload,[],{'sessions':[]},{'mode':'daily_anchor_stack_v1'})
        self.assertEqual([o['startTime'] for o in result['offers'] if o['courseId']=='209809'],['14:30','19:00'])
        feed=public_selector_availability_payload(result)
        full=[c for d in feed['dates'] for t in d['startTimes'] for c in t['courses'] if c['courseId']=='209809']
        self.assertTrue(all(c['sourceSessionIds'] and c['edgeIds'] and c['occupiedUntil'] for c in full))
        html=render_html(result)
        self.assertIn('Heartsaver',html)
        self.assertIn('layered-publication.v2',json.dumps(feed))
        expired=finalize(result,self.now+timedelta(hours=2))
        self.assertFalse(expired['offers'])

    def test_split_availability_on_planted_day_never_reverts_to_free_space_scan(self):
        self.windows=[];self.coverage=[]
        self.window(11,'00:00','12:00',next_day=False)
        self.window(11,'13:00','00:00')
        self.add(11,'12:00','13:00')
        self.assertEqual(self.starts('210549'),{'11:00','13:00'})
        self.assertEqual(self.starts('329495'),{'11:00','13:00'})

    def test_bounded_unknown_interval_closes_only_overlap_within_a_window(self):
        bad=self.add(11,'12:00','12:00',cid='unknown')
        bad['uncertainty_scope']=dict(start=self.at(11,'12:00').isoformat(),end=self.at(11,'13:00').isoformat())
        starts=self.starts('210549')
        self.assertNotIn('12:00',starts)
        self.assertIn('10:00',starts);self.assertIn('14:00',starts)

    def test_unknown_full_family_count_rejects_only_full_family_not_skills(self):
        self.add(11,'12:00','14:30','209809')
        self.assertFalse(self.starts('209809'))
        self.assertEqual(self.starts('329495'),{'11:00','14:30'})
        self.assertTrue(self.starts('359474'))

    def test_old_or_naive_coverage_and_bad_count_are_not_proof(self):
        self.coverage[0]['observed_at']='2026-09-27T12:00:00-04:00'
        self.assertFalse(self.starts())
        self.coverage[0]['observed_at']='2026-10-05T12:00:00'
        self.assertFalse(self.starts())
        projected=project_sources([dict(active_registration_count=True,count_available=True)],{})
        self.assertIsNone(projected[0]['active_registration_count'])

    def test_source_records_not_mutated_and_explicit_activation_required(self):
        self.add(11,'12:00','13:00',count=1)
        before=copy.deepcopy(self.sources);self.payload();self.assertEqual(self.sources,before)
        self.policy['mode']='shadow'
        with self.assertRaisesRegex(ValueError,'explicit'):self.calculation()


if __name__=='__main__':unittest.main()
