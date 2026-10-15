"""Issue 338: scoped edge publication and immutable Heartsaver regression."""
from copy import deepcopy
from datetime import datetime, timedelta
import unittest
from scripts import block_start_time_selector as builder
from scripts import public_block_edges as edges
from scripts.apply_anchor_policy import finalize_selector_payload, production_anchor_policy
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload
from scripts.canonical_scheduling_demand import resolve_canonical_demand
from tests import test_native_public_anchor as native_fixture

class BLSBridgeTests(unittest.TestCase):
    def fixture(self):
        row = native_fixture.NativeAnchorTests().row()
        sessions, _ = resolve_canonical_demand([], [row])
        # All three inputs identify the same real class. Cleanup is added once.
        loaded = {'sessions_current': {'sessions': sessions}, 'schedule_future': {'sessions': sessions},
                  'canonical_demand': {'sessions': [row]}, 'live_availability_snapshot': {}, 'location_resource_map': {}}
        occupancy = builder.build_occupancy(loaded, {})
        blocks = edges.merged_blocks(occupancy)
        self.assertEqual({b['end'].strftime('%H:%M') for b in blocks}, {'17:00'})
        # Canonical aliases must resolve to one public identity.
        self.assertEqual(len(blocks), 1)
        offers=[]
        for cid, duration, cleanup, kind in [('209806',120,30,'full'),('359474',120,30,'full'),('210549',45,15,'skills')]:
            for candidate in edges.plan_starts(datetime(2026,10,10,7),datetime(2026,10,11), 'Brian Ennis', ':: Wilmington; Shipyard Blvd',duration+cleanup,blocks,occupancy):
                start=candidate['start'];end=start+timedelta(minutes=duration+cleanup)
                offers.append(dict(courseId=cid,courseName='BLS',date='2026-10-10',startTime=start.strftime('%H:%M'),location=':: Wilmington; Shipyard Blvd',instructor='Brian Ennis',durationMinutes=duration,cleanupBufferMinutes=cleanup,setupBufferMinutes=0,schedulerConsumptionMinutes=duration+cleanup,schedulerConsumptionEnd=end.strftime('%H:%M'),blockEdge=candidate['edge'],attached_to_session_id=candidate['attached_to_session_id'],offerKind=kind,schedule_role='barnacle',appointmentUrl='https://example.test/appointment',appointmentDayId=1,availabilityBlockId='fixture',durationProvenance='approved-BLS',bufferProvenance='issue338'))
        real=builder.seated_class_selector_offers(schedule_future_payload={'sessions': sessions},selected_courses=[{'course_id':'209809'}],selected_course_ids={'209809'},course_rules={})
        payload={'dates':[{'date':'2026-10-10','startTimes':[{'startTime':o['startTime'],'courses':[o]} for o in offers+real]}], 'counts':{},'occupiedBlockEdges':{'schemaVersion':edges.VERSION,'blocks':edges.serialize_blocks(blocks)}, 'fullFamilyGroups':{'209806':'BLS','359474':'BLS'}}
        return payload,sessions,{'sessions':[row]},offers

    def result(self, payload, sessions, demand):
        return finalize_selector_payload(payload,sessions,demand,production_anchor_policy())

    def rows(self,payload):
        return [o for d in payload['dates'] for s in d['startTimes'] for o in s['courses']]

    def test_exact_candidates_finalizer_and_compaction_preserve_real_class(self):
        payload,sessions,demand,candidates=self.fixture()
        self.assertEqual({(o['courseId'],o['startTime']) for o in candidates},{('209806','11:30'),('209806','17:00'),('359474','11:30'),('359474','17:00'),('210549','13:00'),('210549','17:00')})
        result=self.result(payload,sessions,demand); kept=self.rows(result)
        dynamic=[o for o in kept if o.get('offerType')!='seated_class']
        self.assertEqual(len(dynamic),4) # one full-family start; two uncapped skills edges
        real=[o for o in kept if o.get('offerType')=='seated_class']
        self.assertEqual(len(real),1); self.assertEqual(real[0]['startTime'],'14:00')
        self.assertEqual(real[0]['appointmentUrl'],sessions[0]['registration_url'])
        compact=self.rows(public_selector_availability_payload(result))
        for offer in compact:
            if offer.get('offerType')=='seated_class': continue
            for field in ('blockEdge','attached_to_session_id','schedulerConsumptionMinutes','durationProvenance','bufferProvenance','cleanupBufferMinutes'): self.assertIn(field,offer)

    def test_missing_attachment_and_stale_geometry_fail_closed(self):
        for corruption in ('missing','moved','wrong-course','missing-block'):
            payload,sessions,demand,_=self.fixture()
            for offer in self.rows(payload):
                if not offer.get('blockEdge'): continue
                if corruption=='missing': offer.pop('attached_to_session_id')
                if corruption=='moved': offer['blockEdge']['time']='2026-10-10T18:00:00'
                if corruption=='wrong-course': offer['courseId']='329495'
                if corruption=='missing-block': offer['blockEdge']['blockId']='gone'
            kept=self.rows(self.result(payload,sessions,demand))
            self.assertEqual(len(kept),1,corruption)
            self.assertEqual(kept[0]['offerType'],'seated_class')

    def test_public_validator_requires_preserved_provenance(self):
        from unittest.mock import patch
        from scripts import validate_public_refresh_output as validator
        payload,sessions,demand,_=self.fixture()
        compact=public_selector_availability_payload(self.result(payload,sessions,demand))
        compact['pageKey']='bls'
        with patch.object(validator,'load_json',return_value=compact):
            self.assertEqual(validator.validate_selector('bls',{sessions[0]['session_id']})['offers'],5)
            dynamic=next(o for o in self.rows(compact) if o.get('blockEdge'))
            dynamic.pop('bufferProvenance')
            with self.assertRaisesRegex(ValueError,'bufferProvenance'):
                validator.validate_selector('bls',{sessions[0]['session_id']})

    def test_reconciliation_blocks_all_synthesis(self):
        for status in ('missing','stale'):
            payload,sessions,demand,_=self.fixture()
            payload['reconciliationIssues']=[{'date':'2026-10-10','blocksSynthesis':True,'code':status}]
            kept=self.rows(self.result(payload,sessions,demand))
            self.assertTrue(kept);self.assertTrue(all(o.get('offerType')=='seated_class' for o in kept))


    def test_real_builder_and_finalizer_from_controlled_sources(self):
        import json
        from contextlib import ExitStack
        from unittest.mock import patch
        row=native_fixture.NativeAnchorTests().row()
        sessions,_=resolve_canonical_demand([], [row])
        real_read=builder.read_required_json
        def read(path):
            if path==builder.SESSIONS_CURRENT_PATH: return {'sessions':[]}
            if path==builder.SCHEDULE_FUTURE_PATH: return {'sessions':deepcopy(sessions)}
            if path==builder.LOCATION_RESOURCE_MAP_PATH: return {}
            if path==builder.PEOPLE_CATALOG_PATH:
                return {'people':[{'person_id':'brian','display_name':'Brian Ennis','dynamic_offer_eligible':True,'assignment_mode':'PRIMARY','certifications':[{'certification_code':'AHA_BLS_INSTRUCTOR'}]}]}
            return real_read(path)
        window={'date':'2026-10-10','start_time':'07:00','end_time':'23:59','start_datetime':'2026-10-10T07:00:00','end_datetime':'2026-10-10T23:59:00','location_name':':: Wilmington; Shipyard Blvd','instructor_name':'Brian Ennis','allowed_course_families':['BLS'],'source_availability_window':'fixture'}
        stats={'available_blocks_read':1,'availability_source_used':'fixture','availability_fallback_used':False}
        with ExitStack() as stack:
            for name,value in [('read_required_json',read),('require_current_live_availability_snapshot',lambda:{}),('load_publication_demand',lambda root:{'sessions':[row]}),('sessions_with_canonical_demand',lambda value:(deepcopy(sessions),[])),('selected_public_page_live_windows',lambda *args:([window],stats)),('selector_reference_datetime',lambda:datetime(2026,10,8)),('find_url',lambda *args:(1,'fixture','https://example.test/appointment','')),('resolve_selector_payload',lambda payload:self.result(payload,sessions,{'sessions':[row]}))]:
                stack.enter_context(patch.object(builder,name,value))
            config=builder.load_block_schedule_page_configs()['bls']
            result=builder.build_block_schedule_page(config)
        kept=self.rows(result)
        self.assertEqual({(o['courseId'],o['startTime']) for o in kept},{('209806','11:30'),('359474','11:30'),('210549','13:00'),('210549','17:00')})

if __name__=='__main__': unittest.main()
