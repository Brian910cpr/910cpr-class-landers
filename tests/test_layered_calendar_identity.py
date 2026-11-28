import copy
import json
from datetime import datetime
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.block_start_time_selector import build_occupancy, find_url
from scripts.build_live_availability_snapshot import build_snapshot, layered_calendar_coverage, load_runtime_snapshots
from scripts.layered_day_cache import cached_calculate
from scripts.layered_instructor_identity import configured_calendar_ownership, valid_owned_coverage
from tests import test_layered_publication_adapter as fixtures


class CalendarOwnerProofTests(unittest.TestCase):
    def setUp(self):
        self.f = f = fixtures.LayeredPublicationTests()
        f.setUp()
        self.a = f.policy["brian_person_id"]
        self.b = 'synthetic-other-person'
        self.people = {'people': [dict(person_id=p, display_name='Shared Alias', email=e,
                   dynamic_offer_eligible=True, assignment_mode='PRIMARY')
                    for p, e in [(self.a,'same@one.invalid'), (self.b,'same@two.invalid')]]}
        self.calendar = {'calendar_sources': [
          {'calendar_source_key':'owner_teaching', 'owner_instructor_key':'shared alias',
           'calendar_mode':'explicit_availability','default_location_key':'shipyard'},
          {'calendar_source_key':'owner_extra', 'owner_instructor_key':'same',
           'calendar_mode':'explicit_availability','default_location_key':'shipyard'},
          {'calendar_source_key':'other_teaching', 'owner_instructor_key':'other',
           'calendar_mode':'explicit_availability','default_location_key':'shipyard'},
        ]}
        self.policy = dict(calendar_owner_person_ids={'shared alias':self.a,'same':self.a,'other':self.b},
                           calendar_source_owners={'owner_teaching':self.a,'owner_extra':self.a,'other_teaching':self.b})
        self.now = datetime.fromisoformat('2026-10-05T16:00:00+00:00')
        self.event = dict(id='synthetic-open', summary='Available', start='2026-10-11T08:00:00-04:00',
                          end='2026-10-11T18:00:00-04:00')
        evidence = dict(export_status='ok', warnings=[], skipped={},
            generated_at=self.now.isoformat(),
            date_range=dict(start='2026-10-10T00:00:00-04:00',end='2026-10-13T00:00:00-04:00'))
        self.snapshot = dict(events_by_source={'owner_teaching':[self.event],
              'owner_extra':[], 'other_teaching':[dict(self.event, id='synthetic-other-open')]},
              source_evidence={key:copy.deepcopy(evidence) for key in self.policy['calendar_source_owners']})

    def blocks(self, policy=None):
        return build_snapshot(self.calendar,self.people,{},self.snapshot,
                              identity_policy=policy)[0]

    def coverage(self, blocks=None, policy=None):
        return layered_calendar_coverage(self.calendar,self.people,self.snapshot,
                 blocks if blocks is not None else self.blocks(policy),now=self.now,identity_policy=policy)

    def test_alias_collision_old_wrong_strict_right_and_missing_independent_source(self):
        legacy = self.blocks()
        legacy_owner = next(row for row in legacy if row['source_calendar_id']=='owner_teaching')
        self.assertEqual(legacy_owner['person_id'], self.b)  # Wrong valid ID; reproduced.
        strict = self.blocks(self.policy)
        self.assertEqual({row['source_calendar_id']:row['person_id'] for row in strict},
                         {'owner_teaching': self.a, 'other_teaching': self.b})
        self.assertEqual({p['instructor_person_id']:set(p['source_ids']) for p in self.coverage(strict,self.policy)},
                         {self.a:{'owner_teaching','owner_extra'},self.b:{'other_teaching'}})
        del self.snapshot['events_by_source']['owner_extra']  # metadata alone is not a full export
        self.assertEqual([p['instructor_person_id'] for p in self.coverage(strict,self.policy)],[self.b])

    def test_consumer_rejects_substituted_owner_wrong_source_set_and_configuration_change(self):
        strict = self.blocks(self.policy)
        fake = [dict(row, person_id=self.b) for row in strict if row['source_calendar_id']=='owner_teaching']
        self.assertEqual(self.coverage(fake,self.policy), [])
        _, required = configured_calendar_ownership(self.calendar,self.people['people'],self.policy)
        proof = next(p for p in self.coverage(strict,self.policy) if p['instructor_person_id']==self.a)
        self.assertTrue(valid_owned_coverage(proof,required))
        self.assertFalse(valid_owned_coverage(dict(proof, source_ids=['owner_teaching']),required))
        self.assertFalse(valid_owned_coverage(dict(proof, instructor_person_id=self.b),required))
        self.calendar['calendar_sources'][1]['owner_instructor_key']='other'
        _, new = configured_calendar_ownership(self.calendar,self.people['people'],self.policy)
        self.assertFalse(valid_owned_coverage(proof,new))

    def test_wrong_emitted_calendar_id_keeps_physical_hold_scoped_to_configured_owner(self):
        f=self.f
        raw=dict(self.event, availability_status='blocked', source_calendar_id='owner_teaching',
            start_datetime='2026-10-11T12:00:00-04:00',end_datetime='2026-10-11T13:00:00-04:00',
            start_time='12:00',end_time='13:00',date='2026-10-11',end_date='2026-10-11',
            instructor_name='Shared Alias',person_id=self.b,location_name=f.windows[0]['location_name'],
            availability_location_mode='instructor_time_only')
        rows = build_occupancy({'live_availability_snapshot':{'availability_blocks':[raw]},
            'location_resource_map':f.resources}, {},True, strict_instructor_crosswalk={},
            strict_calendar_source_owners={'owner_teaching':self.a})
        self.assertEqual(len(rows),1)
        self.assertTrue(rows[0]['instructor_unassigned'])
        self.assertEqual(rows[0]['uncertain_calendar_owner_id'],self.a)
        self.assertNotIn('effective_instructor_person_id',rows[0])
        f.sources = rows
        f.windows[0].update(start=f.at(11,'08:00').isoformat(),end=f.at(11,'18:00').isoformat())
        f.coverage[0].update(instructor_person_id=self.a,start=f.windows[0]['start'],end=f.windows[0]['end'])
        f.policy['verified_instructor_identity']=True
        with tempfile.TemporaryDirectory() as work:
            def calc():
                return cached_calculate(f.windows,f.sources,f.courses,f.policy,f.resources,f.now,
                    lambda w:(w['start'],w['end']),lambda *_:True,f.coverage,cache_dir=Path(work))
            first=calc()
            self.assertTrue(first['reports'][0]['normalized_occupancy'])
            self.assertEqual(calc()['incremental_cache']['hits'],1)
            rows[0]['uncertain_calendar_owner_id']=self.b
            changed=calc()
            self.assertEqual(changed['incremental_cache']['hits'],0)
            self.assertFalse(changed['reports'][0]['normalized_occupancy'])
            self.assertTrue(changed['reports'][0]['accepted'])

    def test_inverse_missing_route_does_not_erase_block_and_skills_stay_unverified(self):
        self.calendar['calendar_sources'][0]['calendar_mode']='inverse_blocking'
        self.calendar['calendar_sources'][0]['availability_location_mode']='instructor_time_only'
        rows=self.blocks(self.policy)
        own=[row for row in rows if row['source_calendar_id']=='owner_teaching']
        self.assertEqual([row['availability_status'] for row in own],['blocked'])
        f=self.f
        self.assertEqual(find_url(f.windows[0],f.at(11,'09:00'),'509474',[],f.resources,
            strict_container_owners={}), (None,None,None,'native_skills_route_owner_unverified'))
        self.assertIsNotNone(find_url(f.windows[0],f.at(11,'09:00'),'509474',[],f.resources)[2])


    def test_duplicate_exports_deny_coverage_and_keep_earlier_busy_intervals(self):
        self.calendar['calendar_sources'][0]['calendar_mode']='inverse_blocking'
        self.calendar['calendar_sources'][0]['inverse_expansion_require_active_appointment_container']=False
        entries = {'a': ('owner_teaching',[self.event]),
                   'b': ('owner_teaching',[]),
                   'c': ('owner_extra',[]), 'd': ('other_teaching',[self.event])}
        with tempfile.TemporaryDirectory() as root:
            for name,(key,events) in entries.items():
                payload=dict(self.snapshot['source_evidence'][key], calendar_source_id=key,events=events)
                (Path(root)/(name+'.json')).write_text(json.dumps(payload))
            with patch('scripts.build_live_availability_snapshot.RUNTIME_CALENDAR_SNAPSHOT_DIR',Path(root)):
                _,self.snapshot,_=load_runtime_snapshots()
        self.assertEqual(self.snapshot['ambiguous_exports'],['owner_teaching'])
        self.assertEqual(self.snapshot['events_by_source']['owner_teaching'],[])
        rows=self.blocks(self.policy)
        self.assertTrue(any(row['source_calendar_id']=='owner_teaching' and row['availability_status']=='blocked' for row in rows))
        self.assertEqual([proof['instructor_person_id'] for proof in self.coverage(rows,self.policy)],[self.b])
