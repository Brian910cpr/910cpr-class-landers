"""Synthetic DTO -> exact runner/selector/compact validator. No network or files."""
import json,sys
from datetime import datetime, timedelta
from scripts import run_native_publication as runner
from scripts.block_start_time_selector import seated_class_selector_offers
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload, render_html
from scripts.validate_public_refresh_output import validate_native_skills_offer
from scripts.generate_dynamic_offers import normalize_occupancy
from scripts.layered_publication_adapter import finalize
from tests.test_native_skills_publication import NativeSkillsPublicationTests
source=json.load(sys.stdin)
now=datetime.fromisoformat(sys.argv[1].replace('Z','+00:00'))
demand={'generated_at':sys.argv[1],'sessions':[source]}
closed=runner.retained_projection({'sessions':[]},demand)
assert closed['sessions'][0]['public_direct_booking'] is False
schedule=runner.retained_projection({'sessions':[]},demand,skills_enabled=True)
assert len(schedule['sessions'])==1
row=schedule['sessions'][0]
assert row['active_registration_count']==1 and row['public_direct_booking'] is True
blocks=normalize_occupancy(schedule,'synthetic');assert len(blocks)==1 and blocks[0]['end']>blocks[0]['start']
feeds={}
for page in ['heartsaver','arc','hsi']:
 fixture=NativeSkillsPublicationTests().fixture(page)
 offers=seated_class_selector_offers(schedule_future_payload=schedule,selected_courses=fixture.courses,selected_course_ids={'509474'},course_rules={})
 assert len(offers)==1, (page,offers)
 offer=offers[0]
 payload={'pageConfig':runner.native_page_config(fixture.page,page),'pageKey':page,'offers':offers,'generatedAt':sys.argv[1],'validUntil':row['native_skills_booking_admission']['validUntil'],
  'dates':[{'date':offer['date'],'startTimes':[{'startTime':offer['startTime'],'courses':offers}]}]}
 runner.annotate_seated_offers(payload,schedule)
 payload=finalize(payload,now)
 assert len(payload["offers"])==1
 assert finalize(payload,now+timedelta(minutes=16))["offers"] == []
 compact=public_selector_availability_payload(payload)
 c=compact['dates'][0]['startTimes'][0]['courses'][0]
 runner.validate_skills_seated_offer(c,schedule,page,now,0)
 validate_native_skills_offer(c,page,offer['date'],offer['startTime'],compact,now=now)
 assert c['remainingSeats']==1 and c['capacity']==2 and c['offerType']=='seated_class'
 html=render_html(payload)
 assert 'native-skills-seated.v1' in html and 'native-skills-seats2' in html
 assert "selection.set('selectionId'" in html
 feeds[page]=compact
print(json.dumps(feeds))
