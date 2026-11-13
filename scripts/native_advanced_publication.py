"""Advanced native publication bridge; only accepted existing scheduler results.
No new scheduler, inferred qualification, guessed buffers or external container.
"""
from datetime import timedelta, timezone
from hashlib import sha256
import json
import re
from urllib.parse import urlencode
from scripts.native_publication_scope import instant
COURSES={'241108':'acls','209818':'acls','209805':'pals','251496':'pals'}
SCHEMA='native-advanced-publication-policy.v1'
SCOPE='qualified-advanced-shipyard-b.v1'
def active(policy,page):
    return policy.get('enabled') is True and policy.get('advancedFullEnabled') is True and page in {'acls','pals'}
def validate_proof(proof,now):
    if not isinstance(proof,dict) or proof.get('schemaVersion')!=SCHEMA or set(proof.get('courses',{}))!=set(COURSES):
        raise ValueError('native_advanced_policy_proof_required')
    observed,lease,current=instant(proof['observedAt']),instant(proof['validUntil']),instant(now)
    if not observed<=current<lease<=observed+timedelta(minutes=15):raise ValueError('native_advanced_policy_proof_expired')
    for cid,p in proof['courses'].items():
        if type(p.get('materializationEnabled')) is not bool or type(p.get('nativePublicationEnabled')) is not bool:raise ValueError('native_advanced_policy_invalid')
        if not p['nativePublicationEnabled']:continue
        if (not p['materializationEnabled'] or p.get('pageKey')!=COURSES[cid] or p.get('nativeScopeId')!=SCOPE or
            p.get('coursePolicyKey')!='advanced-full:'+cid+'.v1' or not re.fullmatch(r'[a-f0-9-]{36}',str(p.get('canonicalCourseId',''))) or
            p.get('instructionMinutes')!=240 or any(type(p.get(k)) is not int or p[k]<0 for k in ['setupMinutes','cleanupMinutes']) or
            p['setupMinutes']!=0 or type(p.get('maxStudents')) is not int or p['maxStudents']<1 or not p.get('resource') or not p.get('location') or not p.get('instructors')):
            # Current layered model has no pre-instruction setup interval. Do not
            # silently drop one or label it teaching: keep that course closed.
            raise ValueError('native_advanced_policy_invalid_or_unsupported_setup')
    return proof

def course_policy(policy,cid,now):
    proof=validate_proof(policy.get('_advancedProof'),now)
    row=proof['courses'].get(str(cid))
    return row if row and row['nativePublicationEnabled'] else None

def qualified(policy,window,course,now):
    p=course_policy(policy,str(course['course_id']),now)
    if p is None:return False
    return any(t['name']==window.get('instructor_name') and t['availabilityPersonId']==str(window.get('person_id')) and instant(t['qualificationValidThrough'])>=instant(window['end']) for t in p['instructors'])

def duration_policy(policy,scheduler,now):
    result=dict(scheduler,course_duration_overrides=dict(scheduler.get('course_duration_overrides',{})))
    for cid in COURSES:
        p=course_policy(policy,cid,now)
        if p:result['course_duration_overrides'][cid]={'instruction_minutes':240,'cleanup_minutes':p['cleanupMinutes'],'evidence':'verified native advanced runtime policy '+p['coursePolicyKey']}
    return result

def offer_fields(policy,candidate,report,window,now):
    cid=str(candidate['course']);p=course_policy(policy,cid,now)
    if p is None:raise ValueError('native_advanced_course_not_ready')
    if candidate not in report.get('accepted',[]):raise ValueError('native_advanced_candidate_not_accepted')
    start,end,teaching=map(instant,[candidate['start'],candidate['end'],candidate['instruction_end']])
    if teaching-start!=timedelta(minutes=240) or end-teaching!=timedelta(minutes=p['cleanupMinutes']) or candidate['location']!=p['resource'] or window.get('location_name')!=p['location']:
        raise ValueError('native_advanced_occupied_bounds_changed')
    teachers=[t for t in p['instructors'] if t['name']==candidate['instructor'] and t['availabilityPersonId']==str(window.get('person_id'))]
    if len(teachers)!=1:raise ValueError('native_advanced_instructor_identity_required')
    teacher=teachers[0]
    if instant(teacher['qualificationValidThrough'])<end:raise ValueError('native_advanced_qualification_expired')
    proofs=[x for x in report.get('native_calendar_coverage',[]) if x.get('instructor')==candidate['instructor'] and x.get('location')==candidate['location'] and instant(x['start'])<=start and end<=instant(x['end'])]
    if not proofs:raise ValueError('native_advanced_complete_calendar_coverage_required')
    observed=min(instant(x['observed_at']) for x in proofs)
    lease=min(instant(report['valid_until']),instant(policy['_advancedProof']['validUntil']),observed+timedelta(minutes=15))
    observed=min(observed,instant(policy['_advancedProof']['observedAt']))
    if not observed<=instant(now)<lease or lease>observed+timedelta(minutes=15):raise ValueError('native_advanced_source_proof_expired')
    source=str(window.get('calendar_source_key') or '')
    if source not in teacher.get('calendarSourceKeys',[]) or not re.fullmatch(r'[a-zA-Z0-9_.:-]{1,160}',source):raise ValueError('native_advanced_safe_calendar_source_required')
    bounds=[instant(window[k]) for k in ['start','end']]
    if not bounds[0]<=start<end<=bounds[1]:raise ValueError('native_advanced_availability_fit_required')
    identity=[SCOPE,cid,p['canonicalCourseId'],teacher['id'],candidate['location'],start.isoformat(),end.isoformat()]
    selection='native-full:'+sha256(json.dumps(identity,separators=(',',':')).encode()).hexdigest()
    block='native-advanced-window:'+sha256(json.dumps([source,*[x.isoformat() for x in bounds]],separators=(',',':')).encode()).hexdigest()
    return dict(authority='native-full-course.v3',nativeScopeId=SCOPE,coursePolicyKey=p['coursePolicyKey'],canonicalCourseId=p['canonicalCourseId'],
      instructorId=teacher['id'],availabilityPersonId=teacher['availabilityPersonId'],calendarSourceKey=source,
      availabilityStartsAt=bounds[0].isoformat(),availabilityEndsAt=bounds[1].isoformat(),availabilityBlockId=block,
      occupiedFrom=start.isoformat(),proofObservedAt=observed.isoformat(),validUntil=lease.isoformat(),sourceSessionIds=[],selectionId=selection,
      registrationUrl='/register/checkout/?'+urlencode({'course':cid,'selectionId':selection}))

def claim_dto(offer,generated):
    """Exactly the normalizations used by advanced-course.mjs, not raw rows."""
    def iso(value):return instant(value).isoformat(timespec='milliseconds').replace('+00:00','Z')
    start=instant(offer['date']+'T'+offer['startTime']+':00'+_offset(offer['date'],offer['startTime']))
    return dict(kind='dynamic',authority=offer['authority'],courseNumber=str(offer['courseId']),selectionId=offer['selectionId'],localStart=offer['date']+'T'+offer['startTime'],startsAt=iso(start),endsAt=iso(start+timedelta(minutes=240)),consumptionStartsAt=iso(offer['occupiedFrom']),consumptionEndsAt=iso(offer['occupiedUntil']),
      **{k:offer[k] for k in ['instructor','instructorId','availabilityPersonId','resource','location','nativeScopeId','coursePolicyKey','canonicalCourseId','proofObservedAt','availabilityBlockId','sourceSessionIds','calendarSourceKey','availabilityStartsAt','availabilityEndsAt']},generatedAt=iso(generated),validUntil=iso(offer['validUntil']))
def _offset(day,clock):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    naive=datetime.fromisoformat(day+'T'+clock);zone=ZoneInfo('America/New_York')
    options={naive.replace(tzinfo=zone,fold=f).astimezone(timezone.utc) for f in (0,1) if naive.replace(tzinfo=zone,fold=f).astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)==naive}
    if len(options)!=1:raise ValueError('ambiguous_or_nonexistent_eastern_start')
    dt=next(iter(options)).astimezone(zone)
    return dt.strftime('%z')[:3]+':'+dt.strftime('%z')[3:]

def validate_public(offer,generated,proof,now):
    validate_proof(proof,now);cid=str(offer.get('courseId'));p=course_policy({'_advancedProof':proof},cid,now)
    if not p or offer.get('authority')!='native-full-course.v3' or offer.get('nativeScopeId')!=SCOPE or offer.get('coursePolicyKey')!=p['coursePolicyKey'] or offer.get('canonicalCourseId')!=p['canonicalCourseId'] or offer.get('offerType')!='dynamic_appointment' or offer.get('publicSelectable') is not True or any(k in offer for k in ['appointmentDayId','matchedContainerId']):raise ValueError('unadmitted_advanced_offer')
    dto=claim_dto(offer,generated);start,end=instant(dto['startsAt']),instant(dto['consumptionEndsAt'])
    teachers=[t for t in p['instructors'] if t['id']==offer.get('instructorId') and t['name']==offer.get('instructor') and t['availabilityPersonId']==offer.get('availabilityPersonId')]
    if len(teachers)!=1 or instant(teachers[0]['qualificationValidThrough'])<end:raise ValueError('unqualified_advanced_offer')
    source=str(offer.get('calendarSourceKey',''))
    if source not in teachers[0]['calendarSourceKeys'] or not re.fullmatch(r'[a-zA-Z0-9_.:-]{1,160}',source):raise ValueError('unsafe_advanced_calendar_source')
    observed,lease=instant(offer['proofObservedAt']),instant(offer['validUntil'])
    if not observed<=instant(now)<lease<=min(observed+timedelta(minutes=15),instant(proof['validUntil'])) or not instant(generated)<=instant(now)<instant(generated)+timedelta(minutes=15):raise ValueError('stale_advanced_offer')
    if offer.get('durationMinutes')!=240 or offer.get('setupBufferMinutes')!=0 or offer.get('cleanupBufferMinutes')!=p['cleanupMinutes'] or offer.get('schedulerConsumptionMinutes')!=240+p['cleanupMinutes'] or end-start!=timedelta(minutes=240+p['cleanupMinutes']) or instant(offer['occupiedFrom'])!=start or not instant(offer['availabilityStartsAt'])<=start<end<=instant(offer['availabilityEndsAt']) or start<instant(now)+timedelta(days=1) or start>instant(now)+timedelta(days=90):raise ValueError('advanced_offer_bounds_changed')
    if offer.get('resource')!=p['resource'] or offer.get('location')!=p['location']:raise ValueError('advanced_offer_venue_changed')
    raw=[SCOPE,cid,p['canonicalCourseId'],teachers[0]['id'],p['resource'],start.isoformat(),end.isoformat()]
    selection='native-full:'+sha256(json.dumps(raw,separators=(',',':')).encode()).hexdigest()
    if offer.get('selectionId')!=selection or offer.get('registrationUrl')!='/register/checkout/?'+urlencode({'course':cid,'selectionId':selection}):raise ValueError('advanced_offer_identity_changed')
    return dto
