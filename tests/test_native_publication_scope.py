import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from scripts.native_publication_scope import inverse_bounds, offer_fields, SCOPE

class NativeScopeTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2030,1,1,tzinfo=timezone.utc)
        self.policy={'schemaVersion':'native-publication-scope.v1','enabled':True,'scopeId':SCOPE}
        self.source={'calendar_source_key':'brian_do_not_schedule','owner_instructor_key':'brian','calendar_mode':'inverse_blocking','active':True,'inverse_expansion_horizon_days':90}
        self.calendars={'calendar_sources':[self.source,{'calendar_source_key':'personal','owner_instructor_key':'brian','active':True}]}
        self.snapshot={'source_evidence':{},'events_by_source':{}}
        for key in ['brian_do_not_schedule','personal']:
            self.snapshot['source_evidence'][key]={'export_status':'ok','generated_at':self.now.isoformat(),'date_range':{'start':self.now.isoformat(),'end':(self.now+timedelta(days=10)).isoformat()},'warnings':[],'skipped':{}}
            self.snapshot['events_by_source'][key]=[]
        self.validate=lambda s,e: (None,None,e.get('invalid'),[])
    def bounds(self):
        return inverse_bounds(self.policy,self.source,self.calendars,self.snapshot,self.now,self.validate)
    def test_default_off_and_no_legacy_dependency(self):
        self.assertIsNone(inverse_bounds({}, {}, {}, {}, self.now,self.validate))
        b=self.bounds()
        self.assertEqual(b['endsAt'],self.now+timedelta(days=10))
        self.assertEqual(b['validUntil'],self.now+timedelta(minutes=15))
        self.assertEqual(b['scopeId'],SCOPE)
    def test_every_owned_calendar_required(self):
        del self.snapshot['source_evidence']['personal']
        with self.assertRaisesRegex(ValueError,'missing'):self.bounds()
    def test_stale_partial_invalid_future_closed(self):
        original=deepcopy(self.snapshot)
        for patch in [{'generated_at':(self.now-timedelta(minutes=15)).isoformat()}, {'generated_at':(self.now+timedelta(seconds=1)).isoformat()}, {'warnings':['partial']}, {'skipped':{'parse_error':1}}, {'export_status':'failed'}]:
            self.snapshot=deepcopy(original);self.snapshot['source_evidence']['personal'].update(patch)
            with self.assertRaises(ValueError):self.bounds()
        self.snapshot=deepcopy(original);self.snapshot['events_by_source']['personal']=[{'invalid':'missing_end'}]
        with self.assertRaisesRegex(ValueError,'unresolved'):self.bounds()
    def test_intersected_coverage_not_empty_window_guess(self):
        start=self.now+timedelta(days=2)
        self.snapshot['source_evidence']['personal']['date_range']['start']=start.isoformat()
        self.assertEqual(self.bounds()['startsAt'],start)
        self.snapshot['source_evidence']['personal']['date_range']['end']=self.now.isoformat()
        with self.assertRaises(ValueError):self.bounds()
    def candidate(self):
        # 01:00 Eastern, intentionally overnight and >24 hours ahead.
        start=self.now+timedelta(days=2,hours=6)
        c={'course':'209806','instructor':'Brian Ennis','location':':: Wilmington; Shipyard Blvd - B','start':start,'instruction_end':start+timedelta(minutes=120),'end':start+timedelta(minutes=150),'source_ids':['retained-private-blocker']}
        return c,{'native_proof_observed_at':self.now,'accepted':[c],'availability_window':'fresh-native-window','valid_until':self.now+timedelta(minutes=10)}, {'location_name':':: Wilmington; Shipyard Blvd'}
    def test_overnight_native_identity_refresh_stable_no_external_id(self):
        c,r,w=self.candidate();a=offer_fields(self.policy,c,r,w,self.now)
        r['availability_window']='refreshed-block';r['valid_until']+=timedelta(minutes=1)
        b=offer_fields(self.policy,c,r,w,self.now)
        self.assertEqual(a['selectionId'],b['selectionId'])
        self.assertTrue(a['selectionId'].startswith('native-full:'))
        self.assertNotIn('appointmentDayId',a)
        self.assertNotIn('enrollware',a['registrationUrl'])
    def test_rejected_course_timing_lease_identity_never_promoted(self):
        c,r,w=self.candidate();r['accepted']=[]
        with self.assertRaisesRegex(ValueError,'accepted'):offer_fields(self.policy,c,r,w,self.now)
        for patch in [{'course':'209809'},{'end':c['end']+timedelta(minutes=1)},{'instructor':'Other'}]:
            c,r,w=self.candidate();c.update(patch)
            with self.assertRaises(ValueError):offer_fields(self.policy,c,r,w,self.now)
        c,r,w=self.candidate();r['valid_until']=self.now
        with self.assertRaises(ValueError):offer_fields(self.policy,c,r,w,self.now)

if __name__=='__main__':unittest.main()
