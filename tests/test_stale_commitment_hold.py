import json
import unittest
from pathlib import Path
from scripts.block_start_time_selector import build_occupancy
from scripts.layered_selector_adapter import build_shadow
from datetime import datetime

class ExpiredEvidence(unittest.TestCase):
    def test_mapped_stale_record_and_public_looking_legacy_mirror_are_hard_holds(self):
        config=Path(__file__).resolve().parents[1]/'data/config'
        resources=json.loads((config/'location_resource_map.json').read_text())
        policy=json.loads((config/'layered_scheduling_policy.json').read_text())
        policy['require_verified_day_gravity']=True
        room=':: Wilmington; Shipyard Blvd'
        start='2026-11-30T16:00:00Z'; end='2026-11-30T18:30:00Z'
        legacy={'session_id':'80004','course_id':'209806','start_at':start,'end_at':end,
                'location':room,'location_name':room,'instructor':'Brian Ennis',
                'count_available':True,'active_registration_count':1}
        canonical={'canonical_session_id':'synthetic','external_class_id':'80004','external_course_id':'209806',
                   'catalog_course_id':'209806','start_at':start,'end_at':end,'session_status':'scheduled',
                   'location_name':room,'lead_instructor_name':'Brian Ennis','visibility':'unlisted',
                   'count_available':False,'active_registration_count':None,'demand_status':'stale_reconciliation',
                   'operational_has_stale_commitment':True}
        window=dict(instructor_name='Brian Ennis',person_id=policy['brian_person_id'],location_name=room)
        course=dict(course_id='209806', course_family='BLS', kind='full')
        scope=(datetime.fromisoformat('2026-11-30T13:00:00+00:00'),datetime.fromisoformat('2026-11-30T22:00:00+00:00'))
        now=datetime.fromisoformat('2026-11-27T07:31:04+00:00')
        base={'canonical_demand':{'sessions':[canonical]},'location_resource_map':resources}
        for key in ('sessions_current','schedule_future'):
            rows=build_occupancy({**base,key:{'sessions':[legacy]}},{},True,known_catalog_ids={'209806'})
            self.assertEqual(len(rows),2)
            self.assertTrue(all(b.get('kind')=='hold' for b in rows),rows)
            self.assertTrue(all(b.get('public_direct_booking') is False for b in rows))
            self.assertTrue(all(b.get('active_registration_count') is None for b in rows))
            for ordered in (rows, list(reversed(rows))):
                output=build_shadow([window],ordered,[course],policy,resources,now,lambda _: scope,lambda *_: True)
                self.assertTrue(output['accepted'])
                self.assertFalse(output['seated_offers'])
                self.assertFalse(output['edges'])
                for option in output['accepted']:
                    self.assertTrue(option['end']<=datetime.fromisoformat(start) or option['start']>=datetime.fromisoformat(end))

if __name__=='__main__':unittest.main()
