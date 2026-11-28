import copy
import json
import subprocess
import unittest
import tempfile
from unittest.mock import patch
from pathlib import Path
from scripts import block_start_time_selector as selector
from scripts.build_bls_block_schedule_pilot import render_html, public_selector_availability_payload
from tests.test_layered_publication_adapter import LayeredPublicationTests

ROOT = Path(__file__).resolve().parents[1]

class SkillsOnlyTests(unittest.TestCase):
    def setUp(self):
        self.pages = selector.load_block_schedule_page_configs()
        self.catalog = selector.courses_by_id(json.loads((ROOT/'data/config/course_catalog.json').read_text()))
        self.rules = selector.course_rules_by_id(json.loads((ROOT/'data/inventory/course_consumption_rules.json').read_text()))

    def course(self, page):
        opt = next(o for o in self.pages[page]['course_options'] if o['course_id']=='509474')
        return selector.contextual_course('509474', opt, self.catalog, self.rules)

    def case(self):
        case = LayeredPublicationTests(); case.setUp()
        case.courses.append(self.course('heartsaver'))
        case.add(11,'12:00','14:00','329495',count=1)
        return case

    def test_45_instruction_15_cleanup_and_inherited_qualifications(self):
        for page,template in [('heartsaver','329495'),('arc','372258'),('hsi','445670')]:
            with self.subTest(page=page):
                course=self.course(page)
                self.assertEqual((course['duration_minutes'],course['cleanup_buffer_minutes'],course['scheduler_consumption_minutes']),(45,15,60))
                self.assertEqual(course['required_instructor_certifications'],self.catalog[template]['required_instructor_certifications'])
                self.assertEqual(course['course_family'],self.rules[template]['course_family'])
                self.assertEqual(course['schedule_page_option']['price'],55)
                for cid in ['209808','329495'] if page=='heartsaver' else [template]:
                    self.assertEqual(self.catalog[cid]['required_instructor_certifications'],course['required_instructor_certifications'])

    def test_exact_occupied_edges_keep_full_existing_interval_and_cleanup(self):
        case=self.case(); report=case.calculation()
        offers=[o for o in case.payload()['offers'] if o['courseId']=='509474']
        self.assertEqual({o['startTime'] for o in offers},{'11:00','14:00'})
        self.assertTrue(all(o['durationMinutes']==45 and o['schedulerConsumptionMinutes']==60 and o['cleanupBufferMinutes']==15 for o in offers))
        self.assertEqual(report['projected_sources'][0]['end'],case.at(11,'14:00').isoformat())
        case.add(11,'14:45','15:00',cid='210549')
        self.assertNotIn('14:00',{o['startTime'] for o in case.payload()['offers'] if o['courseId']=='509474'})

    def test_unqualified_and_stale_coverage_fail_closed(self):
        from scripts.layered_publication_adapter import calculate
        case=self.case()
        # Brian has a separate explicit family eligibility exception; use another instructor.
        case.windows[0]['instructor_name']='Other'; case.windows[0]['person_id']='other'
        case.coverage[0]['instructor']='Other'
        result=calculate(case.windows,case.sources,case.courses,case.policy,case.resources,case.now,
            lambda w:(w['start'],w['end']),lambda w,c:False,case.coverage)
        self.assertFalse(any(o['course']=='509474' for r in result['reports'] for o in r['accepted']))
        case.coverage[0]['valid_until']=case.now.isoformat()
        self.assertFalse(any(o['courseId']=='509474' for o in case.payload()['offers']))

    def test_native_date_route_does_not_need_external_container(self):
        case=self.case()
        day,container,url,error=selector.find_url(case.windows[0],case.at(11,'11:00'),'509474',[],{})
        self.assertIsNone(day); self.assertIsNone(container); self.assertIsNone(error)
        self.assertTrue(url.startswith('/register/skills-session/?'))
        self.assertNotIn('enrollware',url)

    def test_unconfigured_native_reservation_never_publishes_a_bookable_offer(self):
        from scripts.layered_publication_adapter import publish
        case=self.case()
        report=case.calculation()
        with tempfile.TemporaryDirectory(prefix='native_skills_disabled_',dir=ROOT.parent) as directory:
            with patch.object(selector,'ROOT',Path(directory)):
                result=publish(report,self.pages['heartsaver'],case.courses,case.windows,case.now,
                    lambda w,s,c:(None,None,'/register/skills-session/',None),
                    lambda s,c:selector.native_reservation_reasons(c))
        self.assertFalse(any(o['courseId']=='509474' for o in result['offers']))
        self.assertTrue(any('native_reservation_not_configured' in o.get('reasons',[]) for o in result['rejectedCourseStartTimes']))

    def test_publication_activation_requires_explicit_verified_evidence(self):
        from datetime import timedelta
        with tempfile.TemporaryDirectory(prefix='native_skills_activation_test_',dir=ROOT.parent) as directory:
            self.assertTrue(Path(directory).resolve().is_relative_to(ROOT.parent.resolve()))
            root=Path(directory);path=root/'data/config/native_skills_activation.json';path.parent.mkdir(parents=True)
            now=selector.selector_reference_datetime()
            with patch.object(selector,'ROOT',root):
                self.assertTrue(selector.native_reservation_reasons(self.course('heartsaver')))
                for activation in [{}, {'enabled':True}, {'schemaVersion':'native-skills-activation.v1','enabled':True,'evidence':'fixture','canonicalVerifiedAt':(now+timedelta(days=1)).isoformat()}]:
                    path.write_text(json.dumps(activation));self.assertTrue(selector.native_reservation_reasons(self.course('heartsaver')))
                path.write_text(json.dumps({'schemaVersion':'native-skills-activation.v1','enabled':True,'evidence':'EXPLICIT TEST ONLY','canonicalVerifiedAt':(now-timedelta(minutes=1)).isoformat()}))
                self.assertEqual(selector.native_reservation_reasons(self.course('heartsaver')),[])

    def run_customer_actions(self, generated, contexts):
        harness = r'''
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const resolver = require("./docs/assets/resolved-selector-availability.js");
const {generated, contexts} = JSON.parse(fs.readFileSync(0, "utf8"));
const now = Date.parse("2026-12-01T12:00:00Z");
Date.now = () => now;
const date = "2026-12-02", time = "13:00", location = "Wilmington; Shipyard Blvd";
const instructor = "Fixture Instructor";
const q = new URLSearchParams({course:"509474",date,startTime:time,location,instructor});
const href = "/register/skills-session/?" + q;
const fixture = {
  courseId:"509474", courseName:"Skills Session", date, startTime:time, location, instructor,
  availabilityBlockId:"synthetic-lease", offerType:"dynamic_appointment", publicSelectable:true,
  durationMinutes:45, schedulerConsumptionMinutes:60, cleanupBufferMinutes:15,
  registrationUrl:href, appointmentUrl:href, validUntil:"2026-12-01T12:10:00Z",
};
function run(key, overrides = {}, extra = {}) {
  let prevented = false, refreshed = false, actionContext;
  const link = {addEventListener(name, callback) {
    assert.equal(name, "click");
    callback({preventDefault() { prevented = true; }});
  }};
  const course = {...fixture, ...overrides};
  const env = {
    URL, document:{createElement() { return {}; }}, link, course,
    selectedDate:date, day:{date}, slot:{startTime:time},
    selectedSkillsContext:key, config:{fullWidth:true,skillsContexts:contexts},
    nativeClassCapabilities:{}, resolvedAvailability:{validUntil:"2026-12-01T12:20:00Z"},
    availabilityReady:() => true, loadResolvedAvailability:() => { refreshed = true; },
    isPastStart:(day,slot) => resolver.isPastStart(day,slot,resolver.businessNow("America/New_York",new Date(now))),
    ResolvedSelectorAvailability:{...resolver,registrationAction(...args) {
      actionContext = args[1]; return resolver.registrationAction(...args);
    }},
    ...extra,
  };
  vm.runInNewContext(generated + "\nglobalThis.notice = requestNotice?.textContent;", env);
  assert.equal(prevented, refreshed);
  return {link, notice:env.notice, prevented, actionContext};
}
function request(result) {
  assert.equal(result.link.textContent, "Request this class");
  assert.equal(new URL(result.link.href).protocol, "mailto:");
  assert.match(result.notice, /No seat is reserved/);
}
for (const {key} of contexts) {
  const result = run(key);
  assert.equal(result.actionContext.skillsContextVerified,true);
  if (["arc-blended","hsi-blended"].includes(key)) {
    assert.equal(result.actionContext.pagePath, key === "arc-blended" ? "/arc.html" : "/hsi.html");
    request(result);
    continue;
  }
  assert.equal(result.actionContext.pagePath,"/heartsaver.html");
  assert.equal(result.actionContext.familyContext,"heartsaver");
  assert.equal(result.link.textContent,"Schedule skills session");
  assert.match(result.notice,/does not collect payment/);
  assert.equal(result.prevented,false);
  const route = new URL(result.link.href);
  assert.equal(route.origin,"https://www.910cpr.com");
  assert.equal(route.pathname,"/register/skills-session/");
  assert.deepEqual(Object.fromEntries(route.searchParams),{
    course:"509474",date,startTime:time,location,instructor,skillsContext:key,context:"heartsaver",
  });
  for (const invalid of [
    {publicSelectable:false}, {isFull:true}, {registrationStatus:"canceled"},
    {durationMinutes:60}, {schedulerConsumptionMinutes:45}, {cleanupBufferMinutes:0},
    {availabilityBlockId:""}, {registrationUrl:"https://example.test"+href},
    {registrationUrl:href+"&course=509474"}, {appointmentUrl:href.replace(date,"2026-12-03")},
    {registrationUrl:href+"&skillsContext=pediatric&context=heartsaver"},
    {instructor:"Different Instructor"},
  ]) request(run(key,invalid));
  assert.equal(run(key,{validUntil:"2026-12-01T11:59:59Z"}).prevented,true);
  assert.equal(run(key,{}, {resolvedAvailability:{validUntil:"2026-12-01T11:59:59Z"}}).prevented,true);
  assert.equal(run(key,{}, {availabilityReady:() => false}).prevented,true);
  request(run(key,{}, {config:{fullWidth:false,skillsContexts:contexts}}));
}
const unknown = run("unknown");
assert.equal(unknown.actionContext.skillsContextVerified,false);
request(unknown);
'''
        result = subprocess.run(
            ["node", "-e", harness],
            input=json.dumps({"generated": generated, "contexts": contexts}),
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_context_placements_pediatric_preserved_no_upload_or_booking_claim(self):
        for page,contexts in [('heartsaver',['cpr-aed','first-aid-cpr-aed']),('arc',['arc-blended']),('hsi',['hsi-blended'])]:
            course=self.course(page)
            self.assertEqual([c['key'] for c in course['schedule_page_option']['skills_contexts']],contexts)
            case=self.case(); payload=case.payload(); payload['pageConfig']=self.pages[page]; payload['pageKey']=page
            html=render_html(payload)
            self.assertIn('skills-session-choice',html)
            self.assertIn('selectedSkillsContext',html)
            # Execute the action and click gate emitted by the real page renderer,
            # against the shared customer resolver instead of matching a literal URL.
            action_start = html.index('const action = ResolvedSelectorAvailability.registrationAction(')
            action_end = html.index('item.append(summary, badge, link);', action_start)
            configs = course['schedule_page_option']['skills_contexts']
            self.run_customer_actions(html[action_start:action_end], configs)
            self.assertNotIn('schedule#ct509474',html)
        pediatric=[o for o in self.pages['heartsaver']['course_options'] if o.get('family_group')=='pediatric-first-aid-cpr-aed']
        self.assertEqual({o['course_id'] for o in pediatric},{'351632','251545'})
        page=(ROOT/'docs/register/skills-session/index.html').read_text()
        self.assertIn('Your date has not been reserved',page)
        self.assertIn('form id="reservation" hidden',page)
        self.assertNotIn('type="file"',page)
        self.assertIn('SkillsReservationClient.reservationState',page)

if __name__=='__main__': unittest.main()
