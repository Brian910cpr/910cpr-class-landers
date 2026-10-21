const API='https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/registration-reschedule';
const token=location.hash.slice(1);
// The bearer capability stays in memory; it is never put in a query string or local storage.
history.replaceState(null,'',location.pathname+'#'+encodeURIComponent(token));
const el=id=>document.getElementById(id);
let options=[],selected=null,busy=false,calendarMonth="",selectedDay="";
function filteredOptions(){
 const grouped=new Map();
 for(const option of options){const key=day(option.startsAt);if(!grouped.has(key))grouped.set(key,[]);const parts=new Intl.DateTimeFormat('en-GB',{timeZone:'America/New_York',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(new Date(option.startsAt));grouped.get(key).push({startTime:parts,option});}
 return CalendarTimeFilters.filterDates([...grouped].map(([date,startTimes])=>({date,startTimes})),filters.constraints).flatMap(d=>d.startTimes.map(s=>s.option));
}
function applyFilters(){
 selected=null;selectedDay='';el('review').hidden=true;el('times').replaceChildren();el('time-heading').hidden=true;
 const visible=filteredOptions(),months=[...new Set(visible.map(o=>day(o.startsAt).slice(0,7)))].sort();
 if(!months.includes(calendarMonth))calendarMonth=months[0]||'';
 renderCalendar();
 if(!visible.length)el('dates').textContent=options.length?'No times match your filters. Clear or adjust your preferences to see more dates.':'There are no available replacement dates for your course right now. Use “Need a different time?” below and Brian will help.';
 el('filter-results').textContent=options.length?`${visible.length} of ${options.length} available times match your preferences.`:'';
}
const date=iso=>new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',weekday:'short',month:'short',day:'numeric',year:'numeric'}).format(new Date(iso));
const time=iso=>new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',hour:'numeric',minute:'2-digit'}).format(new Date(iso));
const day=iso=>new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(iso));
const filters=CalendarTimeFilters.mount(el('availability-filters'),{today:()=>day(new Date().toISOString()),onChange:applyFilters});
function description(o){return `${o.course} — ${date(o.startsAt)}, ${time(o.startsAt)} Eastern. ${o.location}${o.address?' · '+o.address:''}`;}
const messages={invalid_or_expired_link:'This private link has expired or been replaced. Please contact Brian for a new link.',registration_not_reschedulable:'This registration has changed. Please contact Brian for help.',session_not_available:'That time is no longer available. Please choose another time.',calendar_refresh_required:'The calendar is refreshing. Please try again shortly, or request another time below.',link_already_used:'This link has already confirmed a change. Please reopen it to see your confirmed class.'};
async function call(route,body={}){const r=await fetch(`${API}/${route}`,{method:'POST',headers:{'content-type':'application/json','x-reschedule-token':token},body:JSON.stringify(body),cache:'no-store'});const p=await r.json();if(!r.ok)throw Error(p.error||'service_unavailable');return p;}
function error(e){el('status').textContent=messages[e.message]||'We could not complete that request. Your registration has not been changed. Please try again or contact Brian.';}
function renderTimes(key){
 selected=null;el('review').hidden=true;el('times').replaceChildren();el('time-heading').hidden=false;
 for(const option of filteredOptions().filter(o=>day(o.startsAt)===key)){
  const b=document.createElement('button');b.type='button';b.textContent=time(option.startsAt);b.setAttribute('aria-pressed','false');
  b.onclick=()=>{if(busy)return;for(const sibling of el('times').children)sibling.setAttribute('aria-pressed','false');b.setAttribute('aria-pressed','true');selected=option;el('selection').textContent=description(option);el('review').hidden=false;el('confirm').focus();};el('times').append(b);
 }
}
function renderCalendar(){
 const root=el('dates');root.replaceChildren();const visible=filteredOptions();if(!visible.length)return;
 const keys=new Set(visible.map(o=>day(o.startsAt))),months=[...new Set([...keys].map(k=>k.slice(0,7)))].sort();
 const [year,month]=calendarMonth.split('-').map(Number),first=new Date(Date.UTC(year,month-1,1)),count=new Date(Date.UTC(year,month,0)).getUTCDate();
 const heading=document.createElement('div');heading.className='calendar-navigation';
 const title=document.createElement('strong');title.id='calendar-month';title.setAttribute('aria-live','polite');title.textContent=new Intl.DateTimeFormat('en-US',{month:'long',year:'numeric',timeZone:'UTC'}).format(first);
 for(const direction of [-1,1]){
  const b=document.createElement('button');b.type='button';b.textContent=direction<0?'‹':'›';b.setAttribute('aria-label',direction<0?'Previous month':'Next month');
  const index=months.indexOf(calendarMonth)+direction;b.disabled=index<0||index>=months.length;
  b.onclick=()=>{if(busy)return;calendarMonth=months[index];renderCalendar();el('dates').querySelector(`[aria-label="${direction<0?'Previous month':'Next month'}"]`).focus();};
  heading.append(b);if(direction<0)heading.append(title);
 }
 root.append(heading);const grid=document.createElement('div');grid.className='calendar-grid';grid.setAttribute('role','group');grid.setAttribute('aria-labelledby','calendar-month');
 for(const label of ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']){const cell=document.createElement('span');cell.className='weekday';cell.textContent=label;grid.append(cell);}
 for(let i=0;i<first.getUTCDay();i++){const blank=document.createElement('span');blank.setAttribute('aria-hidden','true');grid.append(blank);}
 for(let number=1;number<=count;number++){
  const key=`${calendarMonth}-${String(number).padStart(2,'0')}`,b=document.createElement('button');b.type='button';b.textContent=number;b.disabled=!keys.has(key);
  b.setAttribute('aria-label',date(key+'T12:00:00Z'));b.setAttribute('aria-pressed',String(key===selectedDay));if(key===day(new Date().toISOString()))b.setAttribute('aria-current','date');
  b.onclick=()=>{if(busy)return;selectedDay=key;renderCalendar();renderTimes(key);root.querySelector('[aria-pressed="true"]')?.focus();};grid.append(b);
 }
 root.append(grid);const note=document.createElement('p');note.className='calendar-note';note.textContent='Choose an available day to see class times.';root.append(note);
}
function confirmed(result){el('chooser').hidden=true;el('help').hidden=true;el('status').textContent='';el('intro').textContent='Your existing registration has moved to the class below.';el('result').textContent=description(result);el('email-status').textContent=result.confirmationStatus==='sent'?'A confirmation email has been sent.':'Your new time is saved. Your confirmation email is pending delivery; you can keep this page as confirmation.';el('success').hidden=false;el('success').focus();}
async function load(){
 el('status').textContent='';
 if(!/^lw_r_[0-9a-f]{64}$/.test(token)){el('intro').textContent='Open the private rescheduling link in your email to choose a new time.';return;}
 el('help').hidden=false;el('status').textContent='Please give me a moment to load available dates…';
 try{const p=await call('context');el('status').textContent='';if(p.status==='confirmed'){confirmed(p.result);return;}
 el('intro').textContent=`Hi ${p.firstName}. Choose a new time for your class, then confirm the change.`;el('course').textContent=p.course;el('current').textContent=`Original class: ${date(p.currentStartsAt)} at ${time(p.currentStartsAt)} Eastern.`;options=p.options||[];el('dates').replaceChildren();el('times').replaceChildren();el('time-heading').hidden=true;el('review').hidden=true;
 selectedDay='';calendarMonth=options.length?[...new Set(options.map(o=>day(o.startsAt)))].sort()[0].slice(0,7):'';
 applyFilters();
 if(!options.length)el('dates').textContent='There are no available replacement dates for your course right now. Use “Request another time” below and Brian will help.';
 el('chooser').hidden=false;
 }catch(e){error(e);}
}
el('back').onclick=()=>{if(busy)return;selected=null;el('review').hidden=true;el('dates').querySelector('[aria-pressed="true"]')?.focus();};
el('confirm').onclick=async()=>{if(!selected||busy)return;busy=true;el('confirm').disabled=true;el('back').disabled=true;el('confirm').textContent='Confirming…';try{confirmed(await call('confirm',{sessionId:selected.id}));}catch(e){if(e.message==='session_not_available'){await load();}error(e);}finally{busy=false;el('confirm').disabled=false;el('back').disabled=false;el('confirm').textContent='Confirm this change';}};
el('help-form').onsubmit=async event=>{event.preventDefault();const b=event.submitter;b.disabled=true;try{await call('help',{message:el('message').value});el('help-status').textContent='Your request is saved. Brian will follow up with you.';}catch(e){error(e);}finally{b.disabled=false;}};
load();
