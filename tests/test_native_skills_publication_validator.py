import copy
import unittest
from datetime import timedelta
from unittest.mock import patch
from scripts import validate_public_refresh_output as validator
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload
from tests import test_native_skills_publication as native_fixtures

class NativeSkillsValidatorTests(unittest.TestCase):
    def fixture(self,page='heartsaver'):
        helper=native_fixtures.NativeSkillsPublicationTests();case=helper.fixture(page)
        return case,public_selector_availability_payload(helper.publish(case))
    def row(self,feed):return feed['dates'][0]['startTimes'][0]['courses'][0]
    def validate(self,feed,now):
        with patch.object(validator,'load_json',return_value=feed):return validator.validate_selector(feed['pageKey'],set(),now=now)
    def test_three_real_generated_feeds_pass_strict_validator(self):
        for page in ['heartsaver','arc','hsi']:
            case,feed=self.fixture(page);self.assertGreater(self.validate(feed,case.now)['offers'],0)
    def test_version_scope_trace_timing_context_and_original_proof_are_required(self):
        case,original=self.fixture()
        for changes in [{'authority':'wrong'},{'nativeScopeId':'other'},{'nativeOfferId':'native-skills:'+'0'*64},{'capacity':4},{'qualificationPolicy':'guessed'},{'skillsContexts':['hsi-blended']},{'sourceSessionIds':['x','x']},{'sourceSessionIds':[3]},{'availabilityBlockId':' '},{'appointmentDayId':None},{'matchedContainerId':''},{'proofObservedAt':(case.now-timedelta(minutes=15)).isoformat()},{'proofObservedAt':case.now.replace(tzinfo=None).isoformat()},{'proofObservedAt':(case.now+timedelta(seconds=1)).isoformat()},{'durationMinutes':True},{'setupBufferMinutes':15}]:
            bad=copy.deepcopy(original);self.row(bad).update(changes)
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.validate(bad,case.now)
        later=case.now+timedelta(minutes=14);bad=copy.deepcopy(original)
        bad.update(generatedAt=later.isoformat(),validUntil=(later+timedelta(minutes=10)).isoformat())
        for day in bad['dates']:
            for time in day['startTimes']:
                for course in time['courses']:course['validUntil']=bad['validUntil']
        with self.assertRaisesRegex(ValueError,'original proof'):self.validate(bad,later)
    def test_owned_url_only_and_expected_query(self):
        case,original=self.fixture();url=self.row(original)['registrationUrl']
        for value in ['https://www.910cpr.com'+url,'//www.910cpr.com'+url,url+'#',url+'&x=1',url+'&course=509474',url+'&',url+'\n']:
            bad=copy.deepcopy(original);self.row(bad).update(registrationUrl=value,appointmentUrl=value)
            with self.subTest(url=value),self.assertRaises(ValueError):self.validate(bad,case.now)
        bad=copy.deepcopy(original);self.row(bad)['appointmentUrl']='/wrong/'
        with self.assertRaises(ValueError):self.validate(bad,case.now)

if __name__=='__main__':unittest.main()
