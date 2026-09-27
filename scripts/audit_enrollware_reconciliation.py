"""PII-free owner alarm for the existing #297 migration bridge."""
import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


def audit(health, projection):
    sessions=health.get('sessions',[])
    known={str(s['external_class_id']) for s in sessions if s.get('canonical_session_id')}
    non_sessions=[{k:s.get(k) for k in ('external_class_id','non_session_classification','approved_location_key')}
                  for s in sessions if s.get('status')=='classified_non_session' and not s.get('canonical_session_id')]
    non_session_ids={str(s['external_class_id']) for s in non_sessions}
    gaps=[{k:s.get(k) for k in ('external_class_id','status','source_observed_at','reason')}
          for s in sessions if s.get('status')!='current' and str(s.get('external_class_id')) not in non_session_ids]
    for s in projection.get('sessions',[]):
        identity=str(s.get('external_class_id') or s.get('session_id') or '')
        if identity.isdigit() and identity not in known and identity not in non_session_ids and not any(x['external_class_id']==identity for x in gaps):
            gaps.append({'external_class_id':identity,'status':'committed_projection_without_canonical_session'})
    gaps.sort(key=lambda x:(x['external_class_id'],x['status']))
    signature=hashlib.sha256(json.dumps([(x['external_class_id'],x['status']) for x in gaps]).encode()).hexdigest()
    return {'checked_at':health.get('checked_at'),'freshness_minutes':60,'healthy':not gaps,
            'canonical_external_sessions':len(known),'non_session_sources':non_sessions,'gaps':gaps,'signature':signature}


def main():
    today=datetime.now(ZoneInfo('America/New_York')).date()
    url='https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/canonical-session-workspace'
    url+=f'?action=reconciliation-health&from={today-timedelta(days=1)}&to={today+timedelta(days=365)}'
    request=Request(url,headers={'x-hot-sync-admin-key':os.environ['HOT_SYNC_ADMIN_KEY']})
    with urlopen(request,timeout=45) as response: health=json.load(response)
    with urlopen('https://www.910cpr.com/data/admin_schedule.json',timeout=30) as response: projection=json.load(response)
    report=audit(health,projection)
    output=Path(os.environ.get('RECONCILIATION_AUDIT_PATH','data/audit/enrollware_reconciliation_health.json'))
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'healthy':report['healthy'],'gap_count':len(report['gaps']),'signature':report['signature']}))
    return 0 if report['healthy'] else 1

if __name__=='__main__': raise SystemExit(main())
