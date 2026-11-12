import copy
import unittest
from datetime import timedelta
from unittest.mock import patch
from scripts import validate_public_refresh_output as validator
from scripts.layered_publication_adapter import publish
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload
from scripts.native_publication_scope import instant
from tests import test_native_publication_wiring as wired

class NativeFullValidatorTests(unittest.TestCase):
    def fixture(self, course_id='359474'):
        case=wired.NativeWiringTests().fixture()
        if course_id == '209806':
            case.courses[0].update(course_id=course_id,clean_course_name='AHA BLS Provider')
            case.page.update(allowed_course_ids=[course_id],course_options=[{'course_id':course_id}])
        policy=case.policy['native_publication_scope']
        def forbidden(*args):raise AssertionError('legacy URL lookup forbidden')
        payload=publish(case.calculation(),case.page,case.courses,case.windows,case.now,forbidden,lambda *args:[],native_policy=policy)
        feed=public_selector_availability_payload(payload)
        return case,feed
    def validate(self,feed,now):
        with patch.object(validator,'load_json',return_value=feed):
            return validator.validate_selector('bls',set(),now=now)
    def row(self,feed):return feed['dates'][0]['startTimes'][0]['courses'][0]
    def test_actual_wired_compact_feed_passes_strict_refresh_validator(self):
        for course_id in ['209806','359474']:
            case,feed=self.fixture(course_id)
            self.assertGreater(self.validate(feed,case.now)['offers'],0)
            self.assertEqual(instant(self.row(feed)['proofObservedAt']),case.now)
            self.assertEqual(self.row(feed)['courseId'],course_id)
    def test_tampered_identity_trace_course_timing_and_original_proof_rejected(self):
        case,original=self.fixture()
        mutations=[('authority','wrong'),('nativeScopeId','other'),('selectionId','native-full:'+'0'*64),
            ('courseId','209809'),('durationMinutes',True),('cleanupBufferMinutes',0),
            ('schedulerConsumptionMinutes',120),('setupBufferMinutes',1),('publicSelectable',False),
            ('instructor','Other'),('resource','Room C'),('sourceSessionIds',None),
            ('sourceSessionIds',['x','x']),('sourceSessionIds',[3]),('availabilityBlockId',' '),
            ('appointmentDayId',None),('matchedContainerId',''),
            ('proofObservedAt',(case.now-timedelta(minutes=15)).isoformat()),
            ('proofObservedAt',(case.now+timedelta(seconds=1)).isoformat()),
            ('proofObservedAt',case.now.replace(tzinfo=None).isoformat()),
            ('occupiedUntil',(case.now+timedelta(days=2)).isoformat())]
        for key,value in mutations:
            feed=copy.deepcopy(original);self.row(feed)[key]=value
            with self.subTest(key=key,value=value), self.assertRaises(ValueError):self.validate(feed,case.now)
        feed=copy.deepcopy(original);del self.row(feed)['proofObservedAt']
        with self.assertRaises(ValueError):self.validate(feed,case.now)
        for generated in [case.now+timedelta(seconds=1),case.now-timedelta(seconds=1)]:
            feed=copy.deepcopy(original);feed['generatedAt']=generated.isoformat()
            with self.assertRaisesRegex(ValueError,'original proof'):self.validate(feed,case.now)
    def test_owned_relative_url_and_exact_allowlisted_query(self):
        case,original=self.fixture();url=self.row(original)['registrationUrl']
        bad=['https://www.910cpr.com'+url,'//www.910cpr.com'+url,'/other/?'+url.split('?',1)[1],url+'#',url+'#x',url+'&x=1',url+'&course=359474',url+'&empty=',url+'&',url.replace('course=359474','course=209806'),url.replace('/register/','/register\\evil/'),url+'\n']
        for value in bad:
            feed=copy.deepcopy(original);self.row(feed)['registrationUrl']=value;self.row(feed)['appointmentUrl']=value
            with self.subTest(url=value), self.assertRaises(ValueError):self.validate(feed,case.now)
        feed=copy.deepcopy(original);self.row(feed)['appointmentUrl']='https://other.invalid/'
        with self.assertRaises(ValueError):self.validate(feed,case.now)
    def test_expiry_and_downgrade_do_not_refresh_original_proof(self):
        case,original=self.fixture()
        feed=copy.deepcopy(original)
        # A new publication timestamp and lease cannot renew old observed evidence.
        later=case.now+timedelta(minutes=14)
        feed['generatedAt']=later.isoformat();feed['validUntil']=(later+timedelta(minutes=10)).isoformat()
        for day in feed['dates']:
            for slot in day['startTimes']:
                for c in slot['courses']:c['validUntil']=feed['validUntil']
        with self.assertRaisesRegex(ValueError,'original proof'):self.validate(feed,later)
        feed=copy.deepcopy(original);feed['validUntil']=(case.now+timedelta(minutes=1)).isoformat()
        with self.assertRaisesRegex(ValueError,'exceeds publication'):self.validate(feed,case.now)
        with self.assertRaises(ValueError):self.validate(original,case.now+timedelta(minutes=15))
    def test_dst_gap_fold_lead_and_horizon(self):
        case,original=self.fixture();row=copy.deepcopy(self.row(original))
        for day,clock,current in [('2030-03-10','02:30','2030-03-08T00:00:00Z'),('2030-11-03','01:30','2030-11-01T00:00:00Z')]:
            c=copy.deepcopy(row);c.update(date=day,startTime=clock)
            with self.subTest(day=day),self.assertRaisesRegex(ValueError,'ambiguous or nonexistent'):
                validator.validate_native_full_offer(c,original,'bls',day,clock,now=instant(current))
        for current in [instant(row['date']+'T00:00:00-04:00'),case.now-timedelta(days=100)]:
            feed=copy.deepcopy(original)
            feed['generatedAt']=current.isoformat();feed['validUntil']=(current+timedelta(minutes=10)).isoformat()
            c=self.row(feed);c.update(proofObservedAt=current.isoformat(),validUntil=feed['validUntil'])
            with self.assertRaisesRegex(ValueError,'outside lead or horizon'):
                validator.validate_native_full_offer(c,feed,'bls',c['date'],c['startTime'],now=current)

if __name__=='__main__':unittest.main()
