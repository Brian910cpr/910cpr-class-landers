import json,subprocess,urllib.request,datetime,pathlib
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def gh(path): return json.loads(subprocess.check_output(['gh','api',path],text=True))
def fetch(url):
 r=urllib.request.urlopen(urllib.request.Request(url,headers={'Cache-Control':'no-cache','User-Agent':'910CPR-read-only-continuity-audit'}),timeout=30)
 return r.status,r.geturl(),r.read()
def dt(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
repo='repos/Brian910cpr/910cpr-class-landers'
runs=gh(repo+'/actions/runs?branch=main&per_page=60')['workflow_runs']
pages=sorted([r for r in runs if r['name']=='pages build and deployment' and r['conclusion']=='success'],key=lambda r:r['updated_at'])[-8:]
result={'checkedAt':now(),'publications':[],'live':{},'limitations':'Pages updated_at is deployment completion proxy, not exact edge switch or continuous browser observation. GET only; no registration/payment submitted.'}
previous={}
for r in pages:
 row={'sha':r['head_sha'],'pagesRun':r['id'],'pagesCompletedAt':r['updated_at'],'families':{}}
 for family in ['bls','heartsaver']:
  try:
   p=json.loads(fetch('https://raw.githubusercontent.com/Brian910cpr/910cpr-class-landers/'+r['head_sha']+'/docs/data/block-selector-availability/'+family+'.json')[2])
   f={k:p.get(k) for k in ['generatedAt','validUntil','counts']}
   if family in previous:f['deliveryMarginSeconds']=(dt(previous[family])-dt(r['updated_at'])).total_seconds()
   previous[family]=p['validUntil'];row['families'][family]=f
  except Exception as e:row['families'][family]={'error':type(e).__name__}
 result['publications'].append(row)
for family in ['bls','heartsaver']:
 status,url,body=fetch('https://www.910cpr.com/data/block-selector-availability/'+family+'.json?audit='+now())
 p=json.loads(body); stamp=now()
 courses=[c for d in p['dates'] for s in d['startTimes'] for c in s['courses']]
 sample=next(c for c in courses if 'appointmentDayId=' in c.get('registrationUrl',''))
 try:
  status2,url2,body2=fetch(sample['registrationUrl'])
  handoffError=None
 except Exception as e:
  status2,url2,body2=None,sample['registrationUrl'],b''
  handoffError=str(e)
 pageStatus,pageUrl,html=fetch('https://www.910cpr.com/'+family)
 result['live'][family]={'observedAt':stamp,'httpStatus':status,'generatedAt':p['generatedAt'],'validUntil':p['validUntil'],'unexpired':dt(p['validUntil'])>dt(stamp),'counts':p.get('counts'),'sampleOffer':sample,'handoff':{'error':handoffError,'httpStatus':status2,'finalUrl':url2,'bodyBytes':len(body2),'containsForm':b'<form' in body2.lower()},'page':{'httpStatus':pageStatus,'url':pageUrl,'loadsFamilyFeed':('/data/block-selector-availability/'+family+'.json').encode() in html}}
result['publishers']=[{k:r[k] for k in ['id','name','event','created_at','updated_at','status','conclusion','head_sha']} for r in runs if r['name'] in ['Refresh admin availability','Refresh public site from Enrollware iCal']][:12]
out=pathlib.Path('data/audit/issue334_continuity_r21.json');out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
