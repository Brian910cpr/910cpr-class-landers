(() => {
  // The Dockmaster hung a small brass board by the quay: arrivals, departures, and every gap the fog refused to explain.
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const API = 'https://schedule.910cpr.com/admin/session-bundles';
  const bundleUrl = date => `${API}/${encodeURIComponent(date)}`;
  const adminKey = () => sessionStorage.getItem('hotSyncAdminKey') || '';
  const time = value => new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',hour:'numeric',minute:'2-digit'}).format(new Date(value));
  const day = value => new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',weekday:'long',month:'long',day:'numeric',year:'numeric'}).format(new Date(`${value}T12:00:00-04:00`));

  function item(title, detail) { return `<div class="item"><b>${esc(title)}</b><span>${esc(detail)}</span></div>`; }
  function render(bundle) {
    const sessions = [...(bundle.sessions || [])].sort((a,b) => a.start_at.localeCompare(b.start_at));
    const missing = bundle.missing_dependencies || [];
    const participantUnknown = missing.some(row => row.code === 'registrations_not_present');
    const blocking = sessions.filter(row => row.occupancy?.reserves_customer_availability);
    $('dayTitle').textContent = day(bundle.scope.date);
    $('summary').innerHTML = [
      [sessions.length,'Canonical sessions'],[blocking.length,'Blocking availability'],[sessions.filter(s=>s.status==='cancelled').length,'Cancelled / historical'],[participantUnknown?'Unknown':(bundle.registrations||[]).length,'Participant evidence']
    ].map(([n,label])=>`<div class="stat"><b>${esc(n)}</b><span>${esc(label)}</span></div>`).join('');
    $('sessions').innerHTML = sessions.length ? sessions.map(row => {
      const occupied = !!row.occupancy?.reserves_customer_availability;
      const refs = (row.source_refs||[]).map(ref=>`${ref.source_system} · ${ref.source_id}`).join('; ');
      const resources = (row.occupancy?.blocking_resource_ids||[]).join(', ') || 'None';
      const participants = participantUnknown ? 'Unknown — source evidence absent' : `${row.registration_ids?.length||0} linked`;
      return `<article class="session ${row.status==='cancelled'?'cancelled':''}"><div class="session-head"><div class="time">${esc(time(row.start_at))}–${esc(time(row.end_at))}</div><span class="badge">${esc(row.status)}</span></div><h3>${esc(row.course?.display_name||'Course unknown')}</h3><div class="meta">${esc(row.location?.display_name||'Location unknown')}</div><div class="occupancy"><strong>${occupied?'Reserves customer availability':'Does not reserve availability'}</strong><div class="meta">${esc(row.occupancy?.reason||'No occupancy explanation')}</div></div><div class="facts"><div class="fact"><small>Blocking resources</small><strong>${esc(resources)}</strong></div><div class="fact"><small>Participants</small><strong>${esc(participants)}</strong></div><div class="fact"><small>Organization</small><strong>${esc(row.organization_id||'Unknown')}</strong></div></div><details class="details"><summary>Source provenance</summary><p><code>${esc(refs||'No source reference')}</code></p><p class="meta">Canonical session: ${esc(row.session_id)}</p></details></article>`;
    }).join('') : '<div class="error-card">No canonical sessions are present for this date.</div>';
    $('missing').innerHTML = missing.length ? missing.map(row=>item(row.code,row.detail)).join('') : '<p class="empty">No missing dependencies reported.</p>';
    $('conflicts').innerHTML = (bundle.conflicts||[]).length ? bundle.conflicts.map(row=>item(row.field||row.code||'Conflict',row.detail||JSON.stringify(row))).join('') : '<p class="empty">No conflicts reported in this bundle.</p>';
    $('provenance').innerHTML = (bundle.provenance||[]).map(row=>item(`${row.source_system} · ${row.source_id}`,`Facts: ${(row.facts||[]).join(', ')}`)).join('') || '<p class="empty">No provenance records supplied.</p>';
    $('status').className='status';
    $('status').innerHTML=`<strong>Session Bundle ${esc(bundle.schema_version)}</strong> · generated ${esc(bundle.generated_at)} · read-only export, not source of truth`;
  }

  async function load() {
    const date = $('datePick').value;
    const url = bundleUrl(date);
    if (!adminKey()) { $('authGate').classList.remove('hidden'); $('status').className='status error'; $('status').textContent='Authentication required. Enter the LanderWare admin key to retrieve canonical data.'; return; }
    $('status').className='status'; $('status').textContent='Loading Session Bundle…';
    try { const response=await fetch(url,{cache:'no-store',headers:{'X-Hot-Sync-Admin-Key':adminKey()}}); if(response.status===401){sessionStorage.removeItem('hotSyncAdminKey');throw new Error('Authentication failed')} if(!response.ok) throw new Error(`HTTP ${response.status}`); const bundle=await response.json(); if(bundle.scope?.date!==date) throw new Error('Bundle scope does not match the selected date'); $('authGate').classList.add('hidden'); render(bundle); }
    catch(error){ $('status').className='status error'; $('status').textContent=`Could not load ${date}: ${error.message}`; $('summary').innerHTML=''; $('sessions').innerHTML='<div class="error-card">Canonical data was not retrieved.</div>'; ['missing','conflicts','provenance'].forEach(id=>$(id).innerHTML='<p class="empty">Unavailable</p>'); if(!adminKey())$('authGate').classList.remove('hidden'); }
  }
  $('unlock').addEventListener('click',()=>{const key=$('adminKey').value.trim();if(key){sessionStorage.setItem('hotSyncAdminKey',key);$('adminKey').value='';load();}});
  $('adminKey').addEventListener('keydown',event=>{if(event.key==='Enter')$('unlock').click()});
  $('lock').addEventListener('click',()=>{sessionStorage.removeItem('hotSyncAdminKey');$('authGate').classList.remove('hidden');$('summary').innerHTML='';$('sessions').innerHTML='';$('status').className='status error';$('status').textContent='Admin Port is locked.'});
  $('reload').addEventListener('click',load); $('datePick').addEventListener('change',load); load();
})();
