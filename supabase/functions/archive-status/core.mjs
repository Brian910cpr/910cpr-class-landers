// Consume the existing Python checkpoint contract; never return arbitrary source fields.
export const REPO = 'Brian910cpr/910cpr-class-landers';
export const STATUS_PATH = 'data/audit/issue229_archive_rebuild_status.json';
const PHASES = ['SOURCE_RECOVERY','IDENTITY_RECONCILIATION','ELIGIBILITY_REVIEW','GENERATION','VALIDATION','SITEMAP','DEPLOY','GOOGLE_DISCOVERY'];
const STATES = ['RUNNING','BLOCKED','CHECKPOINT_COMPLETE'];
const BLOCKERS = ['ELIGIBILITY_REVIEW','CURRENT_INVENTORY_GATE','VALIDATION_FAILED','SOURCE_UNAVAILABLE','OPERATOR_REVIEW'];
const COUNTS = ['eligible_pages','pages_generated','pages_validated','pages_failed_validation','sitemap_urls_generated','pages_published'];
const GSC = ['discovered','indexed','class_impressions','class_clicks'];
function require(ok) { if (!ok) throw Error('invalid_checkpoint'); }
function keys(value, names) { require(value && typeof value==='object' && !Array.isArray(value) && Object.keys(value).sort().join('|')===[...names].sort().join('|')); }
function count(value, nullable=false) { require((nullable&&value===null)||(Number.isSafeInteger(value)&&value>=0)); }
function at(value) { require(typeof value==='string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)$/.test(value) && Number.isFinite(Date.parse(value))); require(new Date(value.slice(0,10)).toISOString().slice(0,10)===value.slice(0,10)); return Date.parse(value); }
function ref(value) { keys(value,['commit','path']); require(typeof value.commit==='string' && typeof value.path==='string' && /^[0-9a-f]{40}$/.test(value.commit) && /^data\/audit\/[a-zA-Z0-9_-]+\.(json|md)$/.test(value.path)); }
function counters(m,e) {
  keys(m,COUNTS); for (const k of COUNTS) count(m[k],k==='eligible_pages');
  require(m.eligible_pages===null || e.eligibility!==null);
  require(!m.pages_generated || m.eligible_pages!==null);
  require(m.eligible_pages===null || m.pages_generated<=m.eligible_pages);
  require(m.pages_validated+m.pages_failed_validation<=m.pages_generated);
  require(m.sitemap_urls_generated<=m.pages_validated && m.pages_published<=m.pages_validated);
  require(!m.pages_validated || e.validation!==null); require(!m.pages_published || e.deployment!==null);
}
export function validateCheckpoint(s) {
  keys(s,['schema_version','issue','run_id','revision','phase','state','blockers','last_checkpoint_at','expected_checkpoint_seconds','producer_mode','provenance','baseline','metrics','evidence','gsc','events']);
  require(s.schema_version===1 && s.issue===229 && typeof s.run_id==='string' && /^[a-z0-9][a-z0-9_-]{0,79}$/.test(s.run_id));
  count(s.revision); require(PHASES.includes(s.phase)&&STATES.includes(s.state));
  require(Array.isArray(s.blockers)&&s.blockers.every(b=>BLOCKERS.includes(b)) && Boolean(s.blockers.length)===(s.state==='BLOCKED'));
  at(s.last_checkpoint_at); require(s.expected_checkpoint_seconds===300 && s.producer_mode==='local_checkpoints');
  const p=s.provenance;
  keys(p,['repository','branch','commit','pr','sources']);
  require(p.repository===REPO && typeof p.branch==='string' && /^codex\/[a-zA-Z0-9/_-]{1,120}$/.test(p.branch) && typeof p.commit==='string' && /^[0-9a-f]{40}$/.test(p.commit));
  require(p.pr===null || (Number.isSafeInteger(p.pr)&&p.pr>0)); require(Array.isArray(p.sources)&&p.sources.length===2); p.sources.forEach(ref);
  const b=s.baseline;
  keys(b,['source_rows_recovered','html_urls_recovered','preliminary_candidates','non_candidate_rows','excluded_private_ambiguous_rows','not_elapsed_rows','classification','identity_rows_reconciled','orphan_html_unresolved']);
  for(const [k,v] of Object.entries(b)) if(k!=='classification') count(v);
  keys(b.classification,['client_present_review','invalid_or_ambiguous_timing','non_public_location_review','not_elapsed_at_cutoff','preliminary_public_candidate_requires_review','workbook_provenance_unresolved']);
  Object.values(b.classification).forEach(v=>count(v));
  require(Object.values(b.classification).reduce((a,v)=>a+v,0)===b.source_rows_recovered);
  require(b.preliminary_candidates===b.classification.preliminary_public_candidate_requires_review && b.not_elapsed_rows===b.classification.not_elapsed_at_cutoff);
  require(b.non_candidate_rows===b.source_rows_recovered-b.preliminary_candidates && b.excluded_private_ambiguous_rows===b.non_candidate_rows-b.not_elapsed_rows && b.identity_rows_reconciled===b.source_rows_recovered);
  keys(s.evidence,['eligibility','validation','deployment','gsc']); for(const r of Object.values(s.evidence)) if(r!==null) ref(r);
  counters(s.metrics,s.evidence); require(s.metrics.eligible_pages===null || s.metrics.eligible_pages<=b.source_rows_recovered);
  require(PHASES.indexOf(s.phase)<3 || s.metrics.eligible_pages!==null);
  keys(s.gsc,[...GSC,'observed_at','window_start','window_end']); GSC.forEach(k=>count(s.gsc[k],true));
  if(GSC.some(k=>s.gsc[k]!==null)) {
    require(s.evidence.gsc!==null && at(s.gsc.window_start)<=at(s.gsc.window_end) && at(s.gsc.window_end)<=at(s.gsc.observed_at) && at(s.gsc.observed_at)<=at(s.last_checkpoint_at));
  } else require(['observed_at','window_start','window_end'].every(k=>s.gsc[k]===null));
  require(Array.isArray(s.events)&&s.events.length>0&&s.events.length<=100);
  let previous=at(s.last_checkpoint_at);
  for(const e of s.events) {
    keys(e,['phase','state','at','revision','metrics']); require(PHASES.includes(e.phase)&&STATES.includes(e.state)); count(e.revision);
    require(e.revision<=s.revision && at(e.at)<=previous); previous=at(e.at); counters(e.metrics,s.evidence);
  }
  const newest=s.events[0]; require(newest.phase===s.phase&&newest.state===s.state&&newest.at===s.last_checkpoint_at&&newest.revision===s.revision&&COUNTS.every(k=>newest.metrics[k]===s.metrics[k]));
  return structuredClone(s);
}

export function jobHealth(s, now=Date.now()) {
  const age=(now-at(s.last_checkpoint_at))/1000;
  return {state:age<0?'CLOCK_MISMATCH':s.state==='RUNNING'&&age>s.expected_checkpoint_seconds?'STALLED':s.state,checkpoint_age_seconds:Math.max(0,Math.floor(age))};
}

// Only a server-configured repository ref is accepted. Clients cannot select a source.
export function createGithubSource({token, sourceRef='main', send=fetch, now=Date.now}={}) {
  require(sourceRef==='main'||/^codex\/[a-zA-Z0-9/_-]{1,120}$/.test(sourceRef));
  let cached=null,pending=null;
  return async function read() {
    if(!token) throw Error('status_source_unconfigured');
    if(cached && now()-cached.at<10000) return structuredClone(cached.value);
    if(!pending) pending=(async()=>{
      const r=await send(`https://api.github.com/repos/${REPO}/contents/${STATUS_PATH}?ref=${encodeURIComponent(sourceRef)}`,{
        headers:{Accept:'application/vnd.github+json',Authorization:`Bearer ${token}`,'User-Agent':'LanderWare-archive-monitor'},
        cache:'no-store',redirect:'error',signal:AbortSignal.timeout(10000)
      });
      if(!r.ok) throw Error('status_source_unavailable');
      const text=await r.text(); require(text.length<=200000);
      const body=JSON.parse(text); require(body.encoding==='base64' && typeof body.content==='string' && /^[0-9a-f]{40}$/.test(body.sha));
      const decoded=atob(body.content.replace(/\s/g,'')); require(decoded.length<=130000);
      const checkpoint=validateCheckpoint(JSON.parse(decoded));
      const value={checkpoint,source:{ref:sourceRef,blob:body.sha,fetched_at:new Date(now()).toISOString()}};
      cached={at:now(),value}; return value;
    })();
    try {return structuredClone(await pending);} finally {pending=null;}
  };
}
