import json,sys,types,subprocess,copy
from pathlib import Path
from tests import test_layered_publication_adapter as fixture
from scripts import layered_publication_adapter as current
from scripts.build_bls_block_schedule_pilot import render_html,public_selector_availability_payload
f=fixture.LayeredPublicationTests();f.setUp();f.windows=[];f.coverage=[];f.window(11,'10:00','15:00',next_day=False)
row=f.add(11,'12:00','13:00',count=0);seated=f.direct(row);seated.update(registrationUrl='https://fixture.test/direct-empty',appointmentUrl='https://fixture.test/direct-empty',appointmentDayId=None,publicSelectable=True,durationMinutes=45,displayStartTime='12:00 PM',displayDate='Sunday, October 11, 2026',location=':: Wilmington; Shipyard Blvd',deliveryMode='blended')
def build(adapter):
 c=adapter.calculate(f.windows,f.sources,f.courses,f.policy,f.resources,f.now,lambda w:(w['start'],w['end']),lambda w,c:True,f.coverage)
 return adapter.publish(c,f.page,f.courses,f.windows,f.now,lambda w,s,c:('fixture-day','fixture-container',f'https://fixture.test/enroll?appointmentDayId=fixture-day&courseId={c}&startTime={s:%H:%M}',None),lambda s,c:[],[seated])
after=build(current)
import scripts
saved={}
try:
 for name in ['layered_scheduling_engine','layered_selector_adapter','layered_publication_adapter']:
  full='scripts.'+name;saved[full]=sys.modules[full]
  m=types.ModuleType(full);m.__file__=str((Path('scripts')/(name+'.py')).resolve());sys.modules[full]=m;setattr(scripts,name,m)
  source=subprocess.check_output(['git','show','e663209d1e3db7d582079008250da622a2a01856:scripts/'+name+'.py'],text=True,encoding='utf-8')
  exec(compile(source,m.__file__,'exec'),m.__dict__)
 before=build(sys.modules['scripts.layered_publication_adapter'])
finally:
 for full,m in saved.items():sys.modules[full]=m;setattr(scripts,full.split('.')[-1],m)
receipt={'baseline':'e663209d1e3db7d582079008250da622a2a01856','scenario':'Confirmed-zero 12:00-13:00 class, verified room/instructor window 10:00-15:00, beyond 24 hours, no independent commitment','sources_unchanged':row['active_registration_count']==0}
for name,p in [('before',before),('after',after)]:
 receipt[name]={'feed':public_selector_availability_payload(p),'offers':[{'courseId':o['courseId'],'startTime':o['startTime'],'offerType':o['offerType'],'scheduleRole':o.get('scheduleRole'),'registrationUrl':o.get('registrationUrl')} for o in p['offers']], 'rejectionReasonCounts':p['rejectionReasonCounts'],'occupiedBlocks':p['layeredDiagnostics']['reports'][0]['blocks']}
 Path('data/audit/v2_empty_window_'+name+'.html').write_text(render_html(p),encoding='utf-8')
 Path('.test-tmp/v2_empty_window_'+name+'_feed.json').write_text(json.dumps(public_selector_availability_payload(p)),encoding='utf-8')
Path('data/audit/v2_empty_window_before_after.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
