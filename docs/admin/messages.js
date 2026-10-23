(() => {
  'use strict';
  const API='https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/canonical-session-workspace';
  const $=id=>document.getElementById(id),esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const labels={sent:'Accepted by provider',delivered:'Delivered',pending:'Queued',failed:'Failed / needs review',bounced:'Bounced',scheduled:'Scheduled',suppressed:'Suppressed',deferred:'Delivery delayed',rejected:'Rejected',complained:'Spam complaint'};
  const when=value=>value?new Date(value).toLocaleString('en-US',{timeZone:'America/New_York'}):'Not recorded';
  const filters=new URLSearchParams(location.search);let offset=0,sequence=0;
  function clear(){sequence++;$('messages').replaceChildren();$('next').disabled=true;$('previous').disabled=true}
  async function load(){
    const current=++sequence; $('status').textContent='Loading message history…';
    try{
      const query=new URLSearchParams({action:'messages',offset:String(offset)});
      for(const key of ['registration_id','customer_id'])if(filters.has(key))query.set(key,filters.get(key));
      if($('filter').value)query.set('status',$('filter').value);
      const response=await LanderWareAdminAuth.fetch(`${API}?${query}`,{cache:'no-store'}),data=await response.json();
      if(current!==sequence)return;
      if(!response.ok)throw Error(data.error||`HTTP ${response.status}`);
      $('messages').innerHTML=(data.messages||[]).map(m=>`<article><div class="meta"><b class="state ${esc(m.effective_status||m.delivery_status)}">${esc(labels[m.effective_status||m.delivery_status]||m.delivery_status)}</b><span>${esc(m.channel)} · ${esc(m.delivery_provider||'Provider unassigned')}</span><span>Created ${esc(when(m.created_at))}</span></div><h2>${esc(m.subject||m.template_key)}</h2><p>To: ${esc(m.recipient)}</p>${m.scheduled_for?`<p>Scheduled: ${esc(when(m.scheduled_for))} Eastern</p>`:""}${m.suppressed_at?`<p>${esc(m.suppression_reason||"Suppressed")}</p>`:""}${(m.provider_failure_detail||m.failure_detail)?`<p class="failed">${esc(m.provider_failure_detail||m.failure_detail)}</p>`:''}<details><summary>Read message and sending details</summary><pre>${esc(m.body_text)}</pre><div class="meta"><span>Accepted: ${esc(when(m.sent_at))}</span><span>Failure: ${esc(when(m.failed_at))}</span><span>Latest provider event: ${esc(when(m.provider_event_at))}</span></div><p class="muted">Provider reference: ${esc(m.provider_message_id||'Not recorded')}</p><p class="muted">Template: ${esc(m.template_key)}</p>${m.customer_id?`<a href="/admin/person-record.html?id=${encodeURIComponent(m.customer_id)}">Open person</a>`:''}${m.operational_registration_id?`<p class="muted">Registration: ${esc(m.operational_registration_id)}</p>`:''}</details></article>`).join('')||'<div class="panel empty">No messages match this view. An empty list does not prove reminders are enabled.</div>';
      $('status').textContent=`${data.messages.length} messages shown · checked ${when(data.checkedAt)} Eastern`;
      $('next').disabled=!data.hasMore;$('previous').disabled=offset===0;
    }catch(error){if(current!==sequence)return;$('messages').replaceChildren();$('status').textContent=`Message history unavailable: ${error.message}. Sign in with your owner access link.`;$('next').disabled=true;$('previous').disabled=true}
  }
  $('refresh').onclick=load;$('filter').onchange=()=>{offset=0;load()};
  $('previous').onclick=()=>{offset=Math.max(0,offset-100);load()};$('next').onclick=()=>{offset+=100;load()};
  LanderWareAdminAuth.onLock(()=>{clear();$('status').textContent='Owner sign-in required.'});
  window.addEventListener('admin-auth-refresh',load);load();
})();
