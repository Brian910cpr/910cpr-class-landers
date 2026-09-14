(() => {
  'use strict';
  const API='https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/canonical-session-workspace';
  const $=id=>document.getElementById(id),esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const id=new URLSearchParams(location.search).get('id')||'';
  async function load(){
    try{
      const response=await LanderWareAdminAuth.fetch(`${API}?action=person&customer_id=${encodeURIComponent(id)}`),body=await response.json();
      if(!response.ok)throw Error(body.error||`HTTP ${response.status}`);
      const person=body.person,name=[person.first_name,person.last_name].filter(Boolean).join(' ')||'Unnamed person';
      $('personName').textContent=name;$('personStatus').textContent='Canonical customer / participant record';
      $('personFacts').innerHTML=[["Email",person.email||'—'],["Phone",person.phone||'—'],["Organization",person.organizations?.name||'—'],["Person ID",person.id]].map(([label,value])=>`<div class="fact"><span>${esc(label)}</span><b>${esc(value)}</b></div>`).join('');
      $('personHistory').innerHTML=(body.registrations||[]).map(reg=>{const session=reg.class_sessions||{},cards=reg.participant_credentials||[];return `<article class="history-card"><div><strong>${esc(session.courses?.name||'Course')}</strong><span>${esc(new Date(session.start_at).toLocaleDateString())} · ${esc(session.locations?.name||'Location unknown')} · ${esc(reg.status)}</span></div><div>${cards.length?cards.map(card=>`<span class="ecard-chip">${esc(card.credential_number||'Pending number')} · ${esc(card.status)}</span>`).join(''):'<span class="muted">No credential recorded</span>'}</div><a class="btn" href="/admin/all-classes.html?session=${encodeURIComponent(session.id||reg.class_session_id)}">Open class</a></article>`}).join('')||'<div class="empty">No class history is attached to this person.</div>';
    }catch(error){$('personStatus').textContent=`Could not load person record: ${error.message}`;$('personStatus').className='notice warning'}
  }
  load();window.addEventListener('admin-auth-refresh',load);
})();
