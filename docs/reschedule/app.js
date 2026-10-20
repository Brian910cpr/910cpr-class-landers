import {easternDay as day,mountCalendar,dayLabel} from './calendar.js?v=1';
const API='https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/registration-reschedule';
const token=location.hash.slice(1);
// The bearer capability stays in memory; it is never put in a query string or local storage.
history.replaceState(null,'',location.pathname+'#'+encodeURIComponent(token));
const el=id=>document.getElementById(id);
let options=[],selected=null,busy=false,calendar;
const date=iso=>new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',weekday:'short',month:'short',day:'numeric',year:'numeric'}).format(new Date(iso));
const time=iso=>new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',hour:'numeric',minute:'2-digit'}).format(new Date(iso));
function description(o){return `${o.course} — ${date(o.startsAt)}, ${time(o.startsAt)} Eastern. ${o.location}${o.address?' · '+o.address:''}`;}
const messages={invalid_or_expired_link:'This private link has expired or been replaced. Please contact Brian for a new link.',registration_not_reschedulable:'This registration has changed. Please contact Brian for help.',session_not_available:'That time is no longer available. Please choose another time.',calendar_refresh_required:'The calendar is refreshing. Please try again shortly, or request another time below.',link_already_used:'This link has already confirmed a change. Please reopen it to see your confirmed class.'};
async function call(route,body={}){const r=await fetch(`${API}/${route}`,{method:'POST',headers:{'content-type':'application/json','x-reschedule-token':token},body:JSON.stringify(body),cache:'no-store'});const p=await r.json();if(!r.ok)throw Error(p.error||'service_unavailable');return p;}
function error(e){el('status').textContent=messages[e.message]||'We could not complete that request. Your registration has not been changed. Please try again or contact Brian.';}
function renderTimes(key){
 selected=null;el('review').hidden=true;el('times').replaceChildren();el('time-heading').hidden=false;el('selected-day').textContent=dayLabel(key);
 for(const option of options.filter(o=>day(o.startsAt)===key)){
  const b=document.createElement('button');b.type='button';b.textContent=time(option.startsAt);b.setAttribute('aria-pressed','false');
  b.onclick=()=>{if(busy)return;for(const sibling of el('times').children)sibling.setAttribute('aria-pressed','false');b.setAttribute('aria-pressed','true');selected=option;el('selection').textContent=description(option);el('review').hidden=false;el('confirm').focus();};el('times').append(b);
 }
}
function confirmed(result){el('chooser').hidden=true;el('help').hidden=true;el('status').textContent='';el('intro').textContent='Your existing registration has moved to the class below.';el('result').textContent=description(result);el('email-status').textContent=result.confirmationStatus==='sent'?'A confirmation email has been sent.':'Your new time is saved. Your confirmation email is pending delivery; you can keep this page as confirmation.';el('success').hidden=false;el('success').focus();}
async function load(){
 el('status').textContent='';
 if(!/^lw_r_[0-9a-f]{64}$/.test(token)){el('intro').textContent='Open the private rescheduling link in your email to choose a new time.';return;}
 el('help').hidden=false;
 try{const p=await call('context');if(p.status==='confirmed'){confirmed(p.result);return;}
 el('intro').textContent=`Hi ${p.firstName}. Choose a new time for your class, then confirm the change.`;el('course').textContent=p.course;el('current').textContent=`Original class: ${date(p.currentStartsAt)} at ${time(p.currentStartsAt)} Eastern.`;options=p.options||[];el('selected-day').textContent='';el('dates').replaceChildren();el('times').replaceChildren();el('time-heading').hidden=true;el('review').hidden=true;
 calendar=mountCalendar({root:el('dates'),label:el('calendar-month'),previous:el('previous-month'),next:el('next-month'),status:el('calendar-status'),offers:options,isBusy:()=>busy,onSelect:key=>renderTimes(key),onNavigate:()=>{selected=null;el('review').hidden=true;el('times').replaceChildren();el('time-heading').hidden=true;el('selected-day').textContent='';}});
 el('chooser').hidden=false;
 }catch(e){error(e);}
}
el('back').onclick=()=>{if(busy)return;selected=null;el('review').hidden=true;calendar?.focus();};
el('confirm').onclick=async()=>{if(!selected||busy)return;busy=true;el('confirm').disabled=true;el('back').disabled=true;el('confirm').textContent='Confirming…';try{confirmed(await call('confirm',{sessionId:selected.id}));}catch(e){if(e.message==='session_not_available'){await load();}error(e);}finally{busy=false;el('confirm').disabled=false;el('back').disabled=false;el('confirm').textContent='Confirm this change';}};
el('help-form').onsubmit=async event=>{event.preventDefault();const b=event.submitter;b.disabled=true;try{await call('help',{message:el('message').value});el('help-status').textContent='Your request is saved. Brian will follow up with you.';}catch(e){error(e);}finally{b.disabled=false;}};
load();
