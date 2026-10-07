"""Incremental, local V2 calculation cache; publication still validates live inputs.

Cache resource windows rather than rewriting the existing scheduling engine.
Booking removals/moves invalidate old and new scopes through input fingerprints.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
import hashlib
import json
from scripts.layered_selector_adapter import aware
from scripts.layered_publication_adapter import calculate, project_sources, SCHEMA
from scripts.fetch_canonical_scheduling_demand import _atomic_write_json

VERSION = 'layered-day-cache.v1'
ZONE = ZoneInfo('America/New_York')


def pack(value):
    if isinstance(value, datetime):
        return {'__cache_datetime__': value.isoformat()}
    if isinstance(value, dict):
        return {k: pack(v) for k,v in value.items()}
    if isinstance(value, (list, tuple)):
        return [pack(v) for v in value]
    return value


def unpack(value):
    if isinstance(value, dict):
        if set(value) == {'__cache_datetime__'}:
            return aware(value['__cache_datetime__'])
        return {k: unpack(v) for k,v in value.items()}
    if isinstance(value, list):
        return [unpack(v) for v in value]
    return value


def digest(value):
    return hashlib.sha256(json.dumps(pack(value),sort_keys=True,separators=(',',':')).encode()).hexdigest()


def scoped_sources(rows, start, end, travel):
    # Include whole local days, transitions and transitively connected occupancy.
    # Unresolved bounds are never discarded to manufacture free time.
    lower = start.astimezone(ZONE).replace(hour=0,minute=0,second=0,microsecond=0)-timedelta(minutes=travel)
    upper = (end.astimezone(ZONE)-timedelta(microseconds=1)).replace(hour=0,minute=0,second=0,microsecond=0)+timedelta(days=1,minutes=travel)
    chosen = {}
    changed = True
    while changed:
        changed = False
        for index,row in enumerate(rows):
            if index in chosen: continue
            try:
                a,b = aware(row['start']),aware(row['end'])
                if b <= a: raise ValueError('unresolved')
            except (KeyError,ValueError,TypeError):
                chosen[index]=row
                continue
            if a <= upper and b >= lower:
                chosen[index]=row
                new_lower,new_upper=min(lower,a-timedelta(minutes=travel)),max(upper,b+timedelta(minutes=travel))
                if (new_lower,new_upper)!=(lower,upper):
                    lower,upper=new_lower,new_upper;changed=True
    return [chosen[i] for i in sorted(chosen)]


def cached_calculate(windows, occupancy, courses, policy, resources, now, interval,
                     qualified, coverage, travel_minutes=None, *, cache_dir, horizon_days=90):
    now=aware(now)
    horizon_start=now.astimezone(ZONE).replace(hour=0,minute=0,second=0,microsecond=0)
    horizon_end=horizon_start+timedelta(days=horizon_days)
    if not 1 <= horizon_days <= 90: raise ValueError('cache horizon must be 1..90 days')
    cache_dir=Path(cache_dir)
    travel=max([0]+[int(v) for v in (travel_minutes or {}).values() if isinstance(v,(int,float)) and v>=0])
    code=digest([Path(__file__).read_text(), *[Path(__file__).with_name(name).read_text() for name in
        ('layered_publication_adapter.py','layered_selector_adapter.py','layered_scheduling_engine.py','layered_resource_readiness.py')]])
    reports=[];issues=[];hits=0;rebuilt=[];selected=[]
    for index,original in enumerate(windows):
        start,end=map(aware,interval(original))
        if end<=horizon_start or start>=horizon_end: continue
        window=dict(original)
        # Clipping only at rolling horizon boundaries; preserve ordinary windows.
        start,end=max(start,horizon_start),min(end,horizon_end)
        window.update(start=start.isoformat(),end=end.isoformat())
        window.setdefault('source_availability_window',str(index))
        selected.append(window)
        rows=scoped_sources(occupancy,start,end,travel)
        proofs=[]
        for proof in coverage or []:
            try:
                if aware(proof['end'])<=start or aware(proof['start'])>=end: continue
            except (KeyError,ValueError,TypeError): pass
            proofs.append(proof)
        qualifications=[bool(qualified(window,c)) for c in courses]
        signature=digest([VERSION,code,window,rows,courses,policy,resources,proofs,travel_minutes,qualifications])
        identity=digest([window['source_availability_window'],start.isoformat(),end.isoformat()])[:24]
        path=cache_dir/(start.astimezone(ZONE).date().isoformat()+'-'+identity+'.json')
        cached=None
        try:
            entry=json.loads(path.read_text(encoding='utf-8'))
            if (entry['version']==VERSION and entry['signature']==signature
                    and aware(entry['built_at'])<=now<aware(entry['expires_at'])
                    and entry['result_hash']==digest(entry['result'])):
                cached=unpack(entry['result'])
        except (OSError,ValueError,KeyError,TypeError): pass
        if cached is None:
            cached=calculate([window],rows,courses,policy,resources,now,
                lambda w:(w['start'],w['end']),qualified,proofs,travel_minutes)
            deadlines=[now+timedelta(minutes=5)]  # Failed/unknown proof retries remain bounded.
            leases=[r['valid_until'] for r in cached['reports'] if r['valid_until']>now]
            if leases: deadlines=[min(leases)]
            for report in cached['reports']:
                for candidate in report['accepted']:
                    deadline=aware(candidate['start'])-timedelta(minutes=policy.get('lead_minutes',1440))
                    if deadline>=now: deadlines.append(deadline+timedelta(microseconds=1))
            for proof in proofs:
                try:
                    observed=aware(proof['observed_at'])
                    if observed>now: deadlines.append(observed)
                except (KeyError,ValueError,TypeError): pass
            result=pack(cached)
            _atomic_write_json(path,dict(version=VERSION,signature=signature,built_at=now.isoformat(),
                expires_at=min(deadlines).isoformat(),result=result,result_hash=digest(result)))
            rebuilt.append(dict(date=start.astimezone(ZONE).date().isoformat(),window_id=window['source_availability_window']))
        else: hits+=1
        reports.extend(cached['reports']);issues.extend(cached['issues'])
    projected=project_sources(occupancy,{str(c['course_id']):c for c in courses})
    return dict(schema=SCHEMA,reports=reports,issues=issues,projected_sources=projected,
        counts=dict(input_sources=len(occupancy),normalized_sources=len(projected),input_windows=len(selected),
            evaluated_windows=len(reports),failed_windows=len(selected)-len(reports),uncertainty_issues=len(issues)),
        incremental_cache=dict(version=VERSION,horizon_days=horizon_days,hits=hits,rebuilt=rebuilt),
        selected_windows=selected)
