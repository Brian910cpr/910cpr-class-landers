import copy
import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from scripts.layered_publication_adapter import apply_default_owner_occupancy, calculate, publish, project_sources, finalize
from scripts.layered_selector_adapter import aware
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload, public_layered_landscape, render_html
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
            lambda s,c:[],seated,
            require_verified_day_gravity=self.policy.get('require_verified_day_gravity', False))

    def starts(self,cid='209809',day=None):
        return {o['startTime'] for o in self.payload()['offers'] if o['courseId']==cid and (day is None or o['date']==f'2026-10-{day:02d}')}

    def test_clear_day_offers_all_qualified_courses_at_every_half_hour(self):
        # Owner doctrine #16: an open ten-hour qualified window does not
        # automatically thin a course's valid starts to an hourly cadence.
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11, '08:00', '18:00', next_day=False)
        for course in self.courses:
            cid = course['course_id']
            last = 18 if course['kind'] == 'skills' else 15
            expected = {(self.at(11, '08:00') + timedelta(minutes=30*i)).strftime('%H:%M')
                        for i in range(last+1)}
            with self.subTest(cid=cid):
                self.assertEqual(self.starts(cid, day=11), expected)
        self.assertTrue(all(x['step_minutes'] == 30
            for report in self.calculation()['reports']
            for x in report['free_intervals']))

    def test_attested_private_seat_survives_exact_interval_engine_dedup(self):
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11, '08:00', '18:00', next_day=False)
        legacy=self.add(11,'12:00','13:00',cid='359474',count=None)
        legacy['source_file']='legacy'
        canonical=dict(legacy,source_event_id='synthetic-attested-private',
            source_file='canonical_class_sessions',visibility='private',
            operational_has_active_seat=True)
        for rows in ([legacy,canonical],[canonical,legacy]):
            with self.subTest(first=rows[0]['source_file']):
                self.sources=list(rows)
                occupied=self.calculation()['reports'][0]['normalized_occupancy']
                self.assertEqual(len(occupied),1)
                self.assertEqual(occupied[0]['id'],'synthetic-attested-private')
                self.assertTrue(occupied[0]['operational_has_active_seat'])
                self.assertEqual(occupied[0]['kind'],'paid')
                self.assertIsNone(occupied[0]['headcount'])
                public=public_selector_availability_payload(self.payload())
                self.assertNotIn('synthetic-attested-private',json.dumps(public))
                self.assertFalse(any(o.get('offerType')=='seated_class'
                    for o in self.payload()['offers']))

    def test_restricted_identity_cannot_inherit_public_mirror_route(self):
        for visibility in ('private', 'unlisted', 'internal'):
            with self.subTest(visibility=visibility):
                self.sources=[]
                public=self.add(11,'12:00','13:00',count=None,
                    visibility='public',external_class_id='fixture-shared')
                public['source_file']='legacy'
                restricted=dict(public,source_event_id='fixture-restricted',
                    source_file='canonical_class_sessions',visibility=visibility,
                    operational_has_active_seat=True,count_available=True,
                    active_registration_count=1)
                seated=dict(session_id='fixture-shared',date='2026-10-11',
                    startTime='12:00',courseId='210549',courseName='Synthetic',
                    instructor='Brian Ennis',offerType='seated_class',
                    visibility='public',registrationUrl='https://fixture.invalid/private')
                for sources in ([public,restricted],[restricted,public]):
                    self.sources=sources
                    result=self.payload([seated])
                    self.assertFalse(any(o.get('offerType')=='seated_class'
                                         for o in result['offers']))
                    self.assertEqual([r for r in result['rejectedCourseStartTimes']
                        if 'nonpublic_occupied_not_joinable' in r.get('reasons',[])],
                        [{'reasons':['nonpublic_occupied_not_joinable']}])
                    self.assertNotIn(seated['registrationUrl'],json.dumps(result['offers']))
                    self.assertTrue(self.calculation()['reports'][0]['normalized_occupancy'])

    def test_all_seated_identity_aliases_enforce_restricted_visibility(self):
        for mode in (False, True):
            self.policy['require_verified_day_gravity'] = mode
            for visibility in ('private', 'unlisted', 'internal'):
                self.sources=[]
                self.add(11,'12:00','13:00',count=1,visibility=visibility,
                         external_class_id='fixture-restricted-external')
                restricted=self.sources[0]
                base=dict(session_id='fixture-unrelated',date='2026-10-11',
                          startTime='12:00',courseId='210549',courseName='Synthetic',
                          instructor='Brian Ennis',offerType='seated_class',
                          visibility='public',registrationUrl='https://fixture.invalid/alias')
                for key in (restricted['source_event_id'], restricted['external_class_id']):
                    for alias in (dict(sourceSessionId=key,sourceAvailabilityBlock=None),
                                  dict(sourceAvailabilityBlock={'sessionId':key}),
                                  dict(session_id=key,sourceAvailabilityBlock=None)):
                        with self.subTest(mode=mode,visibility=visibility,key=key,alias=alias):
                            result=self.payload([dict(base,**alias)])
                            self.assertFalse(any(o.get('offerType')=='seated_class'
                                                 for o in result['offers']))
                            self.assertIn({'reasons':['nonpublic_occupied_not_joinable']},
                                          result['rejectedCourseStartTimes'])
                            self.assertNotIn(base['registrationUrl'],json.dumps(result['offers']))
                control=self.payload([dict(base,sourceAvailabilityBlock=None)])
                self.assertTrue(any(o.get('offerType')=='seated_class' for o in control['offers']))
                self.assertTrue(self.calculation()['reports'][0]['normalized_occupancy'])

    def test_verified_gravity_distinguishes_shell_and_private_demand(self):
        self.policy['require_verified_day_gravity'] = True
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11,'08:00','18:00',next_day=False)
        self.window(11,'08:00','18:00',name='Michelle',next_day=False)
        source=self.add(11,'12:00','13:00',cid='359474',count=None,visibility='private')
        for count in (None,0):
            source.update(active_registration_count=count,count_available=count is not None)
            offers=self.payload()['offers']
            self.assertTrue(any(o['instructor']=='Brian Ennis' and o['courseId']=='329495'
                                and o['startTime']=='08:00' and o['scheduleRole']=='open_day' for o in offers))
            self.assertFalse(any(o['startTime']=='12:00' for o in offers))
        source.update(operational_has_active_seat=True,count_available=False,active_registration_count=None,course_id='')
        offers=self.payload()['offers']
        self.assertFalse(any(o['instructor']=='Brian Ennis' and o['scheduleRole']=='open_day' for o in offers))
        self.assertTrue(any(o['instructor']=='Brian Ennis' and o['scheduleRole']=='barnacle' for o in offers))
        self.assertTrue(any(o['instructor']=='Michelle' and o['scheduleRole']=='open_day'
                            and o['startTime']=='08:00' for o in offers))
        self.assertFalse(any(o['startTime']=='12:00' for o in offers))
        self.assertNotIn(source['source_event_id'],json.dumps(public_selector_availability_payload(self.payload())))

    def test_verified_gravity_survives_split_windows_and_not_next_clear_day(self):
        self.policy['require_verified_day_gravity'] = True
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11,'08:00','12:00',next_day=False)
        self.window(11,'13:00','18:00',next_day=False)
        self.window(12,'08:00','18:00',next_day=False)
        self.add(11,'12:00','13:00',cid='359474',count=1,visibility='private')
        offers=self.payload()['offers']
        skills=[o for o in offers if o['courseId']=='329495']
        self.assertEqual({o['startTime'] for o in skills if o['date']=='2026-10-11'},{'11:00','13:00'})
        self.assertTrue(any(o['date']=='2026-10-12' and o['startTime']=='08:00'
                            and o['scheduleRole']=='open_day' for o in skills))

    def test_verified_full_course_repeat_is_elapsed_and_exact_course(self):
        self.policy['require_verified_day_gravity'] = True
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(10,'08:00','18:00',next_day=False)
        self.window(12,'08:00','18:00',next_day=False)
        self.window(12,'08:00','18:00',name='Michelle',next_day=False)
        row=self.add(11,'12:00','13:00',cid='359474',count=1,visibility='private')
        offers=self.payload()['offers']
        starts=lambda day,cid,name: {o['startTime'] for o in offers
            if o['date']==f'2026-10-{day:02d}' and o['courseId']==cid and o['instructor']==name}
        self.assertIn('11:30',starts(10,'359474','Brian Ennis'))
        self.assertNotIn('12:00',starts(10,'359474','Brian Ennis'))
        self.assertNotIn('12:30',starts(10,'359474','Brian Ennis'))
        self.assertNotIn('11:30',starts(12,'359474','Brian Ennis'))
        self.assertNotIn('12:00',starts(12,'359474','Brian Ennis'))
        self.assertIn('12:30',starts(12,'359474','Brian Ennis'))
        self.assertIn('11:30',starts(12,'329495','Brian Ennis'))
        self.assertIn('11:30',starts(12,'209809','Brian Ennis'))
        self.assertIn('11:30',starts(12,'359474','Michelle'))
        row.update(count_available=False,active_registration_count=None)
        self.assertIn('11:30',self.starts('359474',day=12))

    def test_repeat_context_uses_utc_and_does_not_add_travel_sources(self):
        from scripts.layered_publication_adapter import repeat_context_for_window, project_sources
        from scripts.layered_scheduling_engine import stamp
        metadata={str(c['course_id']):c for c in self.courses}
        source=self.add(11,'12:00','13:00',cid='359474',count=1,visibility='private')
        source.update(start='2026-11-01T12:00:00-05:00',end='2026-11-01T13:00:00-05:00',
                      location='unmapped-synthetic-venue')
        result=repeat_context_for_window(project_sources(self.sources,metadata),metadata,
            {'instructor_name':'Brian Ennis'},stamp('2026-10-31T12:00:00-04:00'),
            stamp('2026-11-01T14:00:00-05:00'))
        self.assertEqual(result,[{'course':'359474','start':'2026-11-01T17:00:00+00:00'}])
        self.assertEqual(abs(stamp(result[0]['start'])-stamp('2026-10-31T12:00:00-04:00')),timedelta(hours=25))
        self.assertEqual(abs(stamp(result[0]['start'])-stamp('2026-10-31T13:00:00-04:00')),timedelta(hours=24))

    def test_verified_publication_uses_eastern_day_for_utc_source(self):
        self.policy['require_verified_day_gravity'] = True
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11,'18:00','23:30',next_day=False)
        self.window(12,'08:00','18:00',next_day=False)
        source=self.add(11,'20:30','22:30',cid='359474',count=1,visibility='private')
        source.update(start='2026-10-12T00:30:00Z',end='2026-10-12T02:30:00Z')
        offers=self.payload()['offers']
        self.assertTrue(any(o['date']=='2026-10-11' and o['scheduleRole']=='barnacle'
                            for o in offers))
        self.assertFalse(any(o['date']=='2026-10-11' and o['scheduleRole']=='open_day'
                             for o in offers))
        self.assertTrue(any(o['date']=='2026-10-12' and o['startTime']=='08:00'
                            and o['scheduleRole']=='open_day' for o in offers))

    def test_verified_seated_instructor_must_match_source_assignment(self):
        self.policy['require_verified_day_gravity'] = True
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11,'08:00','18:00',next_day=False)
        self.window(11,'08:00','18:00',name='Michelle',next_day=False)
        source=self.add(11,'12:00','14:00',cid='359474',count=1,visibility='public')
        seated=dict(session_id=source['source_event_id'],date='2026-10-11',
            startTime='12:00',courseId='359474',courseName='Synthetic',
            instructor='Michelle',offerType='seated_class',visibility='public',
            registrationUrl='https://fixture.invalid/enroll')
        result=self.payload([seated])
        self.assertIn('seated_instructor_mismatch',result['rejectionReasonCounts'])
        self.assertFalse(any(o.get('offerType')=='seated_class' for o in result['offers']))
        self.assertTrue(any(o['instructor']=='Michelle' and o['startTime']=='08:00'
                            and o['courseId']=='359474' and o['scheduleRole']=='open_day'
                            for o in result['offers']))
        # The known Brian alias is not a mismatch.
        seated['instructor']='Brian'
        result=self.payload([seated])
        self.assertTrue(any(o.get('offerType')=='seated_class' for o in result['offers']))

    def test_rejected_public_diagnostics_never_echo_private_source_dtos(self):
        # Both conflict rejections and expired dynamic URLs pass through this
        # finalizer. Neither may serialize a private record into the public
        # repo's diagnostic artifacts, even when a closure adds a rejection.
        sentinel = "PRIVATE-REGISTRATION-IDENTIFIER-NOT-FOR-PUBLICATION"
        payload = self.payload()
        payload.setdefault('rejectedCourseStartTimes', []).append(dict(
            date='2026-10-11', startTime='12:00', courseId='209809',
            courseFamily='Heartsaver', courseName='Heartsaver Full Classroom',
            offerType='seated_class', reasons=['occupied_by_private_class'],
            sessionId=sentinel, customerEmail='private@example.invalid',
            registrationUrl='https://private.invalid/enroll?token=' + sentinel,
            sourceAvailabilityBlock={'private': sentinel},
            sourceSessionIds=[sentinel], edgeIds=[sentinel]))
        payload['offers'].append(dict(
            date='2026-10-11', startTime='13:00', courseId='209809',
            offerType='dynamic_appointment',
            validUntil=(self.now - timedelta(minutes=1)).isoformat(),
            registrationUrl='https://private.invalid/expired?token=' + sentinel,
            sourceSessionIds=[sentinel]))
        public = finalize(payload, self.now)
        self.assertGreaterEqual(len(public['rejectedCourseStartTimes']), 2)
        for rejected in public['rejectedCourseStartTimes']:
            self.assertTrue(set(rejected).issubset({
                'date', 'startTime', 'courseId', 'courseFamily',
                'courseName', 'offerType', 'scheduleRole', 'reasons'}))
        self.assertNotIn(sentinel, json.dumps(public['rejectedCourseStartTimes']))
        self.assertEqual(payload['rejectedCourseStartTimes'][0]['sessionId'], sentinel)

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

    def test_starred_full_course_consolidates_but_skills_keeps_valid_edges(self):
        for cid in ['210549','209809']:
            with self.subTest(course=cid):
                self.sources=[]
                row=self.add(11,'12:00','13:00',cid=cid)
                self.window(12)
                seated=dict(session_id=row['source_event_id'],date='2026-10-11',startTime='12:00',
                            courseId=cid,courseName='Existing class',offerType='seated_class')
                payload=self.payload([seated])
                day=[o for o in payload['offers'] if o['date']=='2026-10-11' and o['courseId']==cid]
                self.assertEqual(sum(o['offerType']=='seated_class' for o in day),1)
                if cid=='210549':
                    self.assertEqual({o['startTime'] for o in day},{'11:00','12:00','13:00'})
                    self.assertTrue(all(o.get('scheduleRole')=='barnacle' for o in day if o['offerType']!='seated_class'))
                else:
                    self.assertEqual([o['offerType'] for o in day],['seated_class'])
                self.assertTrue(any(o['courseId']!=cid and o['date']=='2026-10-11' for o in payload['offers']))
                self.assertTrue(any(o['courseId']==cid and o['date']=='2026-10-12' for o in payload['offers']))
                self.windows=self.windows[:1];self.coverage=self.coverage[:1]

    def test_oct14_skills_edges_preserve_canonical_two_hour_occupancy(self):
        self.windows=[];self.coverage=[];self.sources=[]
        self.window(14,'15:00','22:00',next_day=False)
        row=self.add(14,'17:30','19:30',cid='329495',count=None)
        seated=dict(session_id=row['source_event_id'],date='2026-10-14',startTime='17:30',
                    courseId='329495',courseName='Existing skills',offerType='seated_class')
        payload=self.payload([seated])
        offers=[o for o in payload['offers'] if o['courseId']=='329495']
        edges=[o for o in offers if o['offerType']!='seated_class']
        self.assertEqual({o['startTime'] for o in edges},{'16:30','19:30'})
        self.assertTrue(all(o['durationMinutes']==45 and o['cleanupBufferMinutes']==15 for o in edges))
        self.assertEqual({o['schedulerConsumptionEnd'] for o in edges},{'17:30','20:30'})
        self.assertEqual(len([o for o in offers if o['offerType']=='seated_class']),1)
        occupied=payload['layeredDiagnostics']['reports'][0]['normalized_occupancy']
        self.assertTrue(any(aware(o['start'])==self.at(14,'17:30') and aware(o['end'])==self.at(14,'19:30') for o in occupied))
        self.windows[0]['start']=self.at(14,'17:30').isoformat()
        self.assertEqual(self.starts('329495',day=14),{'19:30'})

    def test_incomplete_proof_does_not_sterilize_another_instructor(self):
        self.window(11,name='Michelle')
        self.coverage=self.coverage[1:]
        offers=self.payload()['offers']
        self.assertFalse(any(o['instructor']=='Brian Ennis' for o in offers))
        self.assertTrue(any(o['instructor']=='Michelle' for o in offers))

    def test_anchored_day_keeps_edges_but_not_detached_evening_gap(self):
        self.windows=[];self.coverage=[]
        self.window(11,'07:45','14:15',next_day=False)
        self.window(11,'20:00','00:00')
        self.window(11,'20:00','00:00',name='Michelle')
        self.window(12)
        row=self.add(11,'11:45','13:45',cid='209806')
        # The BLS anchor is outside the Heartsaver page's course catalog.
        seated=dict(session_id=row['source_event_id'],date='2026-10-11',startTime='11:45',
                    courseId='209806',courseName='Existing BLS',offerType='seated_class',instructor='Brian Ennis')
        payload=self.payload([seated])
        day=[o for o in payload['offers'] if o['date']=='2026-10-11']
        self.assertTrue(any(o.get('offerType')=='seated_class' for o in day))
        self.assertTrue(any(o.get('scheduleRole')=='barnacle' for o in day))
        self.assertFalse(any(o.get('scheduleRole')=='open_day' and o.get('instructor')=='Brian Ennis' for o in day))
        self.assertTrue(any(o.get('scheduleRole')=='open_day' and o.get('instructor')=='Michelle' for o in day))
        self.assertTrue(any(o.get('scheduleRole')=='open_day' and o['date']=='2026-10-12' for o in payload['offers']))
        self.assertIn('anchored_day_requires_attached_offer',payload['rejectionReasonCounts'])

    def test_unknown_offsite_travel_affects_only_own_instructor(self):
        self.window(11,name='Michelle')
        self.sources.append(dict(source_event_id='offsite',start=self.at(11,'09:00').isoformat(),
            end=self.at(11,'11:00').isoformat(),instructor='Brian Ennis',location='offsite',course_id='210549'))
        offers=self.payload()['offers']
        self.assertFalse(any(o['instructor']=='Brian Ennis' for o in offers))
        self.assertTrue(any(o['instructor']=='Michelle' for o in offers))

    def test_native_venue_alias_keeps_occupied_interval_through_publication(self):
        from scripts.block_start_time_selector import build_occupancy
        label = '4018 Shipyard Blvd, Room B, 910CPR Office'
        for instructor in ('Brian Ennis', 'Michelle'):
            with self.subTest(instructor=instructor):
                demand = dict(canonical_session_id='fixture-native-venue',
                    location_name=label, lead_instructor_name=instructor,
                    session_status='scheduled', external_course_id='359474',
                    start_at=self.at(11, '12:00').isoformat(),
                    end_at=self.at(11, '14:00').isoformat(),
                    count_available=True, active_registration_count=1)
                self.sources = build_occupancy(dict(location_resource_map=self.resources,
                    canonical_demand=dict(sessions=[demand])), {}, allow_unresolved=True)
                self.assertEqual(self.sources[0]['raw_location'], label)
                self.assertEqual(self.sources[0]['resource'], label)
                payload = self.payload()
                self.assertTrue(payload['offers'])
                for offer in payload['offers']:
                    start = aware(offer['date'] + 'T' + offer['startTime'] + ':00-04:00')
                    end = aware(offer['occupiedUntil'])
                    self.assertTrue(end <= self.at(11, '12:00') or start >= self.at(11, '14:00'))
                feed = public_selector_availability_payload(payload)
                self.assertTrue(feed['dates'])
                self.assertIn('fixture.test/enroll', json.dumps(feed))
                html = render_html(payload)
                self.assertTrue('/data/block-selector-availability/heartsaver.json' in html)

    def test_explicit_other_room_is_not_reassigned_to_primary(self):
        self.add(11, '12:00', '14:00', name='Michelle')
        self.sources[0]['resource'] = ':: Wilmington; Shipyard Blvd - A'
        self.assertIn('12:00', self.starts('329495'))

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
        self.assertIn('00:30',self.starts('210549'))
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
        internal_full=[o for o in result['offers'] if o['courseId']=='209809']
        # Preserve source/edge trace inside the calculated payload; only the compact
        # customer-facing selector must omit private provenance after #467.
        self.assertTrue(internal_full)
        self.assertTrue(all(o['sourceSessionIds'] and o['edgeIds'] and o['occupiedUntil']
                            for o in internal_full))
        full=[c for d in feed['dates'] for t in d['startTimes'] for c in t['courses'] if c['courseId']=='209809']
        self.assertEqual(len(full),len(internal_full))
        self.assertTrue(all('sourceSessionIds' not in c and 'edgeIds' not in c
                            and c['occupiedUntil'] and c['registrationUrl'] for c in full))
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

    def test_public_landscape_omits_private_occupied_geometry_but_keeps_internal_blocks(self):
        # A private seated appointment is a real operational blocker. Exact
        # private/unknown start and end times are NOT public selector geometry.
        internal = {
            'projected_sources': [
                dict(source_event_id='SECRET-PRIVATE-ID',visibility='private',
                     course_id='SECRET-PRIVATE-COURSE',kind='paid',
                     operational_has_active_seat=True,count_available=True,
                     active_registration_count=1,start='2026-11-22T15:13:00',
                     end='2026-11-22T17:17:00',resource='SECRET ROOM'),
                dict(source_event_id='SECRET-UNKNOWN-ID',
                     course_id='SECRET-UNKNOWN-COURSE',kind='paid',
                     count_available=True,active_registration_count=2,
                     start='2026-11-23T10:13:00',end='2026-11-23T12:17:00'),
                dict(source_event_id='PUBLIC-CLASS',visibility='public',
                     course_id='209806',kind='paid',count_available=True,
                     active_registration_count=1,
                     start='2026-11-24T10:00:00',end='2026-11-24T12:00:00'),
                dict(source_event_id='SECRET-UNLISTED-ELIGIBILITY',
                     visibility='public',public_direct_booking=False,
                     course_id='SECRET-NONJOINABLE-COURSE',
                     active_registration_count=1,count_available=True,
                     start='2026-11-25T16:13:00',end='2026-11-25T18:17:00'),
            ],
            'reports':[{'blocks':[dict(id='SECRET-BLOCK-ID',
                                       source_ids=['SECRET-PRIVATE-ID'],
                                       start='2026-11-22T15:13:00',
                                       end='2026-11-22T17:17:00')]}],
        }
        before = copy.deepcopy(internal)
        landscape = public_layered_landscape({'layeredDiagnostics':internal})
        self.assertEqual(len(landscape['sources']), 1)
        public = landscape['sources'][0]
        self.assertEqual((public['courseId'],public['role'],public['registeredCount']),
                         ('209806','anchor',1))
        self.assertEqual((public['start'],public['end']),
                         ('2026-11-24T10:00:00','2026-11-24T12:00:00'))
        self.assertNotIn('sourceId',public)
        self.assertEqual(landscape['occupiedBlocks'],[])
        serialized = json.dumps(landscape)
        for secret in ('SECRET-', '2026-11-22T15:13', '2026-11-22T17:17',
                       '2026-11-23T10:13','2026-11-23T12:17',
                       '2026-11-25T16:13','2026-11-25T18:17'):
            self.assertNotIn(secret,serialized)
        self.assertEqual(internal,before)

    def test_compact_public_availability_reports_redact_private_travel_and_room(self):
        # This suite runs in the Anchor policy CI: do not rely on Chrome-only
        # integration tests to gate privacy of public selector JSON.
        private = dict(
            reason='missing directional travel rule: PRIVATE CLIENT LOCATION->PRIVATE ROOM',
            instructor='SECRET STAFF', resource='SECRET ROOM',
            start='2026-12-06T00:00:00-05:00', end='2026-12-06T07:30:00-05:00',
            source_event_id='SECRET SOURCE',
        )
        raw = dict(dates=[], reconciliationIssues=[private, {
            'reason': 'unknown internal PRIVATE VENUE diagnostics',
            'start': '2026-12-10T18:30:00-05:00',
        }], layeredDiagnostics=dict(projected_sources=[dict(
            visibility='private', source_event_id='SECRET SOURCE',
            course_id='SECRET COURSE', resource='SECRET ROOM',
            start=private['start'], end=private['end'],
        )], reports=[]))
        before=copy.deepcopy(raw)
        feed=public_selector_availability_payload(raw)
        self.assertEqual(feed['reconciliationIssues'], [
            dict(reason='missing_directional_travel_rule',start='2026-12-06'),
            dict(reason='availability_coverage_unknown',start='2026-12-10'),
        ])
        self.assertEqual(feed['layeredLandscape']['sources'], [])
        self.assertEqual(feed['layeredLandscape']['occupiedBlocks'], [])
        self.assertNotIn(private['start'], json.dumps(feed))
        self.assertNotIn(private['end'], json.dumps(feed))
        redacted=json.dumps(feed)
        for private_value in ('PRIVATE CLIENT', 'PRIVATE VENUE', 'SECRET STAFF',
                              'SECRET ROOM', 'SECRET SOURCE', 'SECRET COURSE'):
            self.assertNotIn(private_value,redacted)
        # Public occupancy geometry is intentionally preserved; the detailed
        # travel failure is not. Exact source hours must not appear in the
        # public issue entry, but may still block a legitimate overlap.
        self.assertNotIn('end',feed['reconciliationIssues'][0])
        self.assertEqual(feed['reconciliationIssues'][0]['start'],'2026-12-06')
        self.assertEqual(raw,before)

    def test_public_offer_omits_internal_source_and_edge_provenance(self):
        # The full public JSON must not leak identifiers even when private
        # sources are already masked in layeredLandscape. Provenance remains
        # available to the internal calculation, but not the browser.
        raw = {
            'dates': [{'date': '2026-11-22', 'displayDate': 'Sunday, November 22, 2026',
                       'startTimes': [{'startTime': '13:00', 'displayStartTime': '1:00 PM',
                                       'courses': [dict(courseId='209806', courseName='BLS',
                                                        registrationUrl='https://example.com/register',
                                                        sourceSessionIds=['SECRET-PRIVATE-SESSION'],
                                                        edgeIds=['SECRET-PRIVATE-EDGE'],
                                                         attached_to_session_id='SECRET-PRIVATE-SESSION',
                                                         session_id='SECRET-PRIVATE-SESSION')]}]}],
            'layeredDiagnostics': {'projected_sources': [
                dict(source_event_id='SECRET-PRIVATE-SESSION', visibility='private',
                     course_id='SECRET-PRIVATE-COURSE', count_available=True,
                     active_registration_count=1, start='2026-11-22T15:00:00',
                     end='2026-11-22T17:00:00')], 'reports': []},
        }
        before = copy.deepcopy(raw)
        public = public_selector_availability_payload(raw)
        serialized = json.dumps(public)
        for secret in ('SECRET-PRIVATE-SESSION', 'SECRET-PRIVATE-EDGE',
                       'SECRET-PRIVATE-COURSE'):
            self.assertNotIn(secret, serialized)
        shown = public['dates'][0]['startTimes'][0]['courses'][0]
        self.assertEqual(shown['registrationUrl'], 'https://example.com/register')
        self.assertEqual(shown['courseId'], '209806')
        self.assertNotIn('sourceSessionIds', shown)
        self.assertNotIn('edgeIds', shown)
        self.assertNotIn('attached_to_session_id', shown)
        self.assertNotIn('session_id', shown)
        self.assertEqual(raw, before)

    def test_source_records_not_mutated_and_explicit_activation_required(self):
        self.add(11,'12:00','13:00',count=1)
        before=copy.deepcopy(self.sources);self.payload();self.assertEqual(self.sources,before)
        self.policy['mode']='shadow'
        with self.assertRaisesRegex(ValueError,'explicit'):self.calculation()

    def test_fall_back_lease_survives_repeated_hour_then_expires(self):
        self.windows[0].update(start='2026-11-03T09:00:00-05:00',
                               end='2026-11-03T15:00:00-05:00')
        self.now=aware('2026-11-01T01:56:29-04:00')
        self.coverage[0].update(start=self.windows[0]['start'],end=self.windows[0]['end'],
            observed_at='2026-11-01T05:56:28Z',valid_until='2026-11-01T06:11:28Z',
            freshness_minutes=15)
        payload=self.payload()
        self.assertTrue(payload['offers'])
        self.assertEqual(payload['validUntil'],'2026-11-01T06:11:28+00:00')
        # 01:05 EST follows 01:56 EDT despite its smaller wall-clock value.
        self.now=aware('2026-11-01T01:05:00-05:00')
        self.assertTrue(self.payload()['offers'])
        self.assertTrue(finalize(payload,self.now)['offers'])
        # 01:50 EST is later than expiry despite the earlier 01:56 EDT capture.
        self.now=aware('2026-11-01T01:50:00-05:00')
        self.assertFalse(self.payload()['offers'])
        self.assertFalse(finalize(payload,self.now)['offers'])

    def test_spring_forward_lease_uses_elapsed_minutes(self):
        self.windows[0].update(start='2027-03-15T09:00:00-04:00',
                               end='2027-03-15T15:00:00-04:00')
        self.coverage[0].update(start=self.windows[0]['start'],end=self.windows[0]['end'],
            observed_at='2027-03-14T06:55:00Z',valid_until='2027-03-14T07:10:00Z',
            freshness_minutes=15)
        self.now=aware('2027-03-14T03:05:00-04:00')
        self.assertTrue(self.payload()['offers'])
        self.now=aware('2027-03-14T03:10:00-04:00')
        self.assertFalse(self.payload()['offers'])

    def add_intake(self, day, count=None, **fields):
        row = self.add(day, '10:00', '12:30', cid='359474', name='UNKNOWN',
                       count=count, booking_source='confirmed_booking_intake',
                       registration_backend='landerware', session_status='scheduled',
                       stored_instructor_absent=True, instructor_unassigned=True,
                       operational_has_active_seat=True, visibility='private',
                       external_class_id=f'intake-external-{day}')
        row.update(fields)
        return row

    def attribute(self, approved=True):
        return apply_default_owner_occupancy(
            self.sources, 'Brian Ennis', self.room, self.now, self.coverage,
            lambda cid: approved and cid == '359474')

    def test_owner_default_is_effective_only_for_verified_intake(self):
        for day, count in zip(range(11, 16), [None, 1, None, 2, 1]):
            if day != 11:
                self.window(day)
            self.add_intake(day, count=count)
        originals = copy.deepcopy(self.sources)
        effective = self.attribute()
        self.assertEqual(self.sources, originals)
        self.assertEqual({r['instructor'] for r in effective}, {'Brian Ennis'})
        self.assertTrue(all(r['stored_instructor_absent'] for r in effective))
        self.assertEqual([r['active_registration_count'] for r in effective],
                         [None, 1, None, 2, 1])
        self.assertTrue(all(r['visibility'] == 'private' for r in effective))

    def test_owner_fallback_reads_legacy_naive_occupancy_but_not_naive_coverage(self):
        from scripts.block_start_time_selector import parse_dt
        from scripts.layered_selector_adapter import occupancy_instant
        row = self.add_intake(11)
        row.update(start=parse_dt(row["start"]), end=parse_dt(row["end"]))
        self.assertEqual(self.attribute()[0]["instructor"], "Brian Ennis")
        self.coverage[0]["start"] = parse_dt(self.coverage[0]["start"])
        self.assertIs(self.attribute()[0], row)
        for ambiguous in ("2026-11-01T01:30:00", "2027-03-14T02:30:00"):
            with self.assertRaises(ValueError):
                occupancy_instant(ambiguous)
        self.assertNotEqual(occupancy_instant("2026-11-01T01:30:00-04:00"),
                            occupancy_instant("2026-11-01T01:30:00-05:00"))

    def test_no_fallback_without_fresh_proof_cert_or_true_unassignment(self):
        row = self.add_intake(11)
        self.assertIs(self.attribute(approved=False)[0], row)
        for change in [
            {'stored_instructor_absent': False}, {'instructor_unassigned': False, 'instructor':'Amy Arnold'},
            {'operational_has_active_seat': False}, {'session_status':'completed'},
            {'session_status':'canceled'}, {'location_resolution':None}, {'visibility':'public'},
        ]:
            self.sources[:] = [{**row, **change}]
            self.assertIs(self.attribute()[0], self.sources[0])
        self.sources[:] = [row]
        self.coverage[0]['valid_until'] = self.now.isoformat()
        self.assertIs(self.attribute()[0], row)

    def test_distinct_room_and_instructor_conflicts_stay_unassigned_but_exact_mirror_dedups(self):
        row = self.add_intake(11)
        other = dict(row, source_file='docs/data/schedule_future.json',
                     instructor='Brian', instructor_unassigned=False)
        self.sources.append(other)
        self.assertEqual(self.attribute()[0]['instructor'], 'Brian Ennis')
        for update in [
            {'instructor':'Amy Arnold'}, {'external_class_id':'other-class'},
            {'resource':'an offsite facility'}, {'end':None}, {'course_id':'another-course'},
        ]:
            self.sources[1] = {**other, **update}
            self.assertIs(self.attribute()[0], row)

    def test_owner_effective_anchor_keeps_bookends_without_join_or_private_identifiers(self):
        self.policy['require_verified_day_gravity'] = True
        row = self.add_intake(11, source_event_id='PRIVATE-OWNER-INTAKE')
        self.sources = self.attribute()
        seat = dict(offerType='seated_class', session_id=row['external_class_id'],
                    instructor='Brian Ennis', date='2026-10-11', startTime='10:00',
                    courseId='359474', registrationUrl='https://fixture.test/PRIVATE-OWNER-LINK')
        payload = self.payload([seat])
        offers = payload['offers']
        self.assertTrue(any(o['scheduleRole'] == 'barnacle' and o['startTime'] == '12:30'
                            for o in offers))
        self.assertFalse(any(o['offerType'] == 'seated_class' or o['scheduleRole'] == 'open_day'
                             for o in offers))
        self.assertFalse(any(o['courseId'] == '359474' for o in offers))
        self.assertNotIn('PRIVATE-OWNER', json.dumps(public_selector_availability_payload(payload)))


if __name__=='__main__':unittest.main()
