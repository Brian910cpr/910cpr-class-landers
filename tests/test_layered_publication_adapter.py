import copy
import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from scripts.layered_publication_adapter import calculate, publish, project_sources, finalize
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

    def payload(self,seated=(),calculation=None):
        return publish(self.calculation() if calculation is None else calculation,
            self.page,self.courses,self.windows,self.now,
            lambda w,s,c:('fixture-day','fixture-container',f'https://fixture.test/enroll?appointmentDayId=fixture-day&courseId={c}&startTime={s:%H:%M}',None),
            lambda s,c:[],seated)

    def starts(self,cid='209809',day=None):
        return {o['startTime'] for o in self.payload()['offers'] if o['courseId']==cid and (day is None or o['date']==f'2026-10-{day:02d}')}

    def test_distant_confirmed_private_offsite_kept_without_poisoning_other_day(self):
        # A private one-seat offsite session is authoritative occupancy for its
        # own day; its missing route must not reject windows two weeks away.
        self.sources.append(dict(
            source_event_id='fixture-private-distant-offsite',
            start=self.at(24, '09:00').isoformat(),
            end=self.at(24, '10:00').isoformat(),
            instructor='Brian Ennis', location='unmapped-offsite',
            resource='unmapped-offsite',
            source_file='canonical_class_sessions', visibility='private',
            count_available=True, active_registration_count=1))
        result=self.calculation()
        self.assertEqual(result['counts']['normalized_sources'], 1)
        self.assertEqual(result['counts']['failed_windows'], 0, result['issues'])
        self.assertTrue(result['reports'][0]['accepted'])
        self.assertEqual(result['projected_sources'][0]['active_registration_count'], 1)
        public=public_selector_availability_payload(self.payload(calculation=result))
        self.assertNotIn('fixture-private-distant-offsite', json.dumps(public))

    def test_near_window_private_offsite_unknown_travel_still_fails_closed(self):
        # Exact same verified booking within this availability window cannot
        # be assigned a speculative zero-minute return journey.
        self.sources.append(dict(
            source_event_id='fixture-private-near-offsite',
            start=self.at(11, '09:00').isoformat(),
            end=self.at(11, '10:00').isoformat(),
            instructor='Brian Ennis', location='unmapped-offsite',
            resource='unmapped-offsite',
            source_file='canonical_class_sessions', visibility='private',
            count_available=True, active_registration_count=1))
        result=self.calculation()
        self.assertEqual(result['counts']['failed_windows'], 1)
        self.assertEqual(result['counts']['evaluated_windows'], 0)
        self.assertTrue(any('missing directional travel rule' in issue['reason']
                            for issue in result['issues']))
        self.assertEqual(result['projected_sources'][0]['active_registration_count'], 1)
        self.assertEqual(set(result['issues'][0]['route_source_categories']),
                         {'canonical_positive', 'scope_selected_instructor', 'interval_overlaps_window'})

    def test_near_boundary_private_offsite_still_requires_known_route(self):
        # A booking ~38 hours after a window remains in the conservative 48h
        # transition/repeat-gap envelope; it must not get silently pruned.
        self.policy['brian_explicit_interval_only_nonoverlap'] = False
        self.sources.append(dict(
            source_event_id='fixture-private-adjacent-offsite',
            start=self.at(13, '08:00').isoformat(),
            end=self.at(13, '09:00').isoformat(),
            instructor='Brian Ennis', location='unmapped-offsite',
            resource='unmapped-offsite',
            source_file='canonical_class_sessions', visibility='private',
            count_available=True, active_registration_count=1))
        result=self.calculation()
        self.assertEqual(result['counts']['failed_windows'], 1)
        self.assertTrue(any('missing directional travel rule' in issue['reason']
                            for issue in result['issues']))
        self.assertEqual(set(result['issues'][0]['route_source_categories']),
                         {'canonical_positive', 'scope_selected_instructor', 'interval_outside_window'})

    def test_owner_interval_policy_keeps_nonoverlapping_private_canonical_context(self):
        self.policy['brian_explicit_interval_only_nonoverlap'] = True
        self.sources.append(dict(source_event_id='fixture-owner-nonoverlap',
            start=self.at(12, '09:00').isoformat(), end=self.at(12, '10:00').isoformat(),
            instructor='Brian Ennis', location='unmapped-offsite', resource='unmapped-offsite',
            source_file='canonical_class_sessions', visibility='private',
            count_available=True, active_registration_count=1))
        result=self.calculation()
        self.assertEqual(result['counts']['failed_windows'], 0, result['issues'])
        self.assertTrue(result['reports'][0]['accepted'])
        self.assertEqual(result['projected_sources'][0]['active_registration_count'], 1)
        self.assertEqual(result['projected_sources'][0]['visibility'], 'private')
        self.assertEqual(len(result['reports'][0]['normalized_occupancy']),1)
        # A verified direction is not replaced with a guessed opposite direction.
        self.policy['travel_minutes']={self.room+'->unmapped-offsite': 30}
        self.assertEqual(self.calculation()['counts']['failed_windows'], 1)
        del self.policy['travel_minutes']
        # A different source type at that location must not inherit the exception.
        self.sources.append(dict(self.sources[0], source_event_id='fixture-unknown-source',
            source_file='other_source', start=self.at(12,'11:00').isoformat(), end=self.at(12,'12:00').isoformat()))
        self.assertEqual(self.calculation()['counts']['failed_windows'], 1)
        self.sources.pop()
        # Unassigned commitments stay in the engine and cannot be waived
        # if they overlap the selected window.
        self.sources[0].update(instructor='unknown', instructor_unassigned=True)
        self.assertEqual(self.calculation()['counts']['failed_windows'], 0)
        self.sources[0].update(start=self.at(11,'09:00').isoformat(),end=self.at(11,'10:00').isoformat())
        self.assertEqual(self.calculation()['counts']['failed_windows'], 1)

    def test_interval_policy_does_not_apply_to_other_instructors(self):
        self.windows=[]; self.coverage=[]
        self.window(11,name='Other Instructor')
        self.policy['brian_explicit_interval_only_nonoverlap']=True
        self.sources.append(dict(source_event_id='fixture-other-nonoverlap',
            start=self.at(12,'09:00').isoformat(),end=self.at(12,'10:00').isoformat(),
            instructor='Other Instructor',location='unmapped-offsite',resource='unmapped-offsite',
            source_file='canonical_class_sessions',visibility='private',count_available=True,active_registration_count=1))
        self.assertEqual(self.calculation()['counts']['failed_windows'],1)

    def test_other_instructor_private_offsite_does_not_steal_window(self):
        self.sources.append(dict(
            source_event_id='fixture-other-instructor-offsite',
            start=self.at(11, '09:00').isoformat(),
            end=self.at(11, '10:00').isoformat(),
            instructor='Unrelated Instructor', location='unmapped-offsite',
            resource='unmapped-offsite',
            source_file='canonical_class_sessions', visibility='private',
            count_available=True, active_registration_count=1))
        result=self.calculation()
        self.assertEqual(result['counts']['failed_windows'], 0, result['issues'])
        self.assertTrue(result['reports'][0]['accepted'])


    def test_unproven_legacy_occurrence_keeps_hard_block_without_daywide_gravity(self):
        # Physical occupancy and publication day gravity are separate gates.
        self.windows=[];self.coverage=[];self.sources=[]
        self.window(11,'08:00','18:00',next_day=False)
        baseline=self.calculation()
        row=self.add(11,'12:00','13:00',count=None)
        occupied=self.calculation()
        self.assertTrue(any(
            any(self.at(11,'12:00') == aware(source['start'])
                for source in report['normalized_occupancy'])
            for report in occupied['reports']))
        # Isolate the downstream publication gate using the same already
        # calculated clear-day candidates and a late-arriving unknown source.
        baseline['projected_sources']=project_sources([row],{})
        published=self.payload(calculation=baseline)
        self.assertTrue(any(o.get('scheduleRole')=='open_day' for o in published['offers']))
        self.assertNotIn('anchored_day_requires_attached_offer',
                         published['rejectionReasonCounts'])

    def test_only_proven_seated_offer_collapses_same_course_family_day(self):
        # An empty published class shell does not acquire paid Anchor status.
        self.windows=[];self.coverage=[];self.sources=[]
        self.window(11,'08:00','18:00',next_day=False)
        calculation=self.calculation()
        source=self.add(11,'12:00','14:30',cid='209809',count=None)
        calculation['projected_sources']=project_sources([source],{})
        seated=dict(session_id=source['source_event_id'],date='2026-10-11',
                    startTime='12:00',courseId='209809',courseName='Existing',
                    instructor='Brian Ennis',offerType='seated_class')
        unknown=self.payload([seated],calculation=calculation)
        self.assertTrue(any(o['courseId']=='209809' and
                            o.get('scheduleRole')=='open_day' for o in unknown['offers']))
        self.assertNotIn('existing_course_day_anchor',unknown['rejectionReasonCounts'])
        source['count_available']=True
        source['active_registration_count']=1
        calculation['projected_sources']=project_sources([source],{})
        proven=self.payload([seated],calculation=calculation)
        self.assertFalse(any(o['courseId']=='209809' and
                             o.get('scheduleRole')=='open_day' for o in proven['offers']))
        self.assertIn('existing_course_day_anchor',proven['rejectionReasonCounts'])
        self.assertEqual(sum(o['offerType']=='seated_class'
                             for o in proven['offers']),1)

    def test_verified_course_anchor_does_not_collapse_other_instructor(self):
        # Publication must not globally hide a qualified second instructor's
        # already-approved starts merely because someone booked this course
        # with the first instructor. Resource conflicts are tested upstream.
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11, '08:00', '18:00', next_day=False)
        self.window(11, '08:00', '18:00', name='Michelle', next_day=False)
        clear_calculation=self.calculation()
        confirmed=self.add(11, '12:00', '14:30', cid='209809', count=1)
        clear_calculation['projected_sources']=project_sources([confirmed], {})
        seated=dict(session_id=confirmed['source_event_id'],
                    date='2026-10-11', startTime='12:00', courseId='209809',
                    instructor='Brian Ennis', offerType='seated_class')
        offers=self.payload([seated], calculation=clear_calculation)['offers']
        self.assertEqual(sum(o.get('offerType')=='seated_class' for o in offers), 1)
        self.assertFalse(any(o.get('offerType')=='dynamic_appointment'
            and o['courseId']=='209809' and o['instructor']=='Brian Ennis'
            for o in offers))
        self.assertTrue(any(o.get('offerType')=='dynamic_appointment'
            and o['courseId']=='209809' and o['instructor']=='Michelle'
            and o['startTime']=='08:00' and o['scheduleRole']=='open_day'
            for o in offers))

    def test_independent_instructor_keeps_legal_bookends_but_not_shared_room_collision(self):
        # Integration regression: do not rely on a pre-seat clear-day report.
        # The real engine must respect the shared physical room for Michelle,
        # even while the publication gate keeps her independent qualified edges.
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11, '08:00', '18:00', next_day=False)
        self.window(11, '08:00', '18:00', name='Michelle', next_day=False)
        self.policy['require_verified_day_gravity'] = True
        self.add(11, '12:00', '14:30', cid='209809', count=1,
                 visibility='private', registration_status='closed')
        calculation=self.calculation()
        self.assertEqual(len(calculation['reports']), 2, calculation['issues'])
        payload=self.payload(calculation=calculation)
        michelle=[o for o in payload['offers']
                  if o.get('offerType')=='dynamic_appointment'
                  and o.get('instructor')=='Michelle']
        self.assertTrue(michelle, payload['rejectionReasonCounts'])
        self.assertTrue(any(o['scheduleRole']=='barnacle' for o in michelle))
        for offer in michelle:
            start=self.at(11, offer['startTime'])
            end=aware(offer['occupiedUntil'])
            self.assertFalse(start < self.at(11, '14:30')
                             and end > self.at(11, '12:00'),
                             'seated class room was offered to second instructor')
        public=public_selector_availability_payload(payload)
        self.assertNotIn('fixture-11-12:00-Brian Ennis', json.dumps(public))

    def test_canonical_course_mapping_survives_real_occupancy_normalizer(self):
        # Production-shaped joined Supabase demand: canonical private intake has
        # a course FK mapping but no per-session numeric external course ID.
        # Keep the private time blocked AND apply the paid full-course family cap.
        from scripts.block_start_time_selector import build_occupancy
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11,'08:00','18:00',next_day=False)
        self.policy['require_verified_day_gravity']=True
        snapshot={'sessions_current':{'sessions':[]},
                  'schedule_future':{'sessions':[]},
                  'live_availability_snapshot':{},
                  'location_resource_map':self.resources,
                  'canonical_demand':{'sessions':[{
                      'canonical_session_id':'fixture-canonical-private-course-mapped',
                      'session_status':'scheduled','course_key':'aha-bls-provider-renewal',
                      'scheduler_course_id':'359474','external_course_id':None,
                      'start_at':self.at(11,'12:00').isoformat(),
                      'end_at':self.at(11,'14:30').isoformat(),
                      'location_name':':: Wilmington; Shipyard Blvd',
                      'lead_instructor_name':'Brian Ennis',
                      'operational_has_active_seat':True,'count_available':False,
                      'active_registration_count':None,
                  }]}}
        occupied=build_occupancy(snapshot,{},allow_unresolved=True)
        self.assertEqual(len(occupied),1,occupied)
        self.assertEqual(occupied[0]['course_id'],'359474')
        self.assertEqual(occupied[0]['location_resolution'],'location_resource_map')
        self.sources=occupied
        calculation=self.calculation()
        self.assertEqual(len(calculation['reports']),1,calculation['issues'])
        report=calculation['reports'][0]
        self.assertTrue(any(row['id']=='fixture-canonical-private-course-mapped'
            and row['kind']=='paid' and row['course']=='359474'
            for row in report['normalized_occupancy']))
        self.assertFalse(any(row['course']=='359474' for row in report['accepted']),
            'private occupied full course allowed same-family duplicate')
        self.assertTrue(any(reason in report['rejection_reasons'] for reason in
            ('full_course_already_paid_seated','full_family_already_paid_seated')),
            report['rejection_reasons'])
        self.assertFalse(any(o.get('offerType')=='seated_class'
            for o in self.payload(calculation=calculation)['offers']))
        self.assertNotIn('fixture-canonical-private-course-mapped',
            json.dumps(public_selector_availability_payload(self.payload(calculation=calculation))))
        snapshot['canonical_demand']['sessions'][0]['course_identity_conflict']=True
        conflicting=build_occupancy(snapshot,{},allow_unresolved=True)
        self.assertIsNone(conflicting[0]['course_id'])
        self.assertEqual(conflicting[0]['start'],occupied[0]['start'])
        self.assertEqual(conflicting[0]['end'],occupied[0]['end'])

    def test_private_key_only_positive_seat_has_internal_day_gravity(self):
        # A confirmed private seat may lack an external course ID. It is still
        # operational demand, but this gate must never create a joinable seat.
        self.windows=[];self.coverage=[];self.sources=[]
        self.window(11,'08:00','18:00',next_day=False)
        calculation=self.calculation()
        private=dict(source_event_id='fixture-private-canonical-session',
                     course_id='',course_key='aha_bls_provider_renewal',
                     visibility='private',instructor='Brian Ennis',
                     start=self.at(11,'12:00').isoformat(),
                     end=self.at(11,'14:30').isoformat(),
                     count_available=True,active_registration_count=1)
        calculation['projected_sources']=project_sources([private],{})
        result=self.payload(calculation=calculation)
        self.assertFalse(result['offers'])
        self.assertIn('anchored_day_requires_attached_offer',
                      result['rejectionReasonCounts'])
        self.assertNotIn(private['source_event_id'],json.dumps(result['offers']))
        self.assertFalse(any(o.get('offerType')=='seated_class' for o in result['offers']))

    def test_private_unassigned_seat_blocks_time_not_other_instructors_entire_day(self):
        # Real private demand with no verified lead belongs to the occupied
        # interval, not an inferred daywide Anchor for an independent instructor.
        # A separately identified room never becomes a public booking container.
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11, '08:00', '18:00', name='Michelle', next_day=False)
        self.policy['require_verified_day_gravity'] = True
        other_room=':: Wilmington; Shipyard Blvd - C'
        private=self.add(11, '12:00', '13:00', cid='359474', name='',
                         count=1, visibility='private',
                         instructor_unassigned=True)
        private['resource']=other_room
        calculation=self.calculation()
        self.assertEqual(calculation['counts']['failed_windows'], 0,
                         calculation['issues'])
        occupied=calculation['reports'][0]['normalized_occupancy']
        self.assertTrue(any(row['id']==private['source_event_id']
                            and row['location']==other_room
                            and row['headcount']==1 for row in occupied))
        self.assertTrue(any(row['instructor']=='Michelle'
                            and row['kind']=='hold' for row in occupied))
        payload=self.payload(calculation=calculation)
        offers=[o for o in payload['offers']
                if o.get('offerType')=='dynamic_appointment'
                and o['instructor']=='Michelle']
        self.assertTrue(any(o['startTime']=='08:00'
                            and o['courseId']=='209809'
                            and o['scheduleRole']=='open_day' for o in offers),
                        payload['rejectionReasonCounts'])
        self.assertTrue(any(o['startTime']=='13:00' for o in offers))
        for offer in offers:
            start=self.at(11, offer['startTime'])
            end=aware(offer['occupiedUntil'])
            self.assertFalse(start < self.at(11,'13:00')
                             and end > self.at(11,'12:00'),
                             'unassigned appointment time was offered')
        self.assertFalse(any(o.get('offerType')=='seated_class'
                             for o in payload['offers']))
        public=public_selector_availability_payload(payload)
        self.assertNotIn(private['source_event_id'],json.dumps(public))

    def test_unassigned_private_unknown_room_blocks_primary_without_daywide_veto(self):
        # Production-shaped canonical record: paid one-seat appointment, known
        # Shipyard venue, but NULL resource_id and no verified lead instructor.
        # No other room may be inferred; physical time is reserved in the
        # conservative primary room even for an independent qualified teacher.
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11, '08:00', '18:00', name='Michelle', next_day=False)
        self.policy['require_verified_day_gravity'] = True
        private=self.add(11, '12:00', '13:00', cid='359474',
                         name='UNASSIGNED', count=1, visibility='private',
                         registration_status='closed',
                         instructor_unassigned=True)
        private.pop('resource')
        private['location']=':: Wilmington; Shipyard Blvd'
        # A resolved venue is not a verified separate room assignment.
        private['location_resolution']='location_resource_map'
        calculation=self.calculation()
        self.assertEqual(calculation['counts']['failed_windows'], 0,
                         calculation['issues'])
        occupied=calculation['reports'][0]['normalized_occupancy']
        self.assertTrue(any(row['id']==private['source_event_id']
                            and row['location']==self.room
                            and row['headcount']==1 for row in occupied))
        self.assertTrue(any(row['instructor']=='Michelle'
                            and row['kind']=='hold'
                            and row['location']==self.room for row in occupied))
        payload=self.payload(calculation=calculation)
        offers=[row for row in payload['offers']
                if row.get('offerType')=='dynamic_appointment'
                and row.get('instructor')=='Michelle']
        self.assertTrue(offers, payload['rejectionReasonCounts'])
        self.assertTrue(any(aware(row['occupiedUntil']) <= self.at(11, '12:00')
                            or self.at(11, row['startTime']) >= self.at(11, '13:00')
                            for row in offers))
        for row in offers:
            self.assertEqual(row['resource'], self.room)
            self.assertFalse(self.at(11, row['startTime']) < self.at(11, '13:00')
                             and aware(row['occupiedUntil']) > self.at(11, '12:00'),
                             'NULL room was treated as an unoccupied second room')
        public=public_selector_availability_payload(payload)
        self.assertNotIn(private['source_event_id'],json.dumps(public))
        self.assertFalse(any(row.get('offerType')=='seated_class'
                             for row in payload['offers']))

    def test_private_unassigned_shared_room_blocks_duplicate_full_course_not_other_choices(self):
        # A confirmed but unassigned private BLS seat consumes the primary
        # room and its same-course day allowance, not other qualified courses.
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11,'08:00','18:00',name='Michelle',next_day=False)
        self.policy['require_verified_day_gravity']=True
        private=self.add(11,'12:00','14:30',cid='359474',
                         name='UNASSIGNED',count=1,visibility='private',
                         registration_status='closed',instructor_unassigned=True)
        private.pop('resource')
        private['location']=':: Wilmington; Shipyard Blvd'
        private['location_resolution']='location_resource_map'
        calculation=self.calculation()
        self.assertEqual(calculation['counts']['failed_windows'],0,calculation['issues'])
        payload=self.payload(calculation=calculation)
        offers=[o for o in payload['offers']
                if o.get('offerType')=='dynamic_appointment'
                and o.get('instructor')=='Michelle']
        self.assertFalse([o for o in offers if o['courseId']=='359474'],
                         'an unknown-instructor paid BLS seat must not yield another full BLS start')
        self.assertTrue([o for o in offers if o['courseId']=='209809'],
                        'another qualified course must retain its legal bookends')
        self.assertTrue([o for o in offers if o['courseId']=='210549'],
                        'skills repeat gap remains zero')
        public=public_selector_availability_payload(payload)
        self.assertNotIn(private['source_event_id'],json.dumps(public))
        self.assertFalse(any(o.get('offerType')=='seated_class' for o in payload['offers']))

    def test_adjacent_confirmed_private_session_with_unassigned_instructor(self):
        # Source-shaped Nov 20 boundary: confirmed BLS consumption ends at
        # 14:30, exactly when a second closed private appointment begins.
        # Unknown instructor/room must never create a speculative public seat,
        # erase either occupied interval, or free the 14:30 transition.
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11, '08:00', '18:00', next_day=False)
        self.policy['require_verified_day_gravity'] = True
        first=self.add(11, '13:30', '14:30', cid='359474', count=1,
                       visibility='private', registration_status='closed')
        second=self.add(11, '14:30', '16:00', cid='359474',
                        name='UNASSIGNED', count=None,
                        visibility='private', registration_status='closed',
                        operational_has_active_seat=True,
                        instructor_unassigned=True)
        # Synthetic known-venue fallback only: no invented second room,
        # participant identity, or instructor assignment.
        calculation=self.calculation()
        self.assertEqual(len(calculation['reports']), 1, calculation['issues'])
        occupied=calculation['reports'][0]['normalized_occupancy']
        self.assertTrue(any(o['id']==first['source_event_id'] and
                            aware(o['end'])==self.at(11, '14:30') for o in occupied))
        self.assertTrue(any(o['id']==second['source_event_id'] and
                            aware(o['start'])==self.at(11, '14:30') and
                            aware(o['end'])==self.at(11, '16:00') and
                            o['operational_has_active_seat'] for o in occupied))
        self.assertTrue(any(o['id'].startswith('unassigned-') and
                            o['instructor']=='Brian Ennis' for o in occupied))
        payload=self.payload(calculation=calculation)
        public=public_selector_availability_payload(payload)
        for offer in payload['offers']:
            if offer.get('offerType')=='seated_class': continue
            start=self.at(11, offer['startTime'])
            end=aware(offer['occupiedUntil'])
            self.assertFalse(start < self.at(11, '16:00') and
                             end > self.at(11, '13:30'),
                             f"private interval became bookable: {offer['startTime']}")
        self.assertFalse(any(o.get('offerType')=='seated_class'
                             for o in payload['offers']))
        self.assertNotIn(first['source_event_id'], json.dumps(public))
        self.assertNotIn(second['source_event_id'], json.dumps(public))

    def test_native_private_seat_survives_exact_interval_legacy_mirror(self):
        # A legacy class shell and a canonical paid seat may represent the same
        # physical interval. Neither source order may erase verified occupancy
        # or turn the private record into a publicly joinable existing class.
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11, '08:00', '18:00', next_day=False)
        self.policy['require_verified_day_gravity'] = True
        legacy=self.add(11,'12:00','13:00',cid='359474',count=None)
        legacy['source_file']='docs/data/schedule_future.json'
        canonical=dict(legacy,source_event_id='synthetic-canonical-private-seat',
            source_file='canonical_class_sessions',visibility='private',
            operational_has_active_seat=True,count_available=False,
            active_registration_count=None)
        for rows in ([legacy,canonical],[canonical,legacy]):
            with self.subTest(first=rows[0]['source_file']):
                self.sources=list(rows)
                reports=self.calculation()['reports']
                self.assertEqual(len(reports),1)
                occupied=reports[0]['normalized_occupancy']
                self.assertEqual(len(occupied),1)
                self.assertEqual(occupied[0]['id'],'synthetic-canonical-private-seat')
                self.assertTrue(occupied[0]['operational_has_active_seat'])
                self.assertEqual(occupied[0]['kind'],'paid')
                self.assertIsNone(occupied[0]['headcount'])
                # finalize() retains restricted internal diagnostics by design.
                # Test the actual customer-facing whitelist projection instead.
                public=public_selector_availability_payload(self.payload())
                self.assertFalse(any(course.get('offerType')=='seated_class'
                    for day in public['dates'] for slot in day['startTimes']
                    for course in slot['courses']))
                self.assertNotIn('synthetic-canonical-private-seat',json.dumps(public))

    def test_distinct_confirmed_same_interval_bookings_are_not_deduped_as_mirrors(self):
        # Two independently identified paid/private seats can occupy identical
        # instructor/resource geometry even when the canonical records disagree
        # on course family. This is a reconciliation conflict, not proof that
        # either booking may be erased or made available for public joining.
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11, '08:00', '18:00', next_day=False)
        self.policy['require_verified_day_gravity'] = True
        first=self.add(11, '12:00', '13:00', cid='359474', count=1,
                       operational_has_active_seat=True,
                       visibility='private', registration_status='closed')
        first['source_event_id']='independent-private-seat-1'
        second=self.add(11, '12:00', '13:00', cid='209809', count=1,
                        operational_has_active_seat=True,
                        visibility='private', registration_status='closed')
        second['source_event_id']='independent-private-seat-2'
        result=self.calculation()
        self.assertEqual(result['counts']['failed_windows'], 0, result['issues'])
        occupied=result['reports'][0]['normalized_occupancy']
        paid=[row for row in occupied if row['id'] in
              {'independent-private-seat-1', 'independent-private-seat-2'}]
        self.assertEqual(len(paid), 2, 'distinct confirmed seats were deduped by geometry')
        self.assertEqual({row['course'] for row in paid}, {'359474', '209809'})
        self.assertTrue(all(row['operational_has_active_seat'] for row in paid))
        self.assertFalse(any(row['start'] < self.at(11, '13:00') and
                             row['end'] > self.at(11, '12:00')
                             for row in result['reports'][0]['accepted']))
        public=public_selector_availability_payload(self.payload(calculation=result))
        serialized=json.dumps(public)
        self.assertNotIn('independent-private-seat-1', serialized)
        self.assertNotIn('independent-private-seat-2', serialized)

    def test_unmapped_historical_paid_seats_report_family_identity_gap(self):
        # Three distinct one-seat private historical course records have no
        # verified numeric scheduler ID. Preserve ALL physical intervals; do
        # not pretend that their BLS full-course family cap has been proven.
        # A fourth, separately registered BLS class at an identical interval
        # is a distinct commitment, never a geometry-based duplicate.
        self.windows=[]; self.coverage=[]; self.sources=[]
        for day in (11, 12, 13):
            self.window(day, '08:00', '18:00', next_day=False)
        historical_ids=set()
        for day, start, end in (
                (11, '15:00', '17:00'),
                (12, '10:00', '12:00'),
                (13, '11:30', '13:30')):
            row=self.add(day, start, end, cid='hist-course:unmapped-source',
                count=1, operational_has_active_seat=True,
                visibility='private', registration_status='closed')
            row['source_event_id']=f'private-unmapped-{day}'
            historical_ids.add(row['source_event_id'])
        public_seat=self.add(12, '10:00', '12:00', cid='359474',
            count=1, operational_has_active_seat=True,
            visibility='public', registration_status='open')
        public_seat['source_event_id']='independent-public-bought-seat'
        calculation=self.calculation()
        self.assertEqual(calculation['counts']['failed_windows'], 0, calculation['issues'])
        protected=set()
        for report in calculation['reports']:
            occupied=report['normalized_occupancy']
            historical=[row for row in occupied if row['id'] in historical_ids]
            protected.update(row['id'] for row in historical)
            diagnostic=report['family_seating_diagnostics']
            self.assertEqual(
                diagnostic['unmapped_positive_seated_course_count'],
                len(historical))
            if historical:
                self.assertFalse(diagnostic['unmapped_positive_seated_family_policy_proven'])
            for row in historical:
                self.assertEqual(row['kind'], 'paid')
                self.assertTrue(row['operational_has_active_seat'])
                self.assertIsNone(row['course'])
                self.assertFalse(any(
                    offer['start'] < row['end'] and offer['end'] > row['start']
                    for offer in report['accepted']))
        self.assertEqual(protected, historical_ids)
        nov23_shape=next(report for report in calculation['reports']
                         if report['availability_window'].startswith('Brian Ennis-12-'))
        simultaneous=[row for row in nov23_shape['normalized_occupancy']
                      if row['start']==self.at(12, '10:00')
                      and row['end']==self.at(12, '12:00')
                      and row['kind']=='paid']
        self.assertEqual({row['id'] for row in simultaneous},
                         {'private-unmapped-12', 'independent-public-bought-seat'})
        public=json.dumps(public_selector_availability_payload(
            self.payload(calculation=calculation)))
        for private_id in historical_ids:
            self.assertNotIn(private_id, public)
        self.assertNotIn('hist-course:unmapped-source', public)

    def test_different_end_private_mirrors_preserve_latest_consumption_end(self):
        # Production-shaped duplicate evidence can describe the same two seats
        # with different occupied ends (e.g. 19:30 vs 20:00). Preserve both
        # source intervals conservatively until the owner records are reconciled;
        # never count the mirror as a new publicly joinable class.
        self.windows=[]; self.coverage=[]; self.sources=[]
        self.window(11, '08:00', '22:00', next_day=False)
        self.policy['require_verified_day_gravity'] = True
        canonical=self.add(11, '17:30', '20:00', cid='359474', count=2,
                           visibility='unlisted', registration_status='open')
        canonical['source_event_id']='synthetic-canonical-late-end'
        external=self.add(11, '17:30', '19:30', cid='359474', count=2,
                          visibility='unlisted', registration_status='external')
        external['source_event_id']='synthetic-legacy-early-end'
        external['source_file']='docs/data/schedule_future.json'
        for rows in ([canonical, external], [external, canonical]):
            with self.subTest(first=rows[0]['source_file']):
                self.sources=list(rows)
                calculation=self.calculation()
                self.assertEqual(len(calculation['reports']), 1, calculation['issues'])
                occupied=calculation['reports'][0]['normalized_occupancy']
                self.assertEqual({o['id'] for o in occupied},
                    {canonical['source_event_id'], external['source_event_id']})
                self.assertEqual(max(aware(o['end']) for o in occupied),
                                 self.at(11, '20:00'))
                public=public_selector_availability_payload(
                    self.payload(calculation=calculation))
                self.assertFalse(any(
                    offer.get('offerType')=='seated_class'
                    for day in public['dates'] for slot in day['startTimes']
                    for offer in slot['courses']))
                self.assertNotIn('synthetic-canonical-late-end', json.dumps(public))
                self.assertNotIn('synthetic-legacy-early-end', json.dumps(public))
                for offer in self.payload(calculation=calculation)['offers']:
                    if offer.get('offerType') == 'seated_class':
                        continue
                    start=self.at(11, offer['startTime'])
                    end=aware(offer['occupiedUntil'])
                    self.assertFalse(start < self.at(11, '20:00')
                        and end > self.at(11, '17:30'),
                        'shortened mirror exposed occupied private interval')

    def test_v2_empty_occupied_shell_does_not_create_fake_bookend_day(self):
        # The existing physical interval stays unavailable, while safe free
        # time on both sides is scanned instead of requiring fake Barnacles.
        self.windows=[];self.coverage=[];self.sources=[]
        self.window(11,'08:00','18:00',next_day=False)
        self.policy["require_verified_day_gravity"] = True
        row=self.add(11,'12:00','13:00',cid='359474',count=None)
        for count in (None, 0):
            row['count_available'] = count is not None
            row['active_registration_count'] = count
            result=self.payload()
            offers=[o for o in result['offers'] if o['courseId']=='209809']
            self.assertTrue(any(o['startTime']=='08:00' and
                                o['scheduleRole']=='open_day' for o in offers),
                            f"count={count} offers={[(o['startTime'],o['scheduleRole']) for o in offers[:12]]} "
                            f"reasons={result['rejectionReasonCounts']} counts={result['counts']}")
            self.assertTrue(any(o['startTime']=='14:00' and
                                o['scheduleRole']=='open_day' for o in offers))
            self.assertFalse(any(o['startTime']=='12:00' for o in offers))
            self.assertNotIn('anchored_day_requires_attached_offer',
                             result['rejectionReasonCounts'])
        # The same occupied interval, with one verified private seat, must
        # instead provide internal Anchor gravity without a public private seat.
        row['visibility']='private'
        row['active_registration_count']=1
        row['count_available']=True
        proven=self.payload()
        self.assertFalse(any(o.get('scheduleRole')=='open_day' for o in proven['offers']))
        self.assertTrue(any(o.get('scheduleRole')=='barnacle' for o in proven['offers']))
        self.assertFalse(any(o.get('offerType')=='seated_class' for o in proven['offers']))

    def test_clear_day_offers_all_qualified_courses_at_every_half_hour(self):
        # Owner doctrine #16: open qualified windows use the 30-minute grid.
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
        # Even the course/date/time of a rejected private or unlisted seated
        # choice is confidential, not just its source URL and customer fields.
        private_rejections = [row for row in public['rejectedCourseStartTimes']
                              if row.get('offerType') == 'seated_class']
        self.assertEqual(private_rejections, [dict(
            offerType='seated_class',
            reasons=['existing_booking_choice_withheld'])])
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

    def test_public_landscape_never_publishes_nonpublic_booking_geometry(self):
        # Private, unlisted and unknown source commitments must constrain the
        # internal engine but must not reveal exact occupied times in public JSON.
        internal = {
            'projected_sources': [
                dict(source_event_id='SECRET-PRIVATE-ID', visibility='private',
                     course_id='SECRET-PRIVATE-COURSE', kind='paid',
                     operational_has_active_seat=True, count_available=True,
                     active_registration_count=1, start='2026-11-22T15:07:00',
                     end='2026-11-22T17:13:00', resource='Shipyard Room B'),
                dict(source_event_id='SECRET-UNKNOWN-ID',
                     course_id='SECRET-UNKNOWN-COURSE', kind='paid',
                     count_available=True, active_registration_count=2,
                     start='2026-11-23T10:03:00', end='2026-11-23T12:17:00'),
                dict(source_event_id='SECRET-REVOKED-ID', visibility='public',
                     public_direct_booking=False, kind='paid',
                     start='2026-11-25T09:06:00', end='2026-11-25T10:22:00'),
                dict(source_event_id='PUBLIC-CLASS', visibility='public',
                     course_id='209806', kind='paid', count_available=True,
                     active_registration_count=1,
                     start='2026-11-24T10:00:00', end='2026-11-24T12:00:00')],
            'reports':[{'blocks':[dict(id='SECRET-BLOCK-ID',
                                      source_ids=['SECRET-PRIVATE-ID'],
                                      start='2026-11-22T15:07:00',
                                      end='2026-11-22T17:13:00')]}],
        }
        before=copy.deepcopy(internal)
        landscape=public_layered_landscape({'layeredDiagnostics':internal})
        self.assertEqual(len(landscape['sources']), 1)
        public=landscape['sources'][0]
        # Even explicitly public courses must not disclose ingestion/source
        # identifiers (which can encode email or calendar provenance).
        self.assertNotIn('sourceId', public)
        self.assertEqual((public['courseId'], public['role'],
                          public['registeredCount']),
                         ('209806', 'anchor', 1))
        self.assertEqual(landscape['occupiedBlocks'], [])
        public_json=json.dumps(landscape)
        for secret in ('SECRET-PRIVATE-ID','SECRET-PRIVATE-COURSE',
                       'PUBLIC-CLASS', 'SECRET-UNKNOWN-ID','SECRET-UNKNOWN-COURSE',
                       'SECRET-REVOKED-ID','SECRET-BLOCK-ID',
                       '15:07:00','17:13:00','10:03:00','12:17:00',
                       '09:06:00','10:22:00'):
            self.assertNotIn(secret,public_json)
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
        redacted=json.dumps(feed)
        for private_value in ('PRIVATE CLIENT', 'PRIVATE VENUE', 'SECRET STAFF',
                              'SECRET ROOM', 'SECRET SOURCE', 'SECRET COURSE'):
            self.assertNotIn(private_value,redacted)
        # Exact private occupancy remains an internal blocker only; the
        # customer feed exposes eligible starts, not hidden appointment times.
        self.assertNotIn(private['start'],redacted)
        self.assertNotIn(private['end'],redacted)
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
                                                        edgeIds=['SECRET-PRIVATE-EDGE'])]}]}],
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


    def test_final_v2_publisher_withholds_orphan_seated_route_without_source_proof(self):
        # A stale, public-looking class card is not proof that the selected
        # canonical/legacy occupancy source still recognizes that session.
        # Keep source privacy and authoritative bookings separate.
        orphan = dict(session_id='orphan-private-source-sentinel',
                      date='2026-10-11', startTime='12:00',
                      courseId='210549', courseName='Stale unverified class',
                      offerType='seated_class',
                      registrationUrl='https://legacy.invalid/stale')
        payload = self.payload([orphan])
        self.assertFalse(any(o.get('offerType') == 'seated_class'
                             for o in payload['offers']))
        self.assertIn('existing_booking_source_unverified',
                      payload['rejectionReasonCounts'])
        public = public_selector_availability_payload(payload)
        self.assertNotIn('orphan-private-source-sentinel', json.dumps(public))
        self.assertNotIn('legacy.invalid', json.dumps(public))
        self.assertNotIn('Stale unverified class', json.dumps(public))

        # A distinct, recognized positive-seat source remains eligible for
        # the existing seated path; don't suppress verified public inventory.
        verified = self.add(11, '12:00', '13:00', cid='210549', count=1,
                            visibility='public', public_direct_booking=True)
        verified['registration_url'] = 'https://fixture.test/current'
        confirmed = dict(orphan, session_id=verified['source_event_id'],
                         courseName='Verified current class',
                         registrationUrl='https://fixture.test/current')
        result = self.payload([confirmed])
        self.assertTrue(any(o.get('offerType') == 'seated_class'
                            and o.get('session_id') == verified['source_event_id']
                            for o in result['offers']))

    def test_final_v2_publisher_cannot_attach_wrong_course_to_valid_class(self):
        # A valid public, positive-seat class can retain its ID and start time
        # while a stale route labels it as a different course. Never advertise
        # that route; only the source-proven course may remain joinable.
        source = self.add(11, '12:00', '13:00', cid='210549', count=1,
                          visibility='public', public_direct_booking=True)
        source['registration_url'] = 'https://fixture.test/right-course'
        valid = dict(session_id=source['source_event_id'],
                     date='2026-10-11', startTime='12:00',
                     courseId='210549', courseName='Verified skills course',
                     offerType='seated_class',
                     registrationUrl='https://fixture.test/right-course')
        self.assertEqual(sum(o.get('offerType') == 'seated_class'
                             for o in self.payload([valid])['offers']), 1)
        wrong = dict(valid, courseId='359474', courseName='Wrong renewal',
                     registrationUrl='https://wrong.invalid/course')
        result = self.payload([wrong])
        self.assertFalse([o for o in result['offers']
                          if o.get('offerType') == 'seated_class'])
        self.assertIn('existing_booking_course_mismatch',
                      result['rejectionReasonCounts'])
        self.assertEqual(result['layeredDiagnostics']['projected_sources'][0][
            'active_registration_count'], 1)
        public = json.dumps(public_selector_availability_payload(result))
        self.assertNotIn('wrong.invalid', public)
        self.assertNotIn('Wrong renewal', public)
        self.assertNotIn(source['source_event_id'], public)

    def test_final_v2_publisher_rejects_stale_source_matched_class_time(self):
        # A reschedule can retain a stable class identity while the cached
        # public selector still points at the old occurrence. Do not treat
        # ID-only matching as proof of a bookable date/start time.
        self.sources = []
        source = self.add(11, '12:00', '13:00', cid='210549', count=1,
                          visibility='public', public_direct_booking=True)
        source['registration_url'] = 'https://fixture.test/current'
        current = dict(session_id=source['source_event_id'],
                       date='2026-10-11', startTime='12:00',
                       courseId='210549', courseName='Verified current class',
                       offerType='seated_class',
                       registrationUrl='https://fixture.test/current')
        accepted = self.payload([current])
        self.assertEqual(sum(o.get('offerType') == 'seated_class'
                             for o in accepted['offers']), 1)

        for change in ({'date': '2026-10-12'},
                       {'startTime': '14:00'},
                       {'startTime': None}):
            with self.subTest(stale_public_card=change):
                stale = dict(current, **change,
                             registrationUrl='https://stale.invalid/rescheduled')
                result = self.payload([stale])
                self.assertFalse(any(o.get('offerType') == 'seated_class'
                                     for o in result['offers']))
                self.assertIn('existing_booking_occurrence_mismatch',
                              result['rejectionReasonCounts'])
                exposed = json.dumps(public_selector_availability_payload(result))
                self.assertNotIn('stale.invalid', exposed)
                self.assertNotIn(source['source_event_id'], exposed)

        # The authoritative class itself moved, but its identifier stayed
        # stable. A previously valid card must be withdrawn, not reattached.
        source['start'] = self.at(11, '13:00').isoformat()
        source['end'] = self.at(11, '14:00').isoformat()
        moved = self.payload([current])
        self.assertNotIn(current, moved['offers'])
        self.assertIn('existing_booking_occurrence_mismatch',
                      moved['rejectionReasonCounts'])
        self.assertEqual(moved['layeredDiagnostics']['projected_sources'][0][
            'active_registration_count'], 1)
        self.assertEqual(moved['layeredDiagnostics']['projected_sources'][0][
            'start'], source['start'])

    def test_final_v2_publisher_requires_source_attested_registration_route(self):
        # An ID/course/time match does not verify that its CTA belongs to the
        # selected authoritative session. Preserve the active seat and redact
        # all disallowed destination URLs from the public JSON.
        self.sources = []
        source = self.add(11, '12:00', '13:00', cid='210549', count=1,
                          visibility='public', public_direct_booking=True)
        valid = dict(session_id=source['source_event_id'],
                     date='2026-10-11', startTime='12:00',
                     courseId='210549', courseName='Verified seated route',
                     offerType='seated_class',
                     registrationUrl='https://fixture.test/verified')
        missing = self.payload([valid])
        self.assertIn('existing_booking_route_unverified',
                      missing['rejectionReasonCounts'])
        self.assertFalse([o for o in missing['offers'] if o.get('offerType') == 'seated_class'])

        source['registration_url'] = valid['registrationUrl']
        accepted = self.payload([valid])
        self.assertEqual(sum(o.get('offerType') == 'seated_class'
                             for o in accepted['offers']), 1)

        cases = (
            dict(registrationUrl='https://wrong.invalid/different-class'),
            dict(registrationUrl='https://fixture.test/verified',
                 appointmentUrl='https://wrong.invalid/alternate'),
        )
        for wrong in cases:
            with self.subTest(untrusted_route=wrong):
                result = self.payload([dict(valid, **wrong)])
                self.assertFalse([o for o in result['offers']
                                  if o.get('offerType') == 'seated_class'])
                self.assertIn('existing_booking_route_unverified',
                              result['rejectionReasonCounts'])
                self.assertEqual(result['layeredDiagnostics']['projected_sources'][0]
                                 ['active_registration_count'], 1)
                public = json.dumps(public_selector_availability_payload(result))
                self.assertNotIn('wrong.invalid', public)
                self.assertNotIn(source['source_event_id'], public)

        # Even an exact authority-string match is not permission for a
        # plaintext or credential-bearing customer link.
        for bad in ('http://fixture.test/verified',
                    'https://user:pass@fixture.test/verified',
                    'https://fixture.test/verified#hidden'):
            with self.subTest(unsafe_route=bad):
                source['registration_url'] = bad
                result = self.payload([dict(valid, registrationUrl=bad)])
                self.assertIn('existing_booking_route_unverified',
                              result['rejectionReasonCounts'])
        self.sources = []

    def test_canonical_registration_route_survives_occupancy_normalizer(self):
        from scripts.block_start_time_selector import build_occupancy
        destination = 'https://fixture.test/canonical-authority'
        self.sources = build_occupancy(dict(
            location_resource_map=self.resources,
            canonical_demand=dict(sessions=[dict(
                canonical_session_id='canonical-route-proof',
                location_name=':: Wilmington; Shipyard Blvd',
                lead_instructor_name='Brian Ennis',
                session_status='scheduled', visibility='public',
                registration_status='open',
                public_direct_booking=True,
                external_course_id='210549',
                registration_url=destination,
                start_at=self.at(11, '12:00').isoformat(),
                end_at=self.at(11, '13:00').isoformat(),
                count_available=True, active_registration_count=1,
                operational_has_active_seat=True,
            )])), {}, allow_unresolved=True)
        self.assertEqual(self.sources[0]['registration_url'], destination)
        source_offer = dict(session_id='canonical-route-proof',
                            date='2026-10-11', startTime='12:00',
                            courseId='210549', offerType='seated_class',
                            registrationUrl=destination)
        payload = self.payload([source_offer])
        self.assertTrue(any(o.get('offerType') == 'seated_class'
                            for o in payload['offers']))
        self.assertEqual(payload['layeredDiagnostics']['projected_sources'][0]
                         ['active_registration_count'], 1)
        self.sources = []

    def test_final_v2_publisher_withholds_explicitly_closed_public_seated_route(self):
        # A valid positive-seat source remains operationally occupied even
        # when its public registration lifecycle is closed or cancelled.
        # Never revive the stale customer CTA simply because its ID matches.
        for status_field, status in (
                ('registration_status', 'closed'),
                ('registration_status', 'full'),
                ('registration_status', 'unverified'),
                ('registration_status', 'deleted'),
                ('registration_status', 'cancelled'),
                ('session_status', 'canceled'),
                ('session_status', 'deleted'),
                ('is_full', True)):
            with self.subTest(status_field=status_field, status=status):
                self.sources = []
                source = self.add(11, '12:00', '13:00', cid='210549',
                                  count=1, visibility='public',
                                  public_direct_booking=True)
                source[status_field] = status
                seat = dict(session_id=source['source_event_id'],
                            date='2026-10-11', startTime='12:00',
                            courseId='210549', offerType='seated_class',
                            courseName='No longer joinable',
                            registrationUrl='https://closed.invalid/stale')
                payload = self.payload([seat])
                self.assertFalse(any(o.get('offerType') == 'seated_class'
                                     for o in payload['offers']))
                self.assertIn('nonpublic_or_unverified_existing_booking_choice',
                              payload['rejectionReasonCounts'])
                self.assertEqual(payload['layeredDiagnostics']['projected_sources'][0]
                                 ['active_registration_count'], 1)
                public = public_selector_availability_payload(payload)
                self.assertNotIn('closed.invalid', json.dumps(public))
                self.assertNotIn(source['source_event_id'], json.dumps(public))
        self.sources = []

    def test_canonical_closed_route_survives_normalization_and_cannot_be_resurrected(self):
        # This exercises the actual canonical -> build_occupancy -> V2 publisher
        # path. A final route gate is ineffective if the normalizer silently
        # drops canonical registration_status while preserving positive seats.
        from scripts.block_start_time_selector import build_occupancy

        for status in ('closed', 'full', 'unverified', 'cancelled', 'deleted'):
            with self.subTest(registration_status=status):
                self.sources = build_occupancy(dict(
                    location_resource_map=self.resources,
                    canonical_demand=dict(sessions=[dict(
                        canonical_session_id='canonical-closed-route-sentinel',
                        location_name=':: Wilmington; Shipyard Blvd',
                        lead_instructor_name='Brian Ennis',
                        session_status='scheduled', visibility='public',
                        registration_status=status,
                        public_direct_booking=True,
                        external_course_id='210549',
                        start_at=self.at(11, '12:00').isoformat(),
                        end_at=self.at(11, '13:00').isoformat(),
                        count_available=True, active_registration_count=1,
                        operational_has_active_seat=True,
                    )])), {}, allow_unresolved=True)
                self.assertEqual(self.sources[0]['registration_status'], status)
                self.assertEqual(self.sources[0]['session_status'], 'scheduled')
                seated = dict(session_id='canonical-closed-route-sentinel',
                              date='2026-10-11', startTime='12:00',
                              courseId='210549', offerType='seated_class',
                              courseName='Never joinable',
                              registrationUrl='https://closed.invalid/revived')
                payload = self.payload([seated])
                self.assertFalse([o for o in payload['offers']
                                  if o.get('offerType') == 'seated_class'])
                self.assertIn('nonpublic_or_unverified_existing_booking_choice',
                              payload['rejectionReasonCounts'])
                self.assertEqual(payload['layeredDiagnostics']['projected_sources'][0]
                                 ['active_registration_count'], 1)
                public = json.dumps(public_selector_availability_payload(payload))
                self.assertNotIn('canonical-closed-route-sentinel', public)
                self.assertNotIn('closed.invalid', public)
        self.sources = []

    def test_final_v2_publisher_cannot_resurrect_private_or_unlisted_seated_routes(self):
        from scripts.block_start_time_selector import build_occupancy
        for visibility, route_allowed in (('private', True), ('unlisted', True),
                                           ('internal', True), ('public', False)):
            with self.subTest(visibility=visibility, route_allowed=route_allowed):
                self.sources = build_occupancy(dict(
                    location_resource_map=self.resources,
                    canonical_demand=dict(sessions=[dict(
                        canonical_session_id='private-seat-sentinel',
                        location_name=':: Wilmington; Shipyard Blvd',
                        lead_instructor_name='Brian Ennis',
                        session_status='scheduled', external_course_id='210549',
                        start_at=self.at(11, '12:00').isoformat(),
                        end_at=self.at(11, '13:00').isoformat(),
                        count_available=True, active_registration_count=1,
                        operational_has_active_seat=True, visibility=visibility,
                        public_direct_booking=route_allowed,
                    )])), {}, allow_unresolved=True)
                seated = dict(session_id='private-seat-sentinel',
                              date='2026-10-11', startTime='12:00',
                              courseId='210549', courseName='Unlisted source class',
                              offerType='seated_class',
                              registrationUrl='https://private.invalid/forbidden')
                payload = self.payload([seated])
                self.assertFalse([offer for offer in payload['offers']
                                  if offer.get('offerType') == 'seated_class'])
                self.assertFalse(any(
                    row.get('courseName') == 'Unlisted source class'
                    or row.get('date') == '2026-10-11' and row.get('startTime') == '12:00'
                    for row in payload['rejectedCourseStartTimes']
                    if row.get('offerType') == 'seated_class'
                ), 'Rejected private seats must not disclose class or time')
                self.assertIn('nonpublic_or_unverified_existing_booking_choice',
                              payload['rejectionReasonCounts'])
                self.assertTrue(payload['layeredDiagnostics']['projected_sources'][0][
                    'operational_has_active_seat'])
                public = public_selector_availability_payload(payload)
                self.assertNotIn('private-seat-sentinel', json.dumps(public))
                self.assertNotIn('private.invalid', json.dumps(public))
        self.sources = []


    def test_normalized_legacy_mirror_keeps_explicit_route_denials(self):
        from scripts.block_start_time_selector import build_occupancy
        route = 'https://fixture.test/enroll?id=fixture-class-720'
        row = dict(session_id='fixture-class-720', course_id='210549',
                   start_at=self.at(11, '12:00').isoformat(),
                   end_at=self.at(11, '13:00').isoformat(),
                   lead_instructor_name='Brian Ennis', location_name=self.room,
                   course_name='Synthetic skills class', registration_url=route)
        seated = dict(session_id=row['session_id'], date='2026-10-11',
                      startTime='12:00', courseId='210549',
                      courseName='Synthetic skills class', offerType='seated_class',
                      registrationUrl=route)
        for denial in ({}, {'visibility': 'unlisted'}, {'registration_status': 'closed'},
                       {'registration_status': 'full'}, {'session_status': 'cancelled'},
                       {'public_direct_booking': False}, {'is_full': True}):
            with self.subTest(denial=denial):
                self.sources = []
                self.add(11, '12:00', '13:00', count=1, visibility='public',
                         external_class_id=row['session_id'], registration_url=route)
                mirror = build_occupancy(dict(sessions_current={'sessions': [dict(row, **denial)]},
                    schedule_future={'sessions': []}, location_resource_map=self.resources),
                    {}, allow_unresolved=True)
                self.assertEqual(len(mirror), 1)
                self.sources.extend(mirror)
                payload = self.payload([seated])
                public = public_selector_availability_payload(payload)
                actual = [offer for offer in payload['offers']
                          if offer.get('offerType') == 'seated_class']
                self.assertEqual(len(actual), 0 if denial else 1)
                self.assertTrue(any(source.get('active_registration_count') == 1
                                    for source in payload['layeredDiagnostics']['projected_sources']))
                if denial:
                    self.assertIn('nonpublic_or_unverified_existing_booking_choice',
                                  payload['rejectionReasonCounts'])
                    self.assertNotIn(route, json.dumps(public))

    def test_mirrored_closed_route_cannot_override_public_canonical_seat(self):
        canonical = self.add(11, '12:00', '13:00', cid='210549', count=1,
                             visibility='public', external_class_id='legacy-class-720')
        mirror = dict(canonical, source_file='schedule_future',
                      source_event_id='legacy-mirror-720',
                      count_available=False, active_registration_count=None,
                      public_direct_booking=False)
        self.sources.append(mirror)
        seated = dict(session_id='legacy-class-720', date='2026-10-11',
                      startTime='12:00', courseId='210549',
                      courseName='Mirrored registration route',
                      offerType='seated_class',
                      registrationUrl='https://legacy.invalid/unverified')
        payload = self.payload([seated])
        self.assertTrue(any(source.get('active_registration_count') == 1
                            for source in payload['layeredDiagnostics']['projected_sources']))
        self.assertFalse([offer for offer in payload['offers']
                          if offer.get('offerType') == 'seated_class'])
        self.assertIn('nonpublic_or_unverified_existing_booking_choice',
                      payload['rejectionReasonCounts'])
        self.assertNotIn('legacy.invalid',
                         json.dumps(public_selector_availability_payload(payload)))


if __name__=='__main__':unittest.main()
