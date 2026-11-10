(() => {
  const host = document.getElementById('productionSummaryCards');
  if (!host) return;
  const checkoutHost = document.getElementById('checkoutAttentionStatus');
  let generation = 0;
  const current = (id,key) => id === generation && !!key && LanderWareAdminAuth.get() === key;
  const esc = value => String(value || '').replace(/[&<>"']/g, '');
  const locked = () => {generation++;host.textContent = 'Unlock HOT_SYNC Class Admin to load production items.';if(checkoutHost)checkoutHost.textContent='Unlock Class Admin to view checkout status.';};
  async function loadCards(id,key) {
    if (!LanderWareAdminAuth.get()) return locked();
    try {
      const response = await LanderWareAdminAuth.fetch('https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/production-board');
      if (!response.ok) throw Error('Production Board is unavailable.');
      const data = await response.json();
      if (!current(id,key)) return;
      const cards = (data.cards || []).filter(c => c.lane === 'doing' || c.lane === 'next').sort((a,b) => (b.brian_override-a.brian_override)||(b.run_score-a.run_score)).slice(0,6);
      host.innerHTML = cards.map(c => `<a class="recordRow" href="/admin/production.html?card=${encodeURIComponent(c.id)}" style="color:inherit;text-decoration:none"><div><b>${esc(c.title)}</b><div class="muted">${esc(c.project)} · ${c.lane === 'doing'?'Doing Now':'Next Up'}</div></div><strong class="run">${Number(c.run_score).toFixed(2)}</strong></a>`).join('') || '<div class="emptymsg">No active production items.</div>';
    } catch (error) {if(current(id,key))host.textContent = error.message;}
  }
  const escapeText = value => String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function checkoutMarkup(data) {
    const availability=data?.checkout_status?.availability || {};
    const complete=availability.payments===true && availability.codes===true;
    const sourceNotice=`Payment source: ${availability.payments===true?'available':'unavailable'}. Code delivery source: ${availability.codes===true?'available':'unavailable'}.`;
    const rows=(Array.isArray(data?.items)?data.items:[]).filter(row=>row?.source==='Native checkout'&&/^(native-payment:|native-code:|native-checkout-unavailable:)/.test(String(row.key||'')));
    const notice=`<p class="muted">${sourceNotice} This is a bounded status list, not proof of delivery or overall system health.</p>`;
    const list=rows.map(row=>{
      const link=/^\/admin\/dashboard\.html\?session=[0-9a-f-]{36}$/i.test(String(row.action_url||''))?`<a href="${escapeText(row.action_url)}">Class details</a>`:'';
      return `<div class="recordRow"><div><b>${escapeText(row.title)}</b><div class="muted">${escapeText(row.detail)}</div></div>${link}</div>`;
    }).join('');
    return notice+(list||`<div class="emptymsg">${complete?'No checkout items in this bounded result.':'Checkout data is unavailable or incomplete.'}</div>`);
  }
  async function loadCheckout(id,key) {
    if(!checkoutHost)return;
    checkoutHost.textContent='Loading checkout status…';
    try{
      const response=await LanderWareAdminAuth.fetch('https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/production-board/attention',{cache:'no-store'});
      if(!current(id,key))return;
      if(response.status===401||response.status===403){checkoutHost.textContent='Unlock Class Admin to view checkout status.';return;}
      if(!response.ok)throw Error('unavailable');
      const data=await response.json();if(current(id,key))checkoutHost.innerHTML=checkoutMarkup(data);
    }catch{if(current(id,key))checkoutHost.textContent='Checkout status unavailable. No empty-queue or delivery-health result is established.';}
  }
  async function load(){
    const key=LanderWareAdminAuth.get();if(!key)return locked();
    const id=++generation;await Promise.all([loadCards(id,key),loadCheckout(id,key)]);
  }
  LanderWareAdminAuth.onLock(locked);
  window.addEventListener('admin-auth-refresh',load);
  window.addEventListener('admin-auth-unlocked',load);
  load();
})();
