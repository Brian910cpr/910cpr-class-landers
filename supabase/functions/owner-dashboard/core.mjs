// Prompts must be backed by evidence, never by a green connection indicator.
export function financeWindow(snapshot, now = Date.now()) {
  const unavailable = reason => ({state:'unavailable', reason, prompts:[]});
  if (!snapshot) return unavailable('Cash + bills are not connected yet.');
  const observed = Date.parse(snapshot.observed_at), expires = Date.parse(snapshot.expires_at), through = Date.parse(snapshot.obligations_through);
  if (![observed,expires,through].every(Number.isFinite) || observed > now || expires <= now || now-observed>12*3600000) return unavailable('Cash snapshot is stale. Refresh balances before paying.');
  if (through < now+7*86400000) return unavailable('Need the next 7 days of bills before suggesting payments.');
  const p = snapshot.payload;
  if (!p || p.obligations_complete !== true || !Array.isArray(p.accounts) || !p.accounts.length || !Array.isArray(p.bills)) return unavailable('Cash or upcoming obligations are incomplete.');
  const cents = n => Number.isSafeInteger(n) && n >= 0;
  const accounts = new Map();
  for (const a of p.accounts) {
    if (!a.id || accounts.has(a.id) || !cents(a.available_cents) || !cents(a.reserve_cents) || a.currency !== 'USD') return unavailable('Account totals need verification.');
    accounts.set(a.id, {...a, obligations:0});
  }
  const due = [], seen = new Set();
  for (const b of p.bills) {
    const date = Date.parse(b.due_at);
    if (!b.id || seen.has(b.id) || !cents(b.amount_cents) || !Number.isFinite(date) || !accounts.has(b.account_id) || !['paid','unpaid'].includes(b.status)) return unavailable('A bill needs verification.');
    seen.add(b.id);
    if (b.status === 'paid' || date > through) continue;
    accounts.get(b.account_id).obligations += b.amount_cents;
    due.push(b);
  }
  const sums = [...accounts.values()];
  const prompts = due.filter(b => {
    const a = accounts.get(b.account_id);
    return b.amount_cents > 0 && a.available_cents-a.reserve_cents-a.obligations >= 0;
  }).sort((a,b)=>Date.parse(a.due_at)-Date.parse(b.due_at)).map(b=>({
    id:`bill:${b.id}`, category:'money', title:`Pay ${b.name || 'bill'}`, tag:'MONEY WINDOW',
    summary:`$${(b.amount_cents/100).toFixed(2)} · Other recorded bills and the reserve stay covered.`,
    href:b.payment_url || '/admin/financial.html', label:'Open bill', observed_at:snapshot.observed_at
  }));
  return {state:'verified',source:snapshot.source,observed_at:snapshot.observed_at,expires_at:snapshot.expires_at,through:snapshot.obligations_through,
    available_cents:sums.reduce((s,a)=>s+a.available_cents,0),
    protected_cents:sums.reduce((s,a)=>s+a.reserve_cents+a.obligations,0),
    bills:due.sort((a,b)=>Date.parse(a.due_at)-Date.parse(b.due_at)),prompts};
}
export function boardPrompts(cards) {
  // A decision lane or a technical blocker alone is not an instruction for Brian.
  // Production Manager may attach a translated, explicit owner action to a card.
  return cards.filter(c=>!/(?:^|\b)(done|verified|closed|completed)(?:\b|$)/i.test(c.implementation_status||''))
    .flatMap(c=>{
      const a=c.context_manifest?.owner_action;
      if(!a || !['action','where','look_for','reply_with','do_not_touch','why'].every(k=>typeof a[k]==='string'&&a[k].trim())) return [];
      return [{id:`owner:${a.root_action_id||c.id}`,category:'decision',title:a.action,tag:'BRIAN NEEDED',
        summary:a.why,steps:a,href:`/admin/production.html?card=${encodeURIComponent(c.id)}`,
        label:'See the exact step',observed_at:c.updated_at}];
    }).filter((p,i,all)=>all.findIndex(x=>x.id===p.id)===i);
}

export function reportDigest(entries, now=Date.now()) {
  return entries.map(({path,label,max_age_hours,document,error})=>{
    const url=`https://github.com/Brian910cpr/910cpr-class-landers/blob/main/${path}`;
    if(error || !document || typeof document!=='object') return {path,label,url,state:'unavailable',reason:'File could not be read',observed_at:null};
    const raw=document.generated_at||document.timestamp||document.finished_at||document.updated_at||document.last_success_at;
    const timestamp=Date.parse(raw);
    const status=String(document.status||document.pipeline_status||document.build_summary?.status||'').toLowerCase();
    const failure=Boolean(document.error||document.errors?.length||/failed|error|blocked/.test(status));
    const state=!Number.isFinite(timestamp)?'unknown':timestamp>now+300000?'unknown':now-timestamp>max_age_hours*3600000?'stale':failure?'attention':'recent';
    return {path,label,url,state,observed_at:Number.isFinite(timestamp)?new Date(timestamp).toISOString():null,
      reason:failure?'Recorded failure':state==='stale'?'Older than its review window':state==='unknown'?'No reliable report time':'Recent report'};
  });
}
