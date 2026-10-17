import json, pathlib, hashlib, ast, sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
root=pathlib.Path(__file__).resolve().parents[2]
p=pathlib.Path(sys.argv[1])
out=root/'data/audit/issue334_probe_r57.json'
proof=json.loads((p/'proof.json').read_text())
sid='dfa08088-1266-4dd6-ad7d-14856b7f845a'
start=datetime.fromisoformat('2026-11-03T17:00:00+00:00')
end=datetime.fromisoformat('2026-11-03T19:00:00+00:00')
result={'observed_at':datetime.now(timezone.utc).isoformat(),'run_id':38546492384,'probe_commit':'4983a974a31043b6c21fe8e1383f18ff611a74c5','published':False,'canonical_session':{'id':sid,'start_at':start.isoformat(),'end_at':end.isoformat(),'location_id':'fd44e20f-af86-4198-ab7c-fa13dad6a7fd','resource_id':None,'method':'authenticated Supabase SELECT; no room identity inferred'},'pages':{},'artifact_sha256':{}}
for name in sorted(p.iterdir()):
    if name.suffix not in ('.json','.html'): continue
    result['artifact_sha256'][name.name]=hashlib.sha256(name.read_bytes()).hexdigest()
for key,row in proof['pages'].items():
    counts=row['counts']
    assert counts['input_windows']==counts['evaluated_windows'] and counts['failed_windows']==0
    assert not row['calculation_issue_counts']
    feed=json.loads((p/(key+'.json')).read_text())
    blocks=[b for b in feed['layeredLandscape']['occupiedBlocks'] if sid in b['source_ids']]
    assert any(datetime.fromisoformat(b['start'])==start and datetime.fromisoformat(b['end'])==end for b in blocks),key
    day=next((d for d in feed['dates'] if d['date']=='2026-11-03'),{'startTimes':[]})
    offers=[]
    for slot in day['startTimes']:
        for course in slot['courses']:
            if course['offerType']=='dynamic_appointment':
                s=datetime.fromisoformat('2026-11-03T'+slot['startTime']).replace(tzinfo=ZoneInfo('America/New_York'))
                e=datetime.fromisoformat(course['occupiedUntil'])
                assert e<=start or s>=end,(key,slot['startTime'],course['courseId'])
                offers.append({k:course.get(k) for k in ('courseId','startTime','schedulerConsumptionMinutes','cleanupBufferMinutes','occupiedUntil','sourceSessionIds','edgeIds','resource','appointmentDayId','registrationUrl')})
    result['pages'][key]={'counts':counts,'rejection_reasons':row['rejection_reasons'],'occupied_blocks':blocks,'november3_dynamic_offers':offers,'november3_patterns':row['day_patterns'].get('2026-11-03'), 'overlap_count':0}
for key in ['bls','heartsaver']:
    skills=[o for o in result['pages'][key]['november3_dynamic_offers'] if o['schedulerConsumptionMinutes']==60]
    assert {'11:00','14:00'}<={o['startTime'] for o in skills}
    assert all(o['cleanupBufferMinutes']==15 for o in skills)
for name in ['scripts/layered_publication_adapter.py','tests/test_layered_publication_adapter.py']:
    ast.parse((root/name).read_text(encoding='utf-8-sig'))
json.loads((root/'data/config/location_resource_map.json').read_text())
result['checks']='PASS: eight full window coverage checks; eight occupied interval checks; all November 3 dynamic offers nonoverlapping; BLS/HS 45+15 edge geometry; AST/JSON'
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(result['checks'])
