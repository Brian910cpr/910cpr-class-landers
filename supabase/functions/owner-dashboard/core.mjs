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
  return cards.filter(c=>!/(?:^|\b)(done|verified|closed|completed)(?:\b|$)/i.test(c.implementation_status||'') &&
    (c.lane==='decision' || String(c.context_manifest?.next_actor||'').toLowerCase()==='brian'))
    .map(c=>({id:`board:${c.id}`,category:'decision',title:c.title,tag:c.lane==='decision'?'YOUR DECISION':'BRIAN NEEDED',
      summary:c.summary||'Open the work item for the requested decision.',href:`/admin/production.html?card=${encodeURIComponent(c.id)}`,label:'Open decision',observed_at:c.updated_at}));
}
