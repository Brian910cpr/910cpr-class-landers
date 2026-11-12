"""SQL DTO/proof -> shared runner -> renderer/validator. Synthetic stdin only."""
import json, sys
from datetime import datetime, timedelta
from scripts import run_native_publication as runner
from scripts.block_start_time_selector import seated_class_selector_offers, contextual_course, load_block_schedule_page_configs
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload, render_html
from scripts.validate_public_refresh_output import validate_native_skills_offer
from scripts.layered_publication_adapter import finalize
from tests.test_skills_session_509474 import SkillsOnlyTests
value=json.load(sys.stdin)
source=value['source']; proof=value['proof']; observed=value.get('observedAt',proof['observedAt'])
now=datetime.fromisoformat(observed.replace('Z','+00:00'))
demand={'generated_at':observed,'sessions':[source],'native_bls_skills_policy_proof':proof}
policy=dict(schemaVersion='native-publication-scope.v1',scopeId=runner.scope.SCOPE,enabled=True,
            blsSkillsEnabled=True,blsBundleEnabled=True,_blsSkillsProof=proof)
schedule=runner.retained_projection({'sessions':[]},demand,bls_skills_enabled=True,bls_bundle_enabled=True,now=now)
assert len(schedule['sessions'])==1
row=schedule['sessions'][0]
config=runner.native_page_config(load_block_schedule_page_configs()['bls'],bls_skills_enabled=True,bls_bundle_enabled=True)
source_fixture=SkillsOnlyTests();source_fixture.setUp()
option=next(o for o in config['course_options'] if o['course_id']=='509474')
course=contextual_course('509474',option,source_fixture.catalog,source_fixture.rules)
offers=seated_class_selector_offers(schedule_future_payload=schedule,selected_courses=[course],selected_course_ids={'509474'},course_rules={},native_policy=policy,reference_now=now)
assert len(offers)==1, offers
payload=dict(pageConfig=config,pageKey='bls',offers=offers,generatedAt=observed,validUntil=proof['validUntil'])
payload=runner.annotate_seated_offers(payload,schedule)
payload=runner.project_bls_offers(payload,schedule,policy,now)
payload=finalize(payload,now)
assert len(payload['offers'])==2
assert len({o['nativeOfferId'] for o in payload['offers']})==1
assert finalize(payload,now+timedelta(minutes=16))['offers']==[]
feed=public_selector_availability_payload(payload)
for day in feed['dates']:
 for slot in day['startTimes']:
  for offer in slot['courses']:
   runner.validate_bls_offer(offer,schedule,policy,now,0)
   validate_native_skills_offer(offer,'bls',day['date'],slot['startTime'],feed,now=now)
html=render_html(payload)
assert 'HeartCode BLS including online access' in html and 'course.registrationUrl' in html
print(json.dumps(feed))
