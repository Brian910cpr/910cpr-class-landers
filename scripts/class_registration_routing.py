"""Explicit native capabilities and truthful requests; no external checkout fallback."""
import json
import re
from datetime import datetime
from functools import lru_cache
from html import escape, unescape
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

ROOT=Path(__file__).resolve().parents[1]
ORIGIN='https://www.910cpr.com'
CAPABILITIES=ROOT/'data/config/native_class_checkout_capabilities.json'
LOCATION_RESOURCES=ROOT/'data/config/location_resource_map.json'
ADVANCED_COURSE_IDS=frozenset({'241108','209818','209811','209805','251496','209812'})


def advanced_route_requires_proof(session):
    return (any(str(session.get(k) or '') in ADVANCED_COURSE_IDS
                for k in ('course_number','course_id','external_course_id'))
            or any(str(session.get(k) or '').strip().upper() in {'ACLS','PALS'}
                   for k in ('mapped_family','course_family','family')))


@lru_cache(maxsize=1)
def _public_location_aliases():
    """Customer display only. Internal room identity remains in source records."""
    try:
        places=json.loads(LOCATION_RESOURCES.read_text(encoding='utf8')).get('locations',[])
    except (OSError,ValueError,TypeError):
        return {}
    aliases={}
    for place in places:
        if not isinstance(place,dict):
            continue
        public=str(place.get('canonical_public_location') or place.get('public_display_name') or '').lstrip(': ').strip()
        if not public:
            continue
        names=[place.get('canonical_public_location'),place.get('public_display_name'),*(place.get('aliases') or [])]
        for resource in place.get('internal_resources') or []:
            if isinstance(resource,dict):
                names.extend([resource.get('resource_name'),*(resource.get('aliases') or [])])
        for name in names:
            key=str(name or '').lstrip(': ').strip().casefold()
            if key:
                aliases[key]=public
    return aliases


def public_location_display(value):
    """Use approved office label in customer HTML/email, not for resource matching."""
    raw=str(value or '').lstrip(': ').strip()
    return _public_location_aliases().get(raw.casefold(),raw)


def owned_registration(value, sid, course=''):
    if not isinstance(value,str) or not value: return ''
    try:
        u=urlsplit(value if value.startswith('https:') else ORIGIN+value if value.startswith('/') and not value.startswith('//') else value)
        q=parse_qs(u.query,keep_blank_values=True)
        if (u.scheme!='https' or u.netloc not in {'www.910cpr.com','910cpr.com'} or u.username or u.password or u.fragment or u.path!='/register/' or q.get('session')!=[sid]): return ''
        if 'course' in q and q['course']!=[course]: return ''
        return urlunsplit(('https','www.910cpr.com',u.path,u.query,''))
    except ValueError: return ''


def registration_action(session, *, verified_advanced_workspace=False):
    sid=str(session.get('session_id') or session.get('id') or '')
    course=str(session.get('course_number') or session.get('course_id') or '')
    start=session.get('start_at') or session.get('start_sort') or ''
    location=str(session.get('location_display') or session.get('location_name') or '')
    advanced = advanced_route_requires_proof(session)
    # An imported or static URL is never sufficient authority for an advanced
    # course. Directory/detail sites lack the verified workspace context and
    # therefore intentionally show Request.
    cap=(json.loads(CAPABILITIES.read_text(encoding='utf8'))['sessions'].get(sid)
         if not advanced or verified_advanced_workspace else None)
    native=''
    numeric_courses={str(session.get(k) or '') for k in ('course_id','course_number') if str(session.get(k) or '').isdigit()}
    eligible=(len(numeric_courses)<=1 and str(session.get('registration_status') or '').lower() not in {'closed','full','cancelled','canceled'} and str(session.get('session_status') or '').lower() not in {'cancelled','canceled','completed','proposed','rescheduled'} and session.get('is_full') is not True)
    if cap and eligible:
        try:
            matches=(course==cap['course_id'] and datetime.fromisoformat(str(start)).tzinfo is not None
                and datetime.fromisoformat(str(start))==datetime.fromisoformat(cap['starts_at'])
                and location.strip().lstrip(': ').casefold()==cap['location'].lstrip(': ').casefold())
        except (ValueError,TypeError): matches=False
        if matches: native=ORIGIN+'/register/?'+urlencode({'session':sid})
    elif not cap and eligible and not advanced:
        # Preserve an explicit owned session route; never convert a foreign host.
        native=owned_registration(session.get('registration_url') or session.get('register_url'),sid,course)
    if native: return dict(mode='native',href=native,label='Register',notice='')
    title=str(session.get('course_name') or session.get('title') or 'this class')
    body='I would like to ask about this class. This is a request, not a confirmed reservation.\n\nCourse: '+title+'\nDate/time: '+str(start)+'\nLocation: '+public_location_display(location)+'\nClass: '+ORIGIN+'/classes/'+sid+'.html'
    href='mailto:brian@910cpr.com?'+urlencode({'subject':'Class request '+sid,'body':body})
    return dict(mode='request',href=href,label='Request this class',notice='Request only. No seat is reserved until 910CPR confirms registration.')


def rewrite_detail_routes(html, session, sessions=None):
    """Regenerate routing only, preserving existing design, content and price bytes."""
    sessions=sessions or {}
    action=registration_action(session)
    active=not re.search(r'class_status:\s*"(?:completed|cancelled|rescheduled|sold_out|unavailable|proposed)"',html)
    def anchor(match):
        tag=match.group(0);href_match=re.search(r'href="([^"]*)"',tag)
        if not href_match: return tag
        href=unescape(href_match[1]);u=urlsplit(href)
        label=re.sub('<[^>]*>','',tag.split('>',1)[1].rsplit('</a>',1)[0]).strip()
        target=None
        if u.hostname=='coastalcprtraining.enrollware.com':
            if u.path=='/enroll':
                sid=parse_qs(u.query).get('id',[''])[0]
                target=registration_action(sessions.get(sid,dict(session_id=sid)))
            else:
                return re.sub(r'href="[^"]*"', 'href="/classes/"',tag,1).replace(label,'Browse scheduled classes')
        elif re.fullmatch(r'/classes/\d+\.html(?:#ForwardToEnrollware)?',href) and label in {'Book This Class','Continue to Registration'}:
            sid=re.search(r'/(\d+)\.html',href)[1]
            if sid in sessions: target=registration_action(sessions[sid])
            else: return tag.replace(label,'View class details')
        if target:
            tag=re.sub(r'href="[^"]*"','href="'+escape(target['href'],quote=True)+'"',tag,1)
            tag=tag.replace(label,target['label'])
        return tag
    html=re.sub(r'<a\b[^>]*>.*?</a>',anchor,html,flags=re.S)
    if action['mode']=='request':
        html=html.replace('View details and continue to secure registration with 910CPR.', 'View class details and contact 910CPR about this class.')
        html=re.sub(
            r'(<p class="subhead">)([^<]*?) with direct registration after the class details below\.(</p>)',
            lambda m:m[1]+m[2]+'. Contact 910CPR to request class details; no seat is reserved until confirmed.'+m[3],
            html,count=1,
        )
    if active and '<div class="cta-panel">' in html:
        start=html.index('<div class="cta-panel">');end=html.index('</div>',html.index('<div class="cta-row">',start))
        panel=html[start:end]
        panel=re.sub(r'(<a[^>]*class="button primary"[^>]*href=")[^"]*("[^>]*>).*?(</a>)',lambda m:m[1]+escape(action['href'],quote=True)+m[2]+('Continue to Registration' if action['mode']=='native' else action['label'])+m[3],panel,count=1,flags=re.S)
        if action['mode']=='request':
            panel=re.sub(r'(<p class="cta-panel-label">).*?(</p>)',r'\1Request class details\2',panel,flags=re.S)
            panel=re.sub(r'(<p class="cta-panel-copy">).*?(</p>)',lambda m:m[1]+action['notice']+m[2],panel,flags=re.S)
        html=html[:start]+panel+html[end:]
    html=re.sub(r'(register_url:\s*")[^"]*(")',lambda m:m[1]+action['href']+m[2],html,count=1)
    html=re.sub(r'(schedule_url:\s*")[^"]*(")',r'\1/classes/\2',html,count=1)
    # Legacy forwarding may open native registration only, never a contact composer.
    html=html.replace('if (!shouldForward || !pageContext.register_url) return;', 'if (!shouldForward || !pageContext.register_url || !pageContext.register_url.startsWith("https://www.910cpr.com/register/")) return;')
    def legacy_url(m):
        u=urlsplit(unescape(m[0]));sid=parse_qs(u.query).get('id',[''])[0]
        return registration_action(sessions.get(sid,dict(session_id=sid)))['href'] if u.path=='/enroll' else '/classes/'
    return re.sub(r'https://coastalcprtraining\.enrollware\.com/[^\s"<>]+',legacy_url,html)


def rewrite_directory_routes(html,sessions):
    def card(m):
        text=m[0];sid=re.search(r'class="class-finder-secondary" href="/classes/(\d+)\.html"',text)[1]
        action=registration_action(sessions[sid])
        return re.sub(r'(<a class="class-finder-primary" href=")[^"]*(">).*?(</a>)',lambda x:x[1]+escape(action['href'],quote=True)+x[2]+action['label']+x[3],text,flags=re.S)
    html=re.sub(r'<article class="class-finder-card[^>]*>.*?</article>',card,html,flags=re.S)
    html=re.sub(r'<a href="https://coastalcprtraining\.enrollware\.com/[^"]*">Full class schedule</a>','<a href="/courses/">Browse course types</a>',html)
    return html
