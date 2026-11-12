"""Existing canonical pediatric sessions only; no scheduler or external fallback.

The protected snapshot owns booking eligibility, geometry and occupied seats.
Runtime policy and local publication consent are independent, finite gates.
"""
from copy import deepcopy
from datetime import timedelta
import re
from scripts import native_publication_scope as scope

COURSE = '351632'
CANONICAL = '0689a2c5-c507-4e8a-b94c-15e5c5689e28'
KEY = 'heartsaver-pediatric-existing:351632.v1'
AUTHORITY = 'native-pediatric-session-booking.v1'
PROOF_KEY = 'native_pediatric_existing_session_policy_proof'


def validate_policy(p, now):
    if not isinstance(p, dict):
        raise ValueError('pediatric_policy_required')
    expected = dict(schemaVersion='native-pediatric-existing-session-policy.v1', publicCourseId=COURSE,
        canonicalCourseId=CANONICAL, coursePolicyKey=KEY, profileKey='native_heartsaver_351632_draft',
        packageCode='full-course', courseKey='aha-heartsaver-pediatric-fa-cpr-aed', pageKey='heartsaver', materializationEnabled=False, currency='usd')
    if any(type(p.get(k)) is not type(v) or p[k] != v for k,v in expected.items()):
        raise ValueError('pediatric_policy_identity_invalid')
    observed, expiry, now = scope.instant(p['observedAt']), scope.instant(p['validUntil']), scope.instant(now)
    if not observed <= now < expiry <= observed+timedelta(minutes=15):
        raise ValueError('pediatric_policy_stale')
    if any(type(p.get(k)) is not bool for k in ('existingSessionEnabled','nativePublicationEnabled')):
        raise ValueError('pediatric_policy_gate_invalid')
    if not p['existingSessionEnabled'] or not p['nativePublicationEnabled']:
        return None
    if (any(type(p.get(k)) is not int or p[k] < 0 for k in ('instructionMinutes','setupMinutes','cleanupMinutes','maxStudents','profileVersion','unitAmount'))
            or p['unitAmount'] < 1 or p['instructionMinutes'] < 1 or not 1 <= p['maxStudents'] <= 100 or p['profileVersion'] < 1
            or scope.instant(p['qualificationValidThrough']) <= now):
        raise ValueError('pediatric_policy_unverified')
    return p


def session_offer(source, observed, policy, now):
    """Project one protected canonical DTO, never infer authority from a page."""
    try:
        p = validate_policy(policy, now)
        b = source.get('native_pediatric_booking_admission')
        if not p or not isinstance(b, dict): return None
        start,end,occupied_start,occupied_end = [scope.instant(source[k]) for k in ('start_at','end_at','consumption_start_at','consumption_end_at')]
        sid = source['external_class_id']; count=source['active_registration_count']
        if not scope.instant(observed) <= scope.instant(now) < scope.instant(observed)+timedelta(minutes=15): return None
        observed=min(scope.instant(observed),scope.instant(p['observedAt']))
        expiry=min(observed+timedelta(minutes=15),scope.instant(p['validUntil']))
        if not observed <= scope.instant(now) < expiry or start <= scope.instant(now): return None
        if (source.get('registration_authority') != 'landerware-session-authority.v1'
            or source.get('registration_backend') != 'landerware' or source.get('session_status') not in {'scheduled','active'}
            or source.get('visibility') != 'public' or source.get('registration_status') != 'open'
            or source.get('workspace_projection_status') != 'current' or source.get('count_available') is not True
            or source.get('demand_status') != 'current' or source.get('external_course_id') != COURSE
            or source.get('course_key') != p['courseKey'] or not source.get('canonical_session_id')
            or b.get('schemaVersion') != AUTHORITY or b.get('publicCourseId') != COURSE
            or any(b.get(k) != p[k] or type(b.get(k)) is not type(p[k]) for k in ('canonicalCourseId','coursePolicyKey','profileKey','packageCode','profileVersion','instructionMinutes','setupMinutes','cleanupMinutes','unitAmount','currency'))
            or b.get('sourceSessionId') != sid or not re.fullmatch(r'(?:[0-9]+|lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})',sid)
            or not re.fullmatch(r'[a-f0-9]{32}',b.get('identityWitness',''))
            or any(type(v) is not int for v in (count,b.get('capacity'),b.get('remaining')))
            or not 0 <= count < b['capacity'] <= p['maxStudents'] or b['remaining'] != b['capacity']-count
            or end-start != timedelta(minutes=p['instructionMinutes'])
            or start-occupied_start != timedelta(minutes=p['setupMinutes'])
            or occupied_end-end != timedelta(minutes=p['cleanupMinutes'])
            or scope.instant(p['qualificationValidThrough']) < occupied_end
            or not source.get('location_name') or not source.get('lead_instructor_name')): return None
        local=start.astimezone(scope.EASTERN)
        url='/register/?session='+sid+'&course='+COURSE
        return dict(courseId=COURSE, publicCourseId=COURSE, canonicalCourseId=CANONICAL, coursePolicyKey=KEY,
            courseName='Heartsaver Pediatric First Aid CPR AED', courseFamily='Heartsaver', deliveryMode='classroom',
            price=p['unitAmount']/100, currency=p['currency'], authority=AUTHORITY, profileKey=p['profileKey'], profileVersion=p['profileVersion'], checkoutPackage='full-course',
            session_id=sid, canonicalSessionId=source['canonical_session_id'], identityWitness=b['identityWitness'],
            capacity=b['capacity'], remainingSeats=b['remaining'], date=local.date().isoformat(), startTime=local.strftime('%H:%M'),
            displayDate=local.strftime('%A, %B %d, %Y'), displayStartTime=local.strftime('%I:%M %p').lstrip('0'),
            startsAt=start.isoformat(), endsAt=end.isoformat(), occupiedFrom=occupied_start.isoformat(), occupiedUntil=occupied_end.isoformat(),
            durationMinutes=p['instructionMinutes'], setupBufferMinutes=p['setupMinutes'], cleanupBufferMinutes=p['cleanupMinutes'],
            schedulerConsumptionMinutes=p['instructionMinutes']+p['setupMinutes']+p['cleanupMinutes'],
            instructor=source['lead_instructor_name'], location=source['location_name'],
            sourceSessionIds=[sid], sourceAvailabilityBlock={'sessionId':sid}, availabilityBlockId='seated:'+sid,
            offerType='seated_class', publicSelectable=True, registrationUrl=url, appointmentUrl=url,
            proofObservedAt=observed.isoformat(), validUntil=expiry.isoformat())
    except (KeyError,ValueError,TypeError,OverflowError): return None


def project(payload, demand, local_policy, now):
    if payload.get('pageKey') != 'heartsaver': return payload
    if local_policy.get('pediatricExistingSessionEnabled') is not True and not any(str(o.get('courseId')) in {COURSE,'251545'} for o in payload.get('offers',[])):
        return payload
    from scripts.apply_anchor_policy import _rebuild_dates
    result=deepcopy(payload)
    # Neither stale cached choices nor a dynamic pediatric candidate is authority.
    offers=[o for o in result.get('offers',[]) if str(o.get('courseId')) not in {COURSE,'251545'}]
    if scope.active(local_policy) and local_policy.get('pediatricExistingSessionEnabled') is True:
        rows=demand.get('sessions',[])
        ids=[s.get('canonical_session_id') for s in rows if s.get('external_course_id') == COURSE]
        external=[s.get('external_class_id') for s in rows if s.get('external_course_id') == COURSE]
        for source in rows:
            if ids.count(source.get('canonical_session_id')) != 1 or external.count(source.get('external_class_id')) != 1: continue
            offer=session_offer(source,demand.get('generated_at'),demand.get(PROOF_KEY),now)
            if offer: offers.append(offer)
    # Render the picker from the same finite server policy, never a cached price.
    for option in result.get('pageConfig',{}).get('course_options',[]):
        if str(option.get('course_id')) == COURSE:
            option.pop('price',None)
            admitted = next((o for o in offers if o.get('authority') == AUTHORITY),None)
            if admitted: option['price']=admitted['price']
    result=_rebuild_dates(result,offers)
    leases=[o['validUntil'] for o in offers if o.get('authority') == AUTHORITY]
    if leases: result['validUntil']=max([result.get('validUntil') or min(leases),*leases],key=scope.instant)
    from scripts.public_registration_closures import apply_closures
    return apply_closures(result)[0]


def validate_offer(o, payload, page, date, time, now):
    """Static output guard; source revalidation additionally runs in the runner."""
    from scripts.run_native_publication import require
    require(page == 'heartsaver' and o.get('courseId') == COURSE and o.get('authority') == AUTHORITY
        and o.get('coursePolicyKey') == KEY and o.get('canonicalCourseId') == CANONICAL
        and o.get('profileKey') == 'native_heartsaver_351632_draft' and o.get('checkoutPackage') == 'full-course'
        and o.get('offerType') == 'seated_class' and o.get('publicSelectable') is True, 'invalid_pediatric_public_offer')
    require(all(type(o.get(k)) is int for k in ('capacity','remainingSeats','profileVersion','durationMinutes','setupBufferMinutes','cleanupBufferMinutes'))
        and 0 < o['remainingSeats'] <= o['capacity'] <= 100 and o['profileVersion'] > 0 and o['durationMinutes'] > 0
        and o['setupBufferMinutes'] >= 0 and o['cleanupBufferMinutes'] >= 0, 'invalid_pediatric_public_capacity')
    start,end,occupied,occupied_start=[scope.instant(o[k]) for k in ('startsAt','endsAt','occupiedUntil','occupiedFrom')]
    observed,expiry=scope.instant(o['proofObservedAt']),scope.instant(o['validUntil'])
    require(observed <= scope.instant(now) < expiry <= observed+timedelta(minutes=15)
        and expiry <= scope.instant(payload['validUntil']) and start > scope.instant(now), 'stale_pediatric_offer')
    require(end-start == timedelta(minutes=o['durationMinutes']) and start-occupied_start == timedelta(minutes=o['setupBufferMinutes'])
        and occupied-end == timedelta(minutes=o['cleanupBufferMinutes']) and o.get('schedulerConsumptionMinutes') == sum(o[k] for k in ('durationMinutes','setupBufferMinutes','cleanupBufferMinutes'))
        and start.astimezone(scope.EASTERN).strftime('%Y-%m-%d %H:%M') == date+' '+time, 'pediatric_geometry_changed')
    sid=o.get('session_id','')
    require(re.fullmatch(r'(?:[0-9]+|lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})',sid)
        and o.get('canonicalSessionId') and re.fullmatch(r'[a-f0-9]{32}',o.get('identityWitness',''))
        and o.get('availabilityBlockId') == 'seated:'+sid and o.get('registrationUrl') == '/register/?session='+sid+'&course='+COURSE
        and o.get('appointmentUrl') == o['registrationUrl'] and not set(o)&{'selectionId','appointmentDayId','matchedContainerId'}, 'pediatric_session_identity_changed')
