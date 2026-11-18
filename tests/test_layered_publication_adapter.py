import copy
import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from scripts.layered_publication_adapter import calculate, publish, project_sources, finalize, public_calculation_diagnostics
from scripts.layered_selector_adapter import aware, build_shadow
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
            lambda s,c:[],seated)

    def starts(self,cid='209809',day=None):
        return {o['startTime'] for o in self.payload()['offers'] if o['courseId']==cid and (day is None or o['date']==f'2026-10-{day:02d}')}

    def test_clear_day_lists_every_qualified_course_on_half_hour_grid(self):
        # An eight-hour-plus free period must not silently switch to hourly
        # retail starts. Owner doctrine #16 requires 30-minute clear-day offers.
        self.windows=[];self.coverage=[];self.sources=[]
        self.window(11,'08:00','18:00',next_day=False)
        for course in self.courses:
            cid=course['course_id']
            last=18 if course['kind']=='skills' else 15  # 60m / 150m occupied
            expected={(self.at(11,'08:00')+timedelta(minutes=30*i)).strftime('%H:%M')
                      for i in range(last+1)}
            with self.subTest(course=cid):
                self.assertEqual(self.starts(cid,day=11),expected)
        self.assertTrue(all(row['step_minutes']==30
            for report in self.calculation()['reports']
            for row in report['free_intervals']))

    def test_canonical_private_seat_course_key_preserves_family_gravity_without_public_join(self):
        # Real native appointments can have only a durable course_key; the
        # legacy external course ID and public roster proof are unavailable.
        self.windows=[];self.coverage=[];self.sources=[]
        self.window(11,'08:00','18:00',next_day=False)
        self.courses[-1]['course_key']='aha_bls_provider_renewal'
        private=self.add(11,'12:00','14:30',cid=None,count=None,
            visibility='private',course_key='aha_bls_provider_renewal',
            operational_has_active_seat=True)
        private['count_available']=False
        private['active_registration_count']=None
        calculation=self.calculation()
        report=calculation['reports'][0]
        paid=[r for r in report['source_truth'] if r.get('id')==private['source_event_id']]
        self.assertEqual(len(paid),1)
        self.assertEqual((paid[0]['kind'],paid[0]['course']),('paid','359474'))
        self.assertTrue(any(r.get('course')=='359474' and
            'full_course_already_paid_seated' in r.get('reasons',[])
            for r in report['rejected']))
        public=public_calculation_diagnostics(calculation)
        projected=[x for x in public['projected_sources'] if x.get('source_file')=='canonical_class_sessions']
        self.assertEqual(len(projected),1)
        self.assertNotIn('course_id',projected[0])
        self.assertNotIn('operational_has_active_seat',projected[0])
        self.assertNotEqual(projected[0].get('source_event_id'),private['source_event_id'])

        # Ambiguous catalog identity must NOT guess a course/family, but the
        # private paid occupied interval remains a physical room constraint.
        self.courses.append(dict(self.courses[-1],course_id='999999'))
        unresolved=self.calculation()['reports'][0]
        paid=[r for r in unresolved['source_truth'] if r.get('id')==private['source_event_id']]
        self.assertEqual(len(paid),1)
        self.assertEqual((paid[0]['kind'],paid[0]['course']),('paid',None))
        self.assertTrue(any(r.get('id')==private['source_event_id']
            for r in unresolved['normalized_occupancy']))

    def test_repeated_skills_growth_and_full_class_enlarges_block(self):
        self.add(11,'12:00','13:00',count=1)
        for cid in ['210549','329495']: self.assertEqual(self.starts(cid),{'11:00','13:00'})
        self.add(11,'13:00','14:00','329495',count=1)
        for cid in ['210549','329495']: self.assertEqual(self.starts(cid),{'11:00','14:00'})
        self.add(11,'11:00','12:00',count=1)
        self.add(11,'14:00','16:30','209809',count=1)
        for cid in ['210549','329495']: self.assertEqual(self.starts(cid),{'10:00','16:30'})
        self.assertEqual(len(self.calculation()['reports'][0]['blocks']),1)

    def test_oct11_13_14_full_heartsaver_from_shared_room_edges(self):
        self.add(11,'17:00','19:00','359474',count=1)
        self.window(13,'07:45','15:00',next_day=False)
        self.window(13,'17:30','00:00')
        self.add(13,'14:00','18:00','359474',name='Amy',count=1)
        self.window(14,'17:30','00:00')
        self.add(14,'17:30','19:30','329495',count=1)
        self.assertEqual(self.starts(day=11),{'14:30','19:00'})
        self.assertEqual(self.starts(day=13),{'11:30','18:00'})
        self.assertEqual(self.starts(day=14),{'19:30'})
        self.assertTrue(all(o['schedulerConsumptionMinutes']==150 for o in self.payload()['offers'] if o['courseId']=='209809'))

    def test_oct12_conflicts_eliminate_full_class_edges(self):
        self.windows=[];self.coverage=[];self.window(12)
        self.add(12,'09:00','11:00','359474',name='Michelle',count=1)
        self.add(12,'12:00','13:00','210549',count=1)
        self.add(12,'17:00','19:00','359474',name='Michelle',count=1)
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
        self.assertNotIn('12:00',self.starts('329495'))
        self.assertTrue(self.starts('329495'), 'zero-seat source blocks time but not the full day')
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
                row=self.add(11,'12:00','13:00',cid=cid,count=1)
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
        row=self.add(14,'17:30','19:30',cid='329495',count=1)
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
        row=self.add(11,'11:45','13:45',cid='209806',count=1)
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

    def test_public_diagnostics_redact_private_record_fields(self):
        # Source provenance can be canonical, intake, or external. The public
        # report must never reveal a private paid/registered state through
        # either source diagnostics or normalized occupied blocks.
        private=dict(source_event_id='private-record',source_file='canonical_class_sessions',
                     visibility='private',kind='paid',count_available=True,
                     active_registration_count=3,operational_has_active_seat=True,
                     registration_url='https://private.invalid/seat',
                     customer_email='private@example.invalid',customer_id='private-customer')
        unlisted=dict(source_event_id='unlisted-record',source_file='confirmed_booking_intake',
                      visibility='unlisted',kind='seated',count_available=True,
                      active_registration_count=1,operational_has_active_seat=True)
        public=dict(source_event_id='public-record',source_file='canonical_class_sessions',
                    visibility='public',count_available=True,active_registration_count=2)
        internal=dict(projected_sources=[private,unlisted,public],
            reports=[dict(normalized_occupancy=[
                dict(evidence='canonical_class_sessions',kind='paid',headcount=3),
                dict(evidence='confirmed_booking_intake',kind='seated',headcount=1),
                dict(evidence='schedule_future',kind='planted',headcount=None)])])
        result=public_calculation_diagnostics(internal)
        private_out,unlisted_out,public_out=result['projected_sources']
        for source in (private_out,unlisted_out):
            self.assertFalse(any(field in source for field in
                ('registration_url','customer_email','customer_id','active_registration_count',
                 'operational_has_active_seat')),
                'public diagnostics must not reveal even boolean private-seat presence')
            self.assertEqual(source['kind'],'occupied')
        self.assertEqual(public_out['active_registration_count'],2)
        self.assertEqual(private_out['visibility'],'private')
        self.assertNotIn('private-record',json.dumps(result))
        self.assertNotIn('unlisted-record',json.dumps(result))
        for occupied in result['reports'][0]['normalized_occupancy']:
            self.assertNotIn('headcount',occupied)
            self.assertNotIn(occupied['kind'],('paid','seated'),
                'public normalized occupancy must not disclose private gravity')
        # Only the public serialization is redacted; internal proof remains
        # paid and available for actual collision/Anchor calculations.
        self.assertEqual(internal['projected_sources'][0]['kind'],'paid')
        self.assertEqual(internal['reports'][0]['normalized_occupancy'][0]['kind'],'paid')

    def test_rejected_existing_class_and_expired_offer_strip_private_payloads(self):
        # Rejected existing-class rows enter the public report directly. A
        # private booking URL or nested source metadata may never be copied
        # into the customer feed just because a candidate was rejected.
        seated=dict(session_id='unmatched-existing',date='2026-10-11',
            startTime='12:00',courseId='359474',courseName='BLS Renewal',
            offerType='seated_class',location=self.room,
            registrationUrl='https://private.invalid/token-SECRET-BOOKING',
            sourceAvailabilityBlock=dict(sessionId='SECRET-SESSION-ID',
                                         studentEmail='SECRET-EMAIL'),
            sourceSessionIds=['SECRET-SOURCE-ID'],edgeIds=['SECRET-EDGE-ID'],
            participantName='SECRET-PARTICIPANT')
        payload=self.payload([seated])
        self.assertIn('unverified_existing_class_consumption_end',
                      payload['rejectionReasonCounts'])
        rejected=next(row for row in payload['rejectedCourseStartTimes']
                      if 'unverified_existing_class_consumption_end' in row.get('reasons',[]))
        self.assertEqual((rejected['date'],rejected['startTime'],rejected['courseId']),
                         ('2026-10-11','12:00','359474'))
        serialized=json.dumps(payload)
        for secret in ('SECRET-BOOKING','SECRET-SESSION-ID','SECRET-EMAIL',
                       'SECRET-SOURCE-ID','SECRET-EDGE-ID','SECRET-PARTICIPANT'):
            self.assertNotIn(secret,serialized)

        # The finalizer can append a new rejection when a previously accepted
        # dynamic offer's lease expires; that path must obey the same boundary.
        fresh=self.payload()
        self.assertTrue(fresh['offers'])
        fresh['offers'][0]['sourceAvailabilityBlock']={'customer':'SECRET-EXPIRED-CUSTOMER'}
        expired=finalize(fresh,self.now+timedelta(hours=2))
        self.assertFalse(expired['offers'])
        self.assertIn('expired_or_missing_scoped_lease',
                      [reason for row in expired['rejectedCourseStartTimes']
                       for reason in row.get('reasons',[])])
        self.assertNotIn('SECRET-EXPIRED-CUSTOMER',json.dumps(expired))


    def test_unknown_noncanonical_visibility_never_publishes_roster_or_paid_role(self):
        # A source with absent visibility is not public merely because it
        # came from an intake path rather than canonical_class_sessions.
        unknown=dict(source_event_id='unknown-intake',source_file='confirmed_booking_intake',
            kind='paid',count_available=True,active_registration_count=1,
            operational_has_active_seat=True,
            start=self.at(11,'12:00').isoformat(),end=self.at(11,'14:00').isoformat(),
            course_id='359474',resource=self.room)
        public=dict(unknown,source_event_id='verified-public',visibility='public')
        internal=dict(projected_sources=[unknown,public],reports=[])
        sanitized=public_calculation_diagnostics(internal)
        private_report=sanitized['projected_sources'][0]
        self.assertNotIn('operational_has_active_seat',private_report)
        self.assertNotIn('active_registration_count',private_report)
        self.assertFalse(private_report['count_available'])
        self.assertEqual(private_report['kind'],'occupied')
        landscape=public_layered_landscape(dict(layeredDiagnostics=internal))
        unknown_landscape,public_landscape=landscape['sources']
        self.assertEqual(unknown_landscape['role'],'blocking')
        self.assertIsNone(unknown_landscape['courseId'],
                          'private operational occupancy must not advertise its course identity')
        self.assertEqual(public_landscape['courseId'],'359474')
        self.assertFalse(unknown_landscape['countAvailable'])
        self.assertIsNone(unknown_landscape['registeredCount'])
        self.assertEqual(public_landscape['role'],'anchor')
        self.assertTrue(public_landscape['countAvailable'])
        self.assertEqual(public_landscape['registeredCount'],1)
        # Redaction applies even to the unsanitized internal input; internal
        # proof itself remains unchanged and usable for occupancy gravity.
        self.assertEqual(internal['projected_sources'][0]['kind'],'paid')
        self.assertTrue(internal['projected_sources'][0]['operational_has_active_seat'])

    def test_same_interval_legacy_mirror_cannot_erase_private_canonical_seat(self):
        # Source identity, not identical instructor/room/clock geometry, must
        # decide deduplication. Public roster proof remains unavailable.
        self.sources=[]
        legacy=self.add(11,'12:00','13:00',cid='359474',count=None)
        legacy.update(source_event_id='legacy-occurrence',source_file='schedule_future')
        canonical=dict(legacy,source_event_id='canonical-occurrence',
                       source_file='canonical_class_sessions',
                       operational_has_active_seat=True,instructor_unassigned=True,
                       canonical_recorded_registration_count=1,
                       registration_url='https://private.invalid/not-a-public-booking')
        second_legacy=dict(legacy,source_event_id='other-real-occurrence')
        def shadow(rows):
            return build_shadow(self.windows,rows,self.courses,self.policy,self.resources,
                self.now,lambda w:(w['start'],w['end']),lambda w,c:True,
                lead_minutes=0,commitment_coverage=self.coverage,
                shared_room_edges=True)
        for rows in ([legacy,canonical],[canonical,legacy]):
            with self.subTest(first=rows[0]['source_file']):
                occupied=shadow(rows)['normalized_occupancy']
                by_id={row['id']:row for row in occupied}
                self.assertEqual(by_id['canonical-occurrence']['kind'],'paid')
                self.assertEqual(by_id['legacy-occurrence']['kind'],'planted')
                self.assertTrue(any(row['kind']=='hold' and
                    row['id'].startswith('unassigned-') for row in occupied))
        # Exact same-source ingestion is deduped, distinct occurrences survive.
        occupied=shadow([legacy,legacy])['normalized_occupancy']
        self.assertEqual(sum(row['id']=='legacy-occurrence' for row in occupied),1)
        occupied=shadow([legacy,second_legacy])['normalized_occupancy']
        self.assertEqual({row['id'] for row in occupied},
                         {'legacy-occurrence','other-real-occurrence'})
        self.sources=[legacy,canonical]
        public=self.payload()
        self.assertNotIn('private.invalid',json.dumps(public))
        self.assertFalse(any(row.get('offerType')=='seated_class'
                             for row in public['offers']))

    def test_private_paid_occurrence_conflicting_public_empty_class_is_not_joinable(self):
        # A later public zero-seat container is not proof that a distinct
        # private registered occurrence at the same start has become public.
        # Dec 1 real-world pattern: same BLS, venue, start; different IDs.
        self.windows=[];self.coverage=[];self.sources=[]
        self.window(11,'08:00','18:00',next_day=False)
        private=self.add(11,'11:00','13:00',cid='359474',count=None)
        private.update(source_event_id='private-occurrence',visibility='private',
            location=':: Wilmington; Shipyard Blvd',operational_has_active_seat=True,
            instructor_unassigned=True,source_file='canonical_class_sessions')
        public=dict(private,source_event_id='public-empty-offer',
            external_class_id='14996400',visibility='public',count_available=False,
            active_registration_count=None,operational_has_active_seat=False,
            instructor_unassigned=False,source_file='canonical_class_sessions')
        published=dict(session_id='14996400',date='2026-10-11',
            startTime='11:00',courseId='359474',courseName='BLS Renewal',
            offerType='seated_class',location=':: Wilmington; Shipyard Blvd',
            registrationUrl='https://enroll.example.test/public-empty-offer')
        for sources in ([private,public],[public,private]):
            with self.subTest(first=sources[0]['source_event_id']):
                self.sources=sources
                calc=self.calculation()
                occupied=calc['reports'][0]['normalized_occupancy']
                self.assertTrue(any(o['kind']=='paid'
                    and o['id']=='private-occurrence' for o in occupied))
                self.assertTrue(any(o['kind']=='hold'
                    and o['id'].startswith('unassigned-') for o in occupied))
                payload=self.payload([published])
                self.assertFalse(any(o.get('offerType')=='seated_class'
                    for o in payload['offers']))
                self.assertIn('unreconciled_private_committed_public_start',
                              payload['rejectionReasonCounts'])
                self.assertFalse(any(o.get('scheduleRole')=='open_day'
                    for o in payload['offers']))
                self.assertFalse(any('private-occurrence' in str(o.get('registrationUrl',''))
                    for o in payload['offers']))
                public_sources=public_selector_availability_payload(payload)['layeredLandscape']['sources']
                private_view=next(o for o in public_sources if o.get('sourceId') is None)
                self.assertEqual(private_view['role'],'blocking')
                self.assertFalse(private_view['countAvailable'])
                self.assertIsNone(private_view['registeredCount'])
        # Even when the later public container has verified zero enrollment,
        # it cannot displace the private commitment or become a seated Anchor.
        public['count_available']=True;public['active_registration_count']=0
        self.sources=[public,private]
        payload=self.payload([published])
        self.assertFalse(any(o.get('offerType')=='seated_class'
            for o in payload['offers']))
        self.assertIn('unreconciled_private_committed_public_start',
                      payload['rejectionReasonCounts'])

        # The live canonical-demand endpoint supplies course_key but can omit
        # external_course_id (Dec 1 private/public BLS collision). A verified
        # private registration must still protect the same unresolved room.
        public['count_available']=False
        public['active_registration_count']=None
        private['course_id']=None
        private['course_key']='aha-bls-provider'
        for sources in ([private, public], [public, private]):
            with self.subTest(missing_external_course_id=True,
                              first=sources[0]['source_event_id']):
                self.sources=sources
                payload=self.payload([published])
                self.assertFalse(any(o.get('offerType')=='seated_class'
                    for o in payload['offers']))
                self.assertIn('unreconciled_private_committed_public_start',
                              payload['rejectionReasonCounts'])
        # Even when the external catalog labels a course differently, a
        # distinct same-room start cannot bypass a real private commitment.
        private['course_id']='different-catalog-course'
        self.sources=[public,private]
        payload=self.payload([published])
        self.assertIn('unreconciled_private_committed_public_start',
                      payload['rejectionReasonCounts'])

    def test_private_partial_overlap_rejects_distinct_public_seated_starts(self):
        # Real records can start at different times and still consume the
        # same room. A seat cannot be sold because start timestamps differ.
        self.windows=[];self.coverage=[];self.sources=[]
        self.window(11,'08:00','18:00',next_day=False)
        private=self.add(11,'12:00','14:00',cid='359474',count=None)
        private.update(source_event_id='canonical-private',visibility='private',
            course_id=None,course_key='aha-bls-provider',
            operational_has_active_seat=True,instructor_unassigned=True,
            location=':: Wilmington; Shipyard Blvd')
        public=self.add(11,'11:00','13:00',cid='359474',count=None)
        public.update(source_event_id='public-seated',visibility='public',
            location=':: Wilmington; Shipyard Blvd',
            instructor_unassigned=False)
        seated=dict(session_id='public-seated',date='2026-10-11',startTime='11:00',
            courseId='359474',courseName='BLS Renewal',offerType='seated_class',
            location=':: Wilmington; Shipyard Blvd',
            registrationUrl='https://example.test/register/public-seated')
        for sequence in ([private,public],[public,private]):
            with self.subTest(first=sequence[0]['source_event_id']):
                self.sources=sequence
                payload=self.payload([seated])
                self.assertFalse(any(o.get('offerType')=='seated_class'
                    for o in payload['offers']))
                self.assertIn('unreconciled_private_committed_public_start',
                    payload['rejectionReasonCounts'])
                self.assertNotIn('canonical-private',json.dumps(payload),
                    'no public selector field may reveal a private occurrence ID')
        # The same collision also exists when the private class begins first.
        private['start']=self.at(11,'10:00').isoformat()
        private['end']=self.at(11,'11:30').isoformat()
        self.sources=[private,public]
        self.assertFalse(any(o.get('offerType')=='seated_class'
            for o in self.payload([seated])['offers']))
        # Touching is legal; room consumption has ended before the offer.
        public['start']=self.at(11,'14:00').isoformat()
        public['end']=self.at(11,'16:00').isoformat()
        seated['startTime']='14:00'
        self.assertTrue(any(o.get('offerType')=='seated_class'
            for o in self.payload([seated])['offers']))

    def test_unknown_seated_end_and_cross_midnight_overlap_fail_closed(self):
        # An old seated URL with no verifiable occupied end is not a
        # legitimate public option; do not guess that midnight ends its class.
        self.windows=[];self.coverage=[];self.sources=[]
        self.window(11,'20:00','04:00')
        seated=dict(session_id='legacy-unmatched',date='2026-10-11',
            startTime='23:30',courseId='359474',courseName='BLS Renewal',
            offerType='seated_class',location=':: Wilmington; Shipyard Blvd',
            registrationUrl='https://example.test/legacy-unmatched')
        unknown=self.payload([seated])
        self.assertFalse(any(o.get('offerType')=='seated_class'
            for o in unknown['offers']))
        self.assertIn('unverified_existing_class_consumption_end',
            unknown['rejectionReasonCounts'])
        self.assertTrue(any(o.get('scheduleRole')=='open_day'
            for o in unknown['offers']),
            'an unverified seated link must not sterilize unrelated open hours')

        # Explicit duration makes an overnight candidate evaluable. The
        # private class starts the NEXT date while this candidate is running.
        seated['schedulerConsumptionMinutes']=90
        private=self.add(12,'00:00','01:00',cid='359474',count=None)
        private.update(source_event_id='private-after-midnight',
            visibility='private',operational_has_active_seat=True,
            instructor_unassigned=True)
        overlap=self.payload([seated])
        self.assertFalse(any(o.get('offerType')=='seated_class'
            for o in overlap['offers']))
        self.assertIn('unreconciled_private_committed_public_start',
            overlap['rejectionReasonCounts'])
        # Adjacent at 01:00 is a legal half-open boundary.
        private['start']=self.at(12,'01:00').isoformat()
        private['end']=self.at(12,'02:00').isoformat()
        touching=self.payload([seated])
        self.assertTrue(any(o.get('offerType')=='seated_class'
            for o in touching['offers']))

    def test_independent_room_exception_requires_two_verified_assignments(self):
        self.windows=[];self.coverage=[];self.sources=[]
        self.window(11,'08:00','18:00',next_day=False)
        private=self.add(11,'12:00','14:00',cid='359474',count=None)
        private.update(source_event_id='private-room-a',visibility='private',
            operational_has_active_seat=True,resource=':: Wilmington; Shipyard Blvd - A',
            instructor='Michelle',instructor_unassigned=False,
            resource_assignment_verified=True,instructor_assignment_verified=True)
        public=self.add(11,'11:00','13:00',cid='359474',count=None)
        public.update(source_event_id='public-room-b',visibility='public',
            resource=':: Wilmington; Shipyard Blvd - B',
            instructor='Brian Ennis',instructor_unassigned=False,
            resource_assignment_verified=True,instructor_assignment_verified=True)
        seated=dict(session_id='public-room-b',date='2026-10-11',startTime='11:00',
            courseId='359474',courseName='BLS Renewal',offerType='seated_class',
            location=':: Wilmington; Shipyard Blvd',
            registrationUrl='https://example.test/register/public-room-b')
        self.sources=[private,public]
        self.assertTrue(any(o.get('offerType')=='seated_class'
            for o in self.payload([seated])['offers']),
            'two explicitly verified distinct rooms and instructors remain legal')
        for field in ('resource_assignment_verified','instructor_assignment_verified'):
            private[field]=False
            self.assertFalse(any(o.get('offerType')=='seated_class'
                for o in self.payload([seated])['offers']),field)
            private[field]=True
        private['instructor']='Brian Ennis'
        self.assertFalse(any(o.get('offerType')=='seated_class'
            for o in self.payload([seated])['offers']),
            'different rooms never override an instructor conflict')

    def test_unverified_existing_course_blocks_time_not_whole_evening(self):
        # An unknown Enrollware roster is not evidence of a paid day Anchor.
        # Preserve the hard occupied interval while leaving independent legal
        # evening availability subject to the usual instructor/room checks.
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11,'19:00','22:00',next_day=False)
        row=self.add(11,'11:00','13:00',cid='359474',count=None)
        unknown=self.payload()
        evening=[o for o in unknown['offers'] if o['date']=='2026-10-11'
                 and o['instructor']=='Brian Ennis' and o.get('scheduleRole')=='open_day']
        self.assertTrue(evening, 'unknown demand must not invent a daywide Anchor')

        row['active_registration_count']=1
        row['count_available']=True
        proven=self.payload()
        self.assertFalse([o for o in proven['offers'] if o['date']=='2026-10-11'
                          and o['instructor']=='Brian Ennis'
                          and o.get('scheduleRole')=='open_day'])
        self.assertTrue(any(s['kind']=='paid' for s in self.calculation()['reports'][0]['normalized_occupancy']),
                        'internal calculation must preserve verified paid Anchor gravity')
        self.assertFalse(any(s.get('kind')=='paid' for s in
                         proven['layeredDiagnostics']['reports'][0]['normalized_occupancy']),
                         'public diagnostics must not disclose private paid-seat evidence')

    def test_unknown_existing_seat_not_day_anchor_until_proven(self):
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11,'19:00','22:00',next_day=False)
        row=self.add(11,'11:00','13:00',cid='359474',count=None)
        seated=dict(session_id=row['source_event_id'],date='2026-10-11',startTime='11:00',
                    courseId='359474',courseName='Unverified legacy session',
                    offerType='seated_class',instructor='Brian Ennis')
        before=self.payload([seated])
        self.assertTrue(any(o.get('offerType')=='seated_class' for o in before['offers']))
        self.assertTrue(any(o.get('scheduleRole')=='open_day' for o in before['offers']),
                        'a displayed unverified class is not itself canonical seat proof')
        row['active_registration_count']=1;row['count_available']=True
        after=self.payload([seated])
        self.assertFalse(any(o.get('scheduleRole')=='open_day'
                             and o.get('instructor')=='Brian Ennis' for o in after['offers']))
        self.assertTrue(any(o.get('offerType')=='seated_class' for o in after['offers']))

    def test_one_seat_private_class_anchors_operationally_without_public_join_link(self):
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11,'08:00','18:00',next_day=False)
        private = self.add(11,'12:00','14:00',cid='359474',count=1,
                           visibility='private',public_direct_booking=False)
        calculated = self.calculation()
        source = next(s for s in calculated['projected_sources']
                      if s.get('source_event_id') == private['source_event_id'])
        self.assertTrue(source['count_available'])
        self.assertEqual(source['active_registration_count'],1)
        offers = self.payload()['offers']
        self.assertTrue([o for o in offers if o.get('scheduleRole') == 'barnacle'],
                        'proved operational first seat should create compatible bookends')
        self.assertFalse([o for o in offers if o.get('scheduleRole') == 'open_day'],
                         'paid Anchor collapses unattached open-day alternatives')
        self.assertFalse([o for o in offers if o.get('offerType') == 'seated_class'],
                         'private registration must not become a public joinable class')
        private_source=public_selector_availability_payload(self.payload())['layeredLandscape']['sources'][0]
        self.assertEqual(private_source['role'],'blocking')
        self.assertFalse(private_source['countAvailable'])
        self.assertIsNone(private_source['registeredCount'])
        self.assertFalse([o for o in offers
                          if private['source_event_id'] in str(o.get('registrationUrl',''))],
                         'private class identity must never be used as registration URL')
        for offer in offers:
            self.assertTrue(offer['startTime'] < '12:00'
                            or offer['startTime'] >= '14:00',
                            'another public class must not start within private occupancy')

    def test_canonical_private_intake_proves_operational_anchor_not_public_seat(self):
        from scripts.block_start_time_selector import build_occupancy
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11,'08:00','18:00',next_day=False)
        demand=dict(canonical_session_id='synthetic-private-intake',
            source='confirmed_booking_intake',session_status='scheduled',
            visibility='private',registration_status='closed',
            lead_instructor_name='Brian Ennis',lead_instructor_id='synthetic-instructor',
            location_name=':: Wilmington; Shipyard Blvd',
            external_course_id='359474',external_class_id='14925865',
            start_at=self.at(11,'12:00').isoformat(),end_at=self.at(11,'14:00').isoformat(),
            count_available=False,active_registration_count=None,
            canonical_recorded_registration_count=1)
        self.sources=build_occupancy(dict(location_resource_map=self.resources,
            canonical_demand=dict(sessions=[demand])),{},allow_unresolved=True)
        source=self.sources[0]
        self.assertTrue(source['operational_has_active_seat'])
        self.assertFalse(source['count_available'])
        self.assertIsNone(source['active_registration_count'])
        projected=self.calculation()['projected_sources'][0]
        self.assertTrue(projected['operational_has_active_seat'])
        proven_payload=self.payload()
        proven_landscape=public_selector_availability_payload(proven_payload)['layeredLandscape']
        self.assertEqual(proven_landscape['sources'][0]['role'],'blocking',
                         'private occupied class must not expose its registered Anchor status')
        self.assertFalse(proven_landscape['sources'][0]['countAvailable'])
        self.assertIsNone(proven_landscape['sources'][0]['registeredCount'])
        offers=proven_payload['offers']
        self.assertTrue(any(o.get('scheduleRole')=='barnacle' for o in offers))
        self.assertFalse(any(o.get('scheduleRole')=='open_day' for o in offers))
        self.assertFalse(any(o.get('offerType')=='seated_class' for o in offers))
        self.assertFalse(any('synthetic-private-intake' in str(o.get('registrationUrl',''))
                             or '14925865' in str(o.get('registrationUrl','')) for o in offers))
        for offer in offers:
            start=aware(offer['date']+'T'+offer['startTime']+':00-04:00')
            end=aware(offer['occupiedUntil'])
            self.assertTrue(end<=self.at(11,'12:00') or start>=self.at(11,'14:00'))
        # Unverified/legacy source alone cannot become paid gravity.
        demand['source']='enrollware_history'
        self.sources=build_occupancy(dict(location_resource_map=self.resources,
            canonical_demand=dict(sessions=[demand])),{},allow_unresolved=True)
        self.assertFalse(self.sources[0]['operational_has_active_seat'])
        unknown_payload=self.payload()
        self.assertEqual(public_selector_availability_payload(unknown_payload)
                         ['layeredLandscape']['sources'][0]['role'],'blocking')
        self.assertTrue(any(o.get('scheduleRole')=='open_day' for o in unknown_payload['offers']))
        # A human source label never fills in a missing canonical instructor ID.
        demand['source']='confirmed_booking_intake'
        demand['lead_instructor_id']=None
        self.sources=build_occupancy(dict(location_resource_map=self.resources,
            canonical_demand=dict(sessions=[demand])),{},allow_unresolved=True)
        self.assertTrue(self.sources[0]['instructor_unassigned'])

    def test_course_key_only_private_seat_scopes_day_anchor_to_verified_instructor(self):
        # Real canonical endpoint has course_key, but may have no catalog
        # course_id/external_course_id. Publication must not lose the first seat.
        # This isolates the publish-time day collapse from hard overlap checks;
        # the final assertion also checks actual occupied-interval safety.
        from scripts.block_start_time_selector import build_occupancy
        self.windows=[];self.coverage=[];self.sources=[]
        self.window(11,'08:00','18:00',next_day=False)
        free_calculation=self.calculation()
        self.assertTrue(any(o.get('scheduleRole')=='open_day' for o in self.payload()['offers']))
        for assigned in (True,False):
            with self.subTest(assigned=assigned):
                demand=dict(canonical_session_id='private-key-only',
                    course_key='aha-bls-provider',external_course_id=None,
                    source='confirmed_booking_intake',session_status='scheduled',
                    visibility='private',lead_instructor_name='Brian Ennis',
                    lead_instructor_id='verified-brian-id' if assigned else None,
                    location_name=':: Wilmington; Shipyard Blvd',
                    start_at=self.at(11,'12:00').isoformat(),
                    end_at=self.at(11,'14:00').isoformat(),
                    canonical_recorded_registration_count=1,
                    count_available=False,active_registration_count=None)
                source=build_occupancy(dict(location_resource_map=self.resources,
                    canonical_demand=dict(sessions=[demand])),{},allow_unresolved=True)[0]
                self.assertEqual(source['course_key'],'aha-bls-provider')
                self.assertFalse(source['course_id'])
                self.assertTrue(source['operational_has_active_seat'])
                self.assertEqual(source['instructor_unassigned'],not assigned)
                # Deliberately reuse clear-day proposals to isolate the
                # publish-time Anchor filter. A real pipeline also recalculates
                # conflicts before publish, as checked below.
                probe=copy.deepcopy(free_calculation)
                probe['projected_sources']=[source]
                result=publish(probe,self.page,self.courses,self.windows,self.now,
                    lambda w,s,c:('fixture-day','fixture-container',
                        f'https://fixture.test/enroll?courseId={c}&startTime={s:%H:%M}',None),
                    lambda s,c:[],())
                roles=[o.get('scheduleRole') for o in result['offers']]
                if assigned:
                    self.assertNotIn('open_day',roles)
                    self.assertIn('anchored_day_requires_attached_offer',
                                  result['rejectionReasonCounts'])
                else:
                    # Unknown instructor is a real room/time hold, not proof
                    # that every other instructor has an occupied whole day.
                    self.assertIn('open_day',roles)
                    self.assertNotIn('anchored_day_requires_attached_offer',
                                     result['rejectionReasonCounts'])
                self.sources=[source]
                actual=self.payload()
                self.assertFalse(any(o.get('offerType')=='seated_class'
                                     for o in actual['offers']))
                for offer in actual['offers']:
                    start=aware(offer['date']+'T'+offer['startTime']+':00-04:00')
                    end=aware(offer['occupiedUntil'])
                    self.assertTrue(end<=self.at(11,'12:00') or start>=self.at(11,'14:00'))

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
            end=self.at(11,'11:00').isoformat(),instructor='Brian Ennis',location='offsite',course_id='210549',
            count_available=True,active_registration_count=1))
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
        row=self.add(11,'12:00','12:00',count=1)
        row['duration_minutes']=60
        self.assertEqual(self.starts('329495'),{'11:00','13:00'})

    def test_overnight_full_offer_and_half_hour_clear_day(self):
        self.add(11,'20:00','21:30','359474')
        self.windows[0]['end']=self.at(12,'06:00').isoformat()
        self.coverage[0]['end']=self.windows[0]['end']
        full=[o for o in self.payload()['offers'] if o['courseId']=='209809' and o['startTime']=='21:30'][0]
        self.assertTrue(full['occupiedUntil'].startswith('2026-10-12T00:00'))
        self.sources=[]
        self.assertIn('00:00',self.starts('210549'))
        self.assertIn('00:30',self.starts('210549'))
        self.assertIn('23:30',self.starts('210549'))
        self.windows=[];self.coverage=[];self.window(11,'03:00','05:00',next_day=False)
        self.assertEqual(self.starts('210549'),{'03:00','03:30','04:00'})

    def test_feed_trace_and_finalizer_keep_v2_edges_not_legacy_date_gate(self):
        self.add(11,'17:00','19:00','359474',count=1)
        payload=self.payload()
        # Finalizer is re-used by landscape. Freeze its clock, not the source evidence.
        with patch('scripts.layered_publication_adapter.finalize',side_effect=lambda p:finalize(p,self.now)):
            result=finalize_selector_payload(payload,[],{'sessions':[]},{'mode':'daily_anchor_stack_v1'})
        self.assertEqual([o['startTime'] for o in result['offers'] if o['courseId']=='209809'],['14:30','19:00'])
        feed=public_selector_availability_payload(result)
        full=[c for d in feed['dates'] for t in d['startTimes'] for c in t['courses'] if c['courseId']=='209809']
        # Occupied timing is public; internal source/edge identities are not.
        self.assertTrue(all(c['occupiedUntil'] for c in full))
        self.assertTrue(all(not c.get('sourceSessionIds') and not c.get('edgeIds') for c in full))
        html=render_html(result)
        self.assertIn('Heartsaver',html)
        self.assertIn('layered-publication.v2',json.dumps(feed))
        expired=finalize(result,self.now+timedelta(hours=2))
        self.assertFalse(expired['offers'])

    def test_split_availability_on_planted_day_never_reverts_to_free_space_scan(self):
        self.windows=[];self.coverage=[]
        self.window(11,'00:00','12:00',next_day=False)
        self.window(11,'13:00','00:00')
        self.add(11,'12:00','13:00',count=1)
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
        skills=self.starts('329495')
        self.assertTrue(skills, 'skills remain offered outside unverified occupied time')
        self.assertNotIn('12:00',skills)
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


if __name__=='__main__':unittest.main()
