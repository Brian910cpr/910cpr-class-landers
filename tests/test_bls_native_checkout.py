import copy
import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from scripts import block_start_time_selector as selector

ROOT=Path(__file__).resolve().parents[1]

class BlsNativeCheckoutTests(unittest.TestCase):
    def test_staged_prices_distinguish_bundle_and_skills_without_disabling_legacy_routes(self):
        raw=json.loads((ROOT/'data/config/block_schedule_pages.json').read_text(encoding='utf-8'))['pages']['bls']
        legacy={o['course_id']:o['price'] for o in raw['course_options']}
        self.assertEqual(legacy,{'209806':75,'359474':75,'210549':55})
        native={o['course_id']:o['price'] for o in raw['native_checkout_course_options']}
        self.assertEqual(native,{'209806':75,'359474':75,'210549':95,'509474':55})
        self.assertEqual(next(o for o in raw['native_checkout_course_options'] if o['course_id']=='509474')['skills_contexts'],[{'key':'bls-skills','label':'BLS'}])

    def test_activation_requires_verified_explicit_bls_flag_and_preserves_full_class_duration(self):
        now=selector.selector_reference_datetime()
        with tempfile.TemporaryDirectory(prefix='bls_checkout_activation_',dir=ROOT.parent) as tmp:
            root=Path(tmp);p=root/'data/config/native_skills_activation.json';p.parent.mkdir(parents=True)
            with patch.object(selector,'ROOT',root):
                for enabled in [False,True]:
                    p.write_text(json.dumps({'schemaVersion':'native-skills-activation.v1','enabled':True,'evidence':'SYNTHETIC LOCAL ONLY','canonicalVerifiedAt':(now-timedelta(minutes=1)).isoformat(),'blsEnabled':enabled}),encoding='utf-8')
                    page=selector.load_block_schedule_page_configs()['bls']
                    self.assertEqual(len(page['course_options']),4 if enabled else 3)
                catalog=selector.courses_by_id(json.loads((ROOT/'data/config/course_catalog.json').read_text(encoding='utf-8')))
                rules=selector.course_rules_by_id(json.loads((ROOT/'data/inventory/course_consumption_rules.json').read_text(encoding='utf-8')))
                options={o['course_id']:o for o in page['course_options']}
                for cid in ['210549','509474']:
                    course=selector.contextual_course(cid,options[cid],catalog,rules)
                    self.assertEqual((course['duration_minutes'],course['cleanup_buffer_minutes'],course['scheduler_consumption_minutes'],course['default_capacity']),(45,15,60,2))
                    self.assertEqual(selector.native_reservation_reasons(course),[])
                for cid in ['209806','359474']:
                    course=selector.contextual_course(cid,options[cid],catalog,rules)
                    self.assertEqual(course['duration_minutes'],120)
                    self.assertEqual(course['schedule_page_option']['price'],75)

    def test_gate_aware_hubs_sessions_and_full_appointments(self):
        from scripts import native_bls_routes as routes
        from scripts import build_course_landers as landers
        # Sparse checkout lacks the operational supervisor package. This renderer
        # test never invokes reporting or writes generated pages.
        import sys, types
        reporter=types.ModuleType('supervisor.status_snapshot');reporter.write_status_snapshot=lambda *a,**k: None
        with patch.dict(sys.modules,{'supervisor':types.ModuleType('supervisor'),'supervisor.status_snapshot':reporter}):
            from scripts import build_index_and_sitemap as hubs
        from datetime import datetime, timezone
        from urllib.parse import parse_qs, urlsplit
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as tmp:
            root=Path(tmp);p=root/'data/config/native_skills_activation.json';p.parent.mkdir(parents=True)
            legacy='https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=10&startTime=09:00&courseId=209806'
            row={'session_id':'123456','course_id':'209806','registration_url':'https://coastalcprtraining.enrollware.com/enroll?id=123456','_parsed_start':datetime(2031,1,1,tzinfo=timezone.utc)}
            for gate in [False,True]:
                p.write_text(json.dumps({'schemaVersion':'native-skills-activation.v1','enabled':True,'blsEnabled':gate,'evidence':'LOCAL FIXTURE','canonicalVerifiedAt':'2026-01-01T00:00:00Z'}),encoding='utf-8')
                with patch.object(hubs,'ROOT',root),patch.object(selector,'ROOT',root),patch.object(landers,'REPO_ROOT',root):
                    for cid in ['209806','359474','210549','509474']:
                        url=routes.course_link(root,cid,legacy)
                        self.assertEqual(url,'/bls.html?course='+cid if gate else legacy)
                    self.assertEqual(routes.course_link(root,'440431',legacy),legacy)
                    self.assertEqual(routes.course_link(root,None,legacy),legacy)
                    self.assertEqual(routes.session_link(root,'209806','123456',legacy),'/register/?session=123456' if gate else legacy)
                    self.assertEqual(routes.session_link(root,'210549','123456',legacy),'/bls.html?course=210549' if gate else legacy)
                    self.assertNotIn('/register/',routes.session_link(root,'209806','bad/id',legacy))
                    for cid in ['209806','359474']:
                        url=routes.appointment_link(root,cid,'2031-01-01','09:00','Fixture place','Fixture instructor',legacy)
                        self.assertEqual(urlsplit(url).path,'/register/' if gate else '/enroll')
                        if gate:self.assertEqual(parse_qs(urlsplit(url).query)['course'],[cid])
                    self.assertEqual(routes.appointment_link(root,'210549','2031-01-01','09:00','','',legacy),legacy)
                    card=landers.session_card(row)
                    self.assertIn('/register/?session=123456' if gate else 'enroll?id=123456',card)
                    block=landers.build_session_blocks({'course_id':'210549','schedule_url':legacy},[])
                    self.assertIn('/bls.html?course=210549' if gate else 'appointment.aspx',block)
                    with patch.object(selector,'matching_container',return_value=({'container_id':'fixture'},10,None)):
                        result=selector.find_url({'location_name':'Fixture place','instructor_name':'Fixture instructor'},datetime(2031,1,1,9),'209806',[],{})
                        self.assertEqual(result[0],10)
                        self.assertEqual(urlsplit(result[2]).path,'/register/' if gate else '/enroll')
                    rendered=hubs.render_course_session_rows([row])
                    self.assertIn('/register/?session=123456' if gate else '/classes/123456.html#ForwardToEnrollware',rendered)
                    body=hubs.render_course_page_body({'course_name':'BLS Provider','primary_course_id':'209806','parent_hub':'/bls.html'},[])
                    self.assertIn('/bls.html?course=209806' if gate else 'href="/bls.html"',body)
            p.write_text('{}',encoding='utf-8');self.assertFalse(routes.enabled(root))

if __name__=='__main__':unittest.main()
