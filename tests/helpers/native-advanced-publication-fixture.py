"""Synthetic stdin-to-feed integration fixture. No network or writes."""
import json,sys
from datetime import datetime,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts import native_advanced_publication as advanced
from scripts.layered_publication_adapter import calculate,publish
from scripts.layered_selector_adapter import aware
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload
root=Path(__file__).resolve().parents[2];data=json.load(sys.stdin);proof=data['proof'];p=proof['courses']['241108'];teacher=p['instructors'][0];now=advanced.instant(proof['observedAt']);day=(now.astimezone(ZoneInfo('America/New_York'))+timedelta(days=20)).date().isoformat()
policy={'schemaVersion':'native-publication-scope.v1','enabled':True,'advancedFullEnabled':True,'_advancedProof':proof}
scheduler=json.loads((root/'data/config/layered_scheduling_policy.json').read_text());scheduler.update(mode='active_local_v2',primary_resource=p['resource']);scheduler=advanced.duration_policy(policy,scheduler,now);scheduler['native_publication_scope']=policy
resources={'locations':[{'canonical_public_location':p['location'],'aliases':[],'internal_resources':[{'resource_name':p['resource']}]}]}
window={'source_availability_window':'synthetic-window','instructor_name':teacher['name'],'person_id':teacher['availabilityPersonId'],'calendar_source_key':teacher['calendarSourceKeys'][0],'location_name':p['location'],'start':day+'T13:00:00-05:00','end':day+'T18:00:00-05:00'}
# Use the actual Eastern offset for the chosen test date, not a machine-local clock.
for key in ['start','end']:window[key]=datetime.fromisoformat(window[key][:19]).replace(tzinfo=ZoneInfo('America/New_York')).isoformat()
coverage=[dict(status='known_complete',instructor=teacher['name'],location=p['resource'],start=window['start'],end=window['end'],observed_at=proof['observedAt'],valid_until=proof['validUntil'],freshness_minutes=15,source_ids=teacher['calendarSourceKeys'])]
course={'course_id':'241108','course_family':'ACLS','kind':'full'}
calc=calculate([window],data['occupancy'],[course],scheduler,resources,now,lambda w:(aware(w['start']),aware(w['end'])),lambda w,c:advanced.qualified(policy,w,c,now),coverage,{})
payload=publish(calc,{'page_key':'acls','output_path':'docs/acls.html'},[course],[window],now,lambda *args:(_ for _ in ()).throw(AssertionError('external URL must not be used')),lambda *args:[],native_policy=policy)
json.dump({'feed':public_selector_availability_payload(payload),'claims':[advanced.claim_dto(o,payload['generatedAt']) for o in payload['offers']]},sys.stdout)
