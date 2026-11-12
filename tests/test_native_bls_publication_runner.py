"""Synthetic local tests: independently gated aliases share physical inventory."""
import copy
from datetime import timedelta
import json
from pathlib import Path
import unittest
from scripts import run_native_publication as runner
from scripts import native_publication_scope as scope
from scripts.block_start_time_selector import load_block_schedule_page_configs, contextual_course
from scripts.build_bls_block_schedule_pilot import render_html, public_selector_availability_payload
from tests.test_native_skills_publication import NativeSkillsPublicationTests
from tests.test_skills_session_509474 import SkillsOnlyTests
from tests.test_native_skills_publication_validator import NativeSkillsValidatorTests


class NativeBlsRunnerTests(unittest.TestCase):
    def fixture(self, skills=True, bundle=True):
        helper = NativeSkillsPublicationTests(); case = helper.fixture()
        proof = dict(schemaVersion=scope.BLS_PROOF, nativeScopeId=scope.SCOPE,
            observedAt=case.now.isoformat(), validUntil=(case.now+timedelta(minutes=15)).isoformat(),
            physicalCourseId='509474', context='bls-skills', profileKey='native_skills_shared', profileVersion=2,
            skillsEnabled=True, bundleEnabled=True, qualificationValidThrough=(case.now+timedelta(days=91)).isoformat(),
            instructionMinutes=45, cleanupMinutes=15, capacity=2, skillsCents=5500, bundleCents=9500)
        case.native_policy.update(skillsEnabled=False,blsSkillsEnabled=skills,blsBundleEnabled=bundle,_blsSkillsProof=proof)
        config = runner.native_page_config(load_block_schedule_page_configs()['bls'], bls_skills_enabled=skills, bls_bundle_enabled=bundle)
        source=SkillsOnlyTests(); source.setUp()
        option=next(o for o in config['course_options'] if o['course_id']=='509474')
        case.page=config; case.courses=[contextual_course('509474',option,source.catalog,source.rules)]
        payload=helper.publish(case)
        result=runner.project_bls_offers(payload, {'sessions':[]}, case.native_policy, case.now)
        return case,result

    def test_independent_choices_exact_prices_and_identity(self):
        ids=[]
        for skills,bundle,expected in [(True,False,{'509474'}),(False,True,{'210549'}),(True,True,{'509474','210549'})]:
            case,payload=self.fixture(skills,bundle)
            self.assertEqual({o['courseId'] for o in payload['offers']},expected)
            physical={}
            for o in payload['offers']:
                runner.validate_bls_offer(o, {'sessions':[]},case.native_policy,case.now,300)
                physical.setdefault(o['startTime'],set()).add(o['nativeOfferId'])
            self.assertTrue(all(len(v)==1 for v in physical.values()))
            ids.append(physical)
            options={o['course_id']:o for o in payload['pageConfig']['course_options']}
            self.assertEqual(set(options)&set(scope.BLS_PACKAGES),expected)
            for cid in expected:self.assertEqual(options[cid]['price'],55 if cid=='509474' else 95)
            NativeSkillsValidatorTests().validate(public_selector_availability_payload(payload),case.now)
            html=render_html(payload)
            self.assertIn('course.registrationUrl',html)
        self.assertEqual(ids[0],ids[1]);self.assertEqual(ids[1],ids[2])

    def test_default_off_render_is_byte_identical_and_allowlist_unchanged(self):
        pages=load_block_schedule_page_configs()
        a=runner.native_page_config(pages['bls'])
        b=runner.native_page_config(pages['bls'],bls_skills_enabled=False,bls_bundle_enabled=False)
        self.assertEqual(a,b)
        case,payload=self.fixture()
        payload['pageConfig']=a; payload['offers']=[]
        first=render_html(payload)
        payload['pageConfig']=b
        self.assertEqual(first.encode(),render_html(payload).encode())
        saved=json.loads((Path(runner.ROOT)/runner.POLICY).read_text())
        self.assertIs(saved['blsSkillsEnabled'],False);self.assertIs(saved['blsBundleEnabled'],False)
        self.assertEqual(len(runner.publication_paths()),6);self.assertEqual(len(runner.publication_paths(True)),15)
        for key in ('blsSkillsEnabled','blsBundleEnabled'):
            for value in (1,'true',None):
                with self.assertRaises(ValueError):runner.policy_enabled(dict(saved,**{key:value}))

    def test_missing_stale_changed_policy_and_package_cannot_publish(self):
        case,payload=self.fixture(); original=copy.deepcopy(payload['offers'][0])
        for proof in [None,{},dict(case.native_policy['_blsSkillsProof'],validUntil=case.now.isoformat()),
                      dict(case.native_policy['_blsSkillsProof'],skillsEnabled=False,bundleEnabled=False),
                      dict(case.native_policy['_blsSkillsProof'],profileVersion=3)]:
            policy=dict(case.native_policy,_blsSkillsProof=proof)
            self.assertFalse(runner.project_bls_offers(copy.deepcopy(payload),{'sessions':[]},policy,case.now)['offers'])
            with self.assertRaises(ValueError):runner.validate_bls_offer(original,{'sessions':[]},policy,case.now,0)
        for changes in [dict(checkoutPackage='legacy'),dict(profileVersion=4),dict(skillsContexts=['cpr-aed']),
                        dict(policyProofObservedAt=(case.now-timedelta(seconds=1)).isoformat()),
                        dict(validUntil=(case.now+timedelta(minutes=16)).isoformat())]:
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                runner.validate_bls_offer(dict(original,**changes),{'sessions':[]},case.native_policy,case.now,0)

    def test_bundle_unready_does_not_remove_skills(self):
        case,payload=self.fixture()
        case.native_policy['_blsSkillsProof']['bundleEnabled']=False
        result=runner.project_bls_offers(payload,{'sessions':[]},case.native_policy,case.now)
        self.assertEqual({o['courseId'] for o in result['offers']},{'509474'})

    def test_seated_context_filtering_preserves_one_session_and_shared_seat(self):
        case,_=self.fixture(); start=case.at(11,'11:00'); sid='lw-11111111-1111-4111-8111-111111111111'
        source=dict(canonical_session_id='canonical-skills',external_class_id=sid,external_course_id='509474',
            source='landerware_event',registration_backend='landerware',registration_authority='landerware-generated-session.v1',
            session_status='scheduled',registration_status='open',visibility='public',workspace_projection_status='current',
            count_available=True,active_registration_count=1,canonical_registered_count=0,held_seat_count=1,unreconciled_reserved_count=0,
            start_at=start.isoformat(),end_at=(start+timedelta(minutes=45)).isoformat(),consumption_start_at=start.isoformat(),
            consumption_end_at=(start+timedelta(minutes=60)).isoformat(),location_name=':: Wilmington; Shipyard Blvd',
            lead_instructor_name='Brian Ennis',course_name='Skills Session Only',
            native_skills_booking_admission=dict(schemaVersion='native-skills-session-booking.v1',publicCourseId='509474',
                profileKey='native_skills_shared',profileVersion=2,capacity=2,remaining=1,sourceSessionId=sid,
                identityWitness='a'*32,qualificationPolicy=scope.SKILLS_QUALIFICATION_POLICY,
                skillsContexts=['cpr-aed','first-aid-cpr-aed','arc-blended','hsi-blended','bls-skills']))
        demand=dict(generated_at=case.now.isoformat(),sessions=[source],native_bls_skills_policy_proof=case.native_policy['_blsSkillsProof'])
        schedule=runner.retained_projection({'sessions':[]},demand,bls_skills_enabled=True,bls_bundle_enabled=True,now=case.now)
        self.assertEqual(len(schedule['sessions']),1)
        row=schedule['sessions'][0];self.assertEqual(row['active_registration_count'],1)
        self.assertEqual(row['native_skills_booking_admission']['skillsContexts'],['bls-skills'])
        local=start.astimezone(scope.EASTERN)
        from scripts.block_start_time_selector import seated_class_selector_offers
        args=dict(schedule_future_payload=schedule,selected_courses=case.courses,
                  selected_course_ids={'509474'},course_rules={})
        self.assertEqual(seated_class_selector_offers(**args),[])
        offers=seated_class_selector_offers(**args,native_policy=case.native_policy,reference_now=case.now)
        self.assertEqual(len(offers),1)
        offer=offers[0]
        payload=runner.annotate_seated_offers({'pageKey':'bls','offers':[offer]},schedule)
        payload=runner.project_bls_offers(payload,schedule,case.native_policy,case.now)
        self.assertEqual(len(payload['offers']),2)
        self.assertEqual(len({o['nativeOfferId'] for o in payload['offers']}),1)
        for offer in payload['offers']:
            self.assertEqual(offer['remainingSeats'],1)
            runner.validate_bls_offer(offer,schedule,case.native_policy,case.now,300)
        old=runner.retained_projection(schedule,demand,skills_enabled=True,now=case.now)
        self.assertNotIn('bls-skills',old['sessions'][0]['native_skills_booking_admission']['skillsContexts'])
        self.assertEqual(old['sessions'][0]['active_registration_count'],1)
        off=runner.retained_projection(schedule,demand,now=case.now)
        self.assertFalse(off['sessions'][0]['public_direct_booking'])
        self.assertEqual(off['sessions'][0]['active_registration_count'],1)

if __name__=='__main__':unittest.main()
