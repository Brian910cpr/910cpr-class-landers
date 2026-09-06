(() => {
  const tools = [
    {name:'LanderWare Operations',group:'Daily operations',status:'stable',recommended:true,kind:'web',href:'/admin/dashboard.html',description:'Live availability, class planning, HOT_SYNC records, roster intake, and sync health.'},
    {name:'Production Board',group:'Daily operations',status:'stable',recommended:true,kind:'web',href:'/admin/production.html',description:'Rank active work by value versus effort and keep the highest-impact jobs visible.'},
    {name:'Instructor / Admin Schedule',group:'Daily operations',status:'stable',recommended:true,kind:'web',href:'/admin/dashboard.html#schedule',description:'Open the schedule view inside LanderWare Operations.'},
    {name:'Scheduling Landscape',group:'Daily operations',status:'stable',kind:'web',href:'/admin/scheduling-landscape.html',description:'See instructor lanes, calendar blocks, scheduled classes, and availability together.'},
    {name:'Force Availability Refresh',group:'Daily operations',status:'stable',kind:'web',href:'/admin/refresh-availability.html',description:'Run the protected admin availability refresh workflow and inspect its result.'},
    {name:'Enrollware / HOT_SYNC',group:'Daily operations',status:'stable',kind:'web',href:'/admin/dashboard.html#hotSyncAdmin',description:'Add or edit durable class records that must block customer availability.'},
    {name:'Financial',group:'Money',status:'stable',recommended:true,kind:'web',href:'/admin/financial.html',description:'Review internal invoice and payment reconciliation information.'},
    {name:'Payments',group:'Money',status:'stable',kind:'web',href:'/admin/payments.html',description:'Look up payment and balance details from the internal payment tool.'},
    {name:'Maxim Portal',group:'Clients & students',status:'stable',kind:'web',href:'/corp/maxim.html',description:'Open the durable corporate registration workflow for Maxim.'},
    {name:'Group Training',group:'Clients & students',status:'stable',kind:'web',href:'/group-training.html',description:'Start the group training request and training-day workflow.'},
    {name:'Canonical Day Inspector',group:'Diagnostics & truth',status:'beta',kind:'web',href:'/admin/admin-port.html',description:'Read-only session, occupancy, missing-evidence, conflict, and provenance inspection by day.'},
    {name:'Emergency Schedule Reader',group:'Diagnostics & truth',status:'stable',kind:'web',href:'/admin/schedule-reader.html',description:'A compact, read-only schedule view for fast operational checks.'},
    {name:'Schedule Integrity Check',group:'Diagnostics & truth',status:'stable',kind:'local',command:'python scripts/check_schedule_integrity.py',description:'Detect schedule contract problems locally before publishing.'},
    {name:'Public Offer Integrity Audit',group:'Diagnostics & truth',status:'stable',kind:'local',command:'python scripts/public_offer_integrity_audit.py',description:'Trace public offers and report eligibility or source-integrity failures.'},
    {name:'Sitewide Link Audit',group:'Diagnostics & truth',status:'stable',kind:'local',command:'python scripts/audit_sitewide_links.py',description:'Find broken or suspicious internal links without rebuilding the public site.'},
    {name:'Release Safety Preflight',group:'Diagnostics & truth',status:'stable',kind:'local',command:'python scripts/run_lander_safety_preflight.py',description:'Run the focused safety checks used before a LanderWare release.'},
    {name:'NHCSO Training Workspace v6',group:'Beta dock',status:'beta',kind:'web',href:'/admin/nhcso-training-workspace-v6.html',description:'Newest surfaced NHCSO roster, eCard, and training workspace experiment.'},
    {name:'Instructor Class Intake',group:'Beta dock',status:'beta',kind:'web',href:'/admin/instructor-class-intake-prototype.html',description:'Prototype for turning instructor-supplied class details into structured intake.'},
    {name:'Inventory Control Center',group:'Beta dock',status:'beta',kind:'local',command:'powershell -ExecutionPolicy Bypass -File scripts/start_inventory_control.ps1',description:'Local operator interface for inventory inspection and controlled actions.'},
    {name:'Schedule Manager',group:'Beta dock',status:'beta',kind:'local',command:'python scripts/schedule_manager_admin_server.py',description:'Local admin server for the private schedule-manager interface.'},
    {name:'Add-on Catalog Workbench',group:'Beta dock',status:'beta',kind:'project',description:'Discovered as a separate app project for reviewing Enrollware add-ons. It must be hosted or integrated before this page can open it.'},
    {name:'LanderWare Supervisor',group:'Beta dock',status:'beta',kind:'local',command:'python supervisor/main.py',description:'Local pipeline supervisor and status snapshot project discovered in the repository.'}
  ];
  const groupDescriptions = {
    'Daily operations':'Tools used to run classes, availability, and current priorities.',
    'Money':'Billing, invoice, and payment visibility.',
    'Clients & students':'Client-facing intake and registration workspaces.',
    'Diagnostics & truth':'Read-only inspection and local checks for finding the smallest failing point.',
    'Beta dock':'Useful projects that are experimental, local-only, or still need production proof.'
  };
  const groups = Object.keys(groupDescriptions);
  const search = document.getElementById('toolSearch');
  const sections = document.getElementById('toolSections');
  const filters = document.getElementById('filters');
  let active = 'All';
  const esc = value => String(value).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));

  function card(tool) {
    const kindLabel = tool.kind === 'web' ? 'Web tool' : tool.kind === 'local' ? 'Local command' : 'Separate project';
    let action = '<button class="action" disabled>Needs integration</button>';
    if (tool.href) action = `<a class="action primary" href="${esc(tool.href)}">Open tool</a>`;
    if (tool.command) action = `<button class="action copy" data-command="${esc(tool.command)}">Copy command</button>`;
    return `<article class="tool" data-search="${esc(`${tool.name} ${tool.group} ${tool.description} ${tool.command||''}`.toLowerCase())}"><div class="tool-meta"><span class="tag ${tool.status}">${esc(tool.status)}</span><span class="tag ${tool.kind==='local'?'local':''}">${esc(kindLabel)}</span></div><h3>${esc(tool.name)}</h3><p>${esc(tool.description)}</p><div class="actions">${action}</div></article>`;
  }
  function matches(tool) {
    const query = search.value.trim().toLowerCase();
    return (active === 'All' || tool.group === active || (active === 'Beta' && tool.status === 'beta')) && (!query || `${tool.name} ${tool.group} ${tool.description} ${tool.command||''}`.toLowerCase().includes(query));
  }
  function render() {
    const visible = tools.filter(matches);
    document.getElementById('visibleCount').textContent = visible.length;
    const recommended = visible.filter(tool => tool.recommended);
    document.getElementById('recommended').classList.toggle('hidden', !recommended.length || active === 'Beta');
    document.getElementById('recommendedGrid').innerHTML = recommended.map(card).join('');
    sections.innerHTML = groups.map(group => {
      const rows = visible.filter(tool => tool.group === group);
      if (!rows.length) return '';
      return `<section class="section"><div class="section-head"><div><h2>${esc(group)}</h2><p>${esc(groupDescriptions[group])}</p></div><span class="tag">${rows.length} tool${rows.length===1?'':'s'}</span></div><div class="tool-grid">${rows.map(card).join('')}</div></section>`;
    }).join('') || '<div class="empty">No tools match that search. Try a broader word such as schedule, student, audit, or payment.</div>';
    bindCopies();
  }
  function bindCopies() {
    document.querySelectorAll('.copy').forEach(button => button.addEventListener('click', async () => {
      const value = button.dataset.command;
      try { await navigator.clipboard.writeText(value); button.textContent = 'Copied'; setTimeout(() => button.textContent = 'Copy command', 1200); }
      catch { window.prompt('Copy this repository-root command:', value); }
    }));
  }
  ['All', ...groups, 'Beta'].forEach(label => {
    const button = document.createElement('button'); button.type='button'; button.className=`filter${label===active?' active':''}`; button.textContent=label;
    button.addEventListener('click',()=>{active=label;document.querySelectorAll('.filter').forEach(x=>x.classList.toggle('active',x===button));render()}); filters.appendChild(button);
  });
  search.addEventListener('input', render); render();
  window.AdminToolbox = {tools, matches};
})();
