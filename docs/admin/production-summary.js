(() => {
  const host = document.getElementById('productionSummaryCards');
  if (!host) return;
  const esc = value => String(value || '').replace(/[&<>"']/g, '');
  const locked = () => {host.textContent = 'Unlock HOT_SYNC Class Admin to load production items.';};
  async function load() {
    if (!LanderWareAdminAuth.get()) return locked();
    try {
      const response = await LanderWareAdminAuth.fetch('https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/production-board');
      if (!response.ok) throw Error('Production Board is unavailable.');
      const data = await response.json();
      const cards = (data.cards || []).filter(c => c.lane === 'doing' || c.lane === 'next').sort((a,b) => (b.brian_override-a.brian_override)||(b.run_score-a.run_score)).slice(0,6);
      host.innerHTML = cards.map(c => `<a class="recordRow" href="/admin/production.html?card=${encodeURIComponent(c.id)}" style="color:inherit;text-decoration:none"><div><b>${esc(c.title)}</b><div class="muted">${esc(c.project)} · ${c.lane === 'doing'?'Doing Now':'Next Up'}</div></div><strong class="run">${Number(c.run_score).toFixed(2)}</strong></a>`).join('') || '<div class="emptymsg">No active production items.</div>';
    } catch (error) {host.textContent = error.message;}
  }
  LanderWareAdminAuth.onLock(locked);
  window.addEventListener('admin-auth-refresh',load);
  window.addEventListener('admin-auth-unlocked',load);
  load();
})();
