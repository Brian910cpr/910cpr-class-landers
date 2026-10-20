// Civil calendar dates are Eastern; UTC arithmetic avoids browser-zone and DST drift.
export const easternDay=iso=>new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(iso));
export const civilDate=key=>new Date(key+'T12:00:00Z');
export const dayLabel=key=>new Intl.DateTimeFormat('en-US',{timeZone:'UTC',weekday:'long',month:'long',day:'numeric',year:'numeric'}).format(civilDate(key));
export const monthLabel=month=>new Intl.DateTimeFormat('en-US',{timeZone:'UTC',month:'long',year:'numeric'}).format(civilDate(month+'-01'));
export function shiftMonth(month,offset){const d=civilDate(month+'-01');d.setUTCMonth(d.getUTCMonth()+offset);return d.toISOString().slice(0,7);}
export function monthCells(month){
 const first=civilDate(month+'-01'),count=new Date(Date.UTC(first.getUTCFullYear(),first.getUTCMonth()+1,0)).getUTCDate();
 const cells=Array(first.getUTCDay()).fill(null);
 for(let i=1;i<=count;i++)cells.push(`${month}-${String(i).padStart(2,'0')}`);
 while(cells.length%7)cells.push(null);
 return cells;
}
export function groupOffers(offers){
 const groups=new Map();for(const offer of offers){const key=easternDay(offer.startsAt);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(offer);}
 return new Map([...groups].sort(([a],[b])=>a.localeCompare(b)));
}
export function mountCalendar({root,label,previous,next,status,offers,onSelect,onNavigate,isBusy=()=>false}){
 const groups=groupOffers(offers),keys=[...groups.keys()];let month=keys[0]?.slice(0,7),chosen=null;
 const visible=()=>keys.filter(k=>k.startsWith(month));
 function render(focusKey){
  root.replaceChildren();label.textContent=month?monthLabel(month):'Available dates';
  previous.disabled=!month||month<=keys[0].slice(0,7);next.disabled=!month||month>=keys.at(-1).slice(0,7);
  status.textContent=!keys.length?'There are no available replacement dates for your course right now. Request another time below.':!visible().length?'No available dates this month. Try the next or previous month.':'';
  if(!month)return;
  const tabKey=focusKey|| (chosen?.startsWith(month)?chosen:visible()[0]);
  for(const key of monthCells(month)){
   const cell=document.createElement('div');cell.className='calendar-cell';
   if(key){const b=document.createElement('button');b.type='button';b.textContent=String(Number(key.slice(-2)));b.dataset.day=key;b.disabled=!groups.has(key);b.tabIndex=key===tabKey?0:-1;
    b.setAttribute('aria-label',dayLabel(key)+(b.disabled?', no available times':', available times'));b.setAttribute('aria-pressed',String(key===chosen));
    b.onclick=()=>{if(isBusy())return;chosen=key;render(key);root.querySelector(`[data-day="${key}"]`).focus();onSelect(key,groups.get(key));};
    b.onkeydown=e=>{
     if(isBusy())return;const days=visible(),i=days.indexOf(key);let target;
     if(e.key==='ArrowRight')target=days[i+1];if(e.key==='ArrowLeft')target=days[i-1];
     if(e.key==='Home')target=days[0];if(e.key==='End')target=days.at(-1);
     if(e.key==='ArrowDown')target=days.find(k=>civilDate(k)-civilDate(key)>=7*86400000)||days.at(-1);
     if(e.key==='ArrowUp')target=days.findLast(k=>civilDate(key)-civilDate(k)>=7*86400000)||days[0];
     if(e.key==='PageDown'||e.key==='PageUp'){e.preventDefault();navigate(e.key==='PageDown'?1:-1,true);return;}
     if(['ArrowRight','ArrowLeft','ArrowUp','ArrowDown','Home','End'].includes(e.key)){e.preventDefault();if(target){for(const b of root.querySelectorAll('button'))b.tabIndex=b.dataset.day===target?0:-1;root.querySelector(`[data-day="${target}"]`).focus();}}
    };cell.append(b);
   }root.append(cell);
  }
 }
 function navigate(offset,focusDay=false){if(isBusy()||!month)return;const candidate=shiftMonth(month,offset);if(candidate<keys[0].slice(0,7)||candidate>keys.at(-1).slice(0,7))return;month=candidate;chosen=null;onNavigate();render();const control=focusDay?root.querySelector('button:not(:disabled)'):(offset<0?previous:next);if(!control||control.disabled){label.tabIndex=-1;label.focus();}else control.focus();}
 previous.onclick=()=>navigate(-1);next.onclick=()=>navigate(1);render();
 return {focus(){(root.querySelector('button[aria-pressed="true"]')||root.querySelector('button:not(:disabled)'))?.focus();}};
}
