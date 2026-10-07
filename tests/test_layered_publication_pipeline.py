"""Actual endpoint projection -> selector route -> feed -> Chrome, entirely local."""
import copy
import json
import subprocess
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from tests import test_layered_publication_adapter as fixtures
from scripts import block_start_time_selector as selector
from scripts import publish_scheduling_landscape as landscape
from scripts.build_bls_block_schedule_pilot import render_html, public_selector_availability_payload

ROOT=Path(__file__).resolve().parents[1]


class LayeredPipelineTests(unittest.TestCase):
    def fixture(self):
        case=fixtures.LayeredPublicationTests();case.setUp()
        source=case.add(11,'17:00','19:00','359474',count=1)
        # Execute the existing TS durable-demand projection with fixture-only DB
        # rows and no credentials, fetch, mutations or network. Native counts are
        # authoritative here solely because this is an explicit local fixture.
        row=dict(id=source['source_event_id'],external_class_id='fixture-ew-id',
            external_course_id='359474',start_at=source['start'],end_at=source['end'],
            consumption_start_at=source['start'],consumption_end_at=source['end'],
            source_location_label=':: Wilmington; Shipyard Blvd - B',
            source_instructor_label='Brian Ennis',status='scheduled',source='landerware_event',
            registration_backend='landerware',visibility='public',registration_status='open',
            registrations=[dict(status='registered',registration_source='landerware')],
            landerware_sessions=[dict(id='fixture-workspace',starts_at=source['start'],ends_at=source['end'])])
        code="const {loadEndpoint}=require('./tests/helpers/canonical_demand_endpoint.cjs');const fs=require('fs');const row=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(loadEndpoint(()=>{throw Error('network forbidden')}).projectDemand(row)));"
        projected=json.loads(subprocess.run(['node','-e',code],input=json.dumps(row),text=True,
            capture_output=True,check=True,cwd=ROOT).stdout)
        self.assertTrue(projected['count_available']);self.assertEqual(projected['active_registration_count'],1)
        catalog={str(c['course_id']):dict(c,appointment_eligible=True,appointment_allowed=True,
            duration_minutes=120 if c['kind']=='full' else 45,scheduler_consumption_minutes=150 if c['kind']=='full' else 60,
            setup_buffer_minutes=0,cleanup_buffer_minutes=30 if c['kind']=='full' else 15) for c in case.courses}
        page=copy.deepcopy(case.page);page['allowed_course_ids']=['329495','209809']
        snapshot=dict(generated_at=case.now.isoformat(),availability_blocks=[],layered_commitment_coverage=case.coverage)
        inputs={selector.LOCATION_RESOURCE_MAP_PATH:case.resources,selector.COURSE_CATALOG_PATH:{},
            selector.PEOPLE_CATALOG_PATH:{},selector.APPOINTMENT_CONTAINERS_PATH:{},
            selector.SESSIONS_CURRENT_PATH:{'sessions':[]},selector.SCHEDULE_FUTURE_PATH:{'sessions':[]},
            selector.COURSE_RULES_PATH:{},selector.PUBLIC_LOCATION_POLICY_PATH:{},
            selector.PUBLIC_OFFER_POLICY_PATH:dict(minimum_lead_hours=0,maximum_days_out=30),
            ROOT/'data/config/layered_scheduling_policy.json':case.policy}
        with ExitStack() as stack:
            patches=dict(require_current_live_availability_snapshot=lambda:snapshot,
                load_block_schedule_page_configs=lambda:{'heartsaver':page},
                read_required_json=lambda path:copy.deepcopy(inputs[path]),
                load_publication_demand=lambda root:{'sessions':[projected]},
                sessions_with_canonical_demand=lambda rows:(rows,{}),
                course_rules_by_id=lambda value:catalog,courses_by_id=lambda value:catalog,
                people_lookup=lambda value:{},active_containers=lambda value:[{'fixture':True}],
                selected_public_page_live_windows=lambda snap,res:(case.windows,{'available_blocks_read':1}),
                window_datetimes=lambda window:(case.at(11,'00:00').replace(tzinfo=None),case.at(12,'00:00').replace(tzinfo=None)),
                selector_reference_datetime=lambda:case.now.replace(tzinfo=None),
                public_location_allowed=lambda loc,policy:True,public_policy_reasons=lambda *args,**kwargs:[],
                find_url=lambda window,start,cid,*unused:('fixture-day','fixture-container',
                    f'https://fixture.test/enroll?appointmentDayId=fixture-day&courseId={cid}&startTime={start:%H:%M}',None))
            for name,value in patches.items():stack.enter_context(patch.object(selector,name,value))
            payload=selector.build_block_schedule_page(page)
        self.assertEqual({o['startTime'] for o in payload['offers'] if o['courseId']=='209809'},{'14:30','19:00'})
        self.assertTrue(payload['layeredDiagnostics']['reports'][0]['blocks'])
        return case,payload

    def test_durable_projection_selector_feed_and_landscape_share_decisions(self):
        case,payload=self.fixture()
        feed=public_selector_availability_payload(payload)
        cells=[landscape.compact_offer(o,'heartsaver') for o in payload['offers']]
        self.assertEqual({(c['date'],c['startTime'],c['courseId']) for c in cells},
            {(d['date'],t['startTime'],c['courseId']) for d in feed['dates'] for t in d['startTimes'] for c in t['courses']})
        self.assertTrue(all(c['edgeIds'] and c['sourceSessionIds'] for c in cells))

    def test_public_feed_preserves_blocks_and_offer_consumption_without_private_fields(self):
        case,payload=self.fixture()
        payload['layeredDiagnostics']['projected_sources'][0].update(
            student_name='private participant',course_title='private calendar title',description='private notes')
        feed=public_selector_availability_payload(payload)
        self.assertTrue(feed['layeredLandscape']['occupiedBlocks'])
        self.assertTrue(any(s['role']=='anchor' for s in feed['layeredLandscape']['sources']))
        encoded=json.dumps(feed)
        for value in ['private participant','private calendar title','private notes']:
            self.assertNotIn(value,encoded)
        offers=[c for d in feed['dates'] for t in d['startTimes'] for c in t['courses']]
        self.assertTrue(all(c.get('registrationUrl') for c in offers))
        self.assertTrue(any(c.get('cleanupBufferMinutes')==30 for c in offers))
        self.assertTrue(feed['layeredLandscape']['offersAreAlternatives'])

    def test_public_landscape_keeps_unknown_count_and_generic_blocking(self):
        from scripts.build_bls_block_schedule_pilot import public_layered_landscape
        payload={'layeredDiagnostics':{'projected_sources':[{'source_event_id':'unknown','course_id':'209806','count_available':False,'active_registration_count':0},{'source_event_id':'calendar','source_file':'calendar_blocked','description':'private'}]}}
        result=public_layered_landscape(payload)
        self.assertIsNone(result['sources'][0]['registeredCount'])
        self.assertFalse(result['sources'][0]['countAvailable'])
        self.assertEqual(result['sources'][1]['role'],'blocking')
        self.assertNotIn('private',json.dumps(result))

    def test_actual_desktop_mobile_customer_ui_has_full_heartsaver_edges_and_links(self):
        case,payload=self.fixture();html=render_html(payload);feed=public_selector_availability_payload(payload)
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(channel='chrome',headless=True)
            try:
                for width in [1440,390]:
                    with self.subTest(width=width):
                        page=browser.new_page(viewport={'width':width,'height':1000},timezone_id='America/New_York')
                        page.add_init_script("const NativeDate=Date;const fixtureNow=NativeDate.parse('2026-10-05T16:00:00Z');window.Date=class extends NativeDate{constructor(...args){super(...(args.length?args:[fixtureNow]));}static now(){return fixtureNow;}};")
                        errors=[];requests=[];page.on('pageerror',lambda error:errors.append(str(error)))
                        def local(route):
                            url=route.request.url;requests.append(url);path=urlparse(url).path
                            if path=='/heartsaver.html':route.fulfill(status=200,content_type='text/html',body=html)
                            elif path.startswith('/data/block-selector-availability/'):
                                route.fulfill(status=200,content_type='application/json',body=json.dumps(feed))
                            elif path.startswith('/assets/') and (ROOT/'docs'/path.lstrip('/')).is_file():
                                route.fulfill(status=200,path=str(ROOT/'docs'/path.lstrip('/')))
                            else:route.fulfill(status=204,body='')
                        page.route('**/*',local)
                        page.goto('https://fixture.test/heartsaver.html',wait_until='domcontentloaded')
                        page.wait_for_function("typeof availabilityReady==='function' && availabilityReady()")
                        button=page.locator('[data-course-id="209809"]')
                        if not button.is_visible():page.locator('#show-all-toggle').check()
                        button.click()
                        self.assertEqual(page.evaluate('filteredDates().flatMap(d=>d.startTimes.map(t=>t.startTime))'),['14:30','19:00'])
                        self.assertIn('120 min',page.locator('#course-list').inner_text())
                        self.assertNotIn('Scheduled class',page.locator('#course-list').inner_text())
                        self.assertTrue(all('available option' in label for label in page.locator('#start-list button').evaluate_all("els=>els.map(e=>e.getAttribute('aria-label'))")))
                        href=page.locator('#course-list a').first.get_attribute('href')
                        self.assertIn('courseId=209809',href);self.assertIn('appointmentDayId=fixture-day',href)
                        self.assertFalse(errors)
                        self.assertTrue(any('/assets/resolved-selector-availability.js' in url for url in requests))
                        page.close()
            finally:browser.close()


if __name__=='__main__':unittest.main()
