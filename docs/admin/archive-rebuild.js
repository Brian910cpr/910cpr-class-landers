(() => {
  'use strict';
  const API='https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/archive-status';
  const REPO='https://github.com/Brian910cpr/910cpr-class-landers';
  const auth=window.LanderWareAdminAuth,$=id=>document.getElementById(id);
  const labels={SOURCE_RECOVERY:'Source recovery',IDENTITY_RECONCILIATION:'Identity reconciliation',ELIGIBILITY_REVIEW:'Eligibility review',GENERATION:'Generation',VALIDATION:'Validation',SITEMAP:'Sitemap',DEPLOY:'Deployment',GOOGLE_DISCOVERY:'Google discovery',RUNNING:'Running',BLOCKED:'Blocked',CHECKPOINT_COMPLETE:'Checkpoint complete',STALLED:'Checkpoint stalled',CLOCK_MISMATCH:'Checkpoint clock mismatch',CURRENT_INVENTORY_GATE:'Current inventory publication gate',VALIDATION_FAILED:'Validation failed',SOURCE_UNAVAILABLE:'Source unavailable',OPERATOR_REVIEW:'Operator review'};
  let timer=null,active=null,epoch=0,stopped=false,lastPoll=null,lastCheckpoint=null,rerun=false;
  const number=v=>v===null?'Unknown':Number.isSafeInteger(v)&&v>=0?v.toLocaleString():'Unavailable';
  const date=v=>new Date(v).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'medium'});
  const node=(tag,text,cls)=>{const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(cls)el.className=cls;return el;};
  function metric(host,title,value,note) {const el=node('div',undefined,'metric');el.append(node('span',title),node('strong',number(value)));if(note)el.append(node('small',note));host.append(el);}
  function clear(message) {
    $('privateView').hidden=true;lastCheckpoint=null;
    for(const id of ['baseline','progress','events','google','provenance','phase','jobState','checkpointAge','blockers','eligibility','googleWindow'])$(id).replaceChildren();
    $('connection').textContent=message;
  }
  function render(payload) {
    const s=payload.checkpoint;
    if(s?.schema_version!==1||s.issue!==229||!s.baseline||!s.metrics||!Array.isArray(s.events)||!payload.job_health)throw Error('invalid_checkpoint');
    clear('Checkpoint received. Waiting for the next update…'); lastCheckpoint=s;
    $('phase').textContent=labels[s.phase]||'Unknown phase';$('jobState').textContent=labels[payload.job_health.state]||'Unknown state';
    $('checkpointAge').textContent=`Job checkpoint: ${date(s.last_checkpoint_at)} · ${number(payload.job_health.checkpoint_age_seconds)} seconds old`;
    $('blockers').textContent=s.blockers.map(b=>labels[b]||'Review required').join(' · ');
    const p=s.provenance;
    const commit=node('a',p.commit.slice(0,12));commit.href=REPO+'/commit/'+p.commit;
    const provenance=node('p',`Run ${s.run_id} · Revision ${s.revision} · ${p.branch} · `);provenance.append(commit);
    if(p.pr){const pr=node('a',` · PR #${p.pr}`);pr.href=REPO+'/pull/'+p.pr;provenance.append(pr);}
    $('provenance').append(provenance,node('p',`Feed read: ${date(payload.source.fetched_at)} · ${payload.source.ref} · ${payload.source.blob.slice(0,12)}`));
    const b=s.baseline;
    metric($('baseline'),'Source rows recovered',b.source_rows_recovered);
    metric($('baseline'),'Historical HTML URLs',b.html_urls_recovered);
    metric($('baseline'),'Preliminary candidates',b.preliminary_candidates,'Awaiting eligibility approval');
    metric($('baseline'),'Private / ambiguous / review',b.excluded_private_ambiguous_rows,`${number(b.not_elapsed_rows)} additional rows not elapsed`);
    $('eligibility').textContent=s.metrics.eligible_pages===null?'Approved eligible corpus: unresolved. Progress percentages will appear after review.':`Approved eligible corpus: ${number(s.metrics.eligible_pages)} pages.`;
    for(const [key,title] of [['pages_generated','Generated'],['pages_validated','Validated'],['pages_failed_validation','Failed validation'],['sitemap_urls_generated','Sitemap URLs'],['pages_published','Published']]) {
      const row=node('div',undefined,'row');row.append(node('span',title),node('strong',number(s.metrics[key])));
      if(s.metrics.eligible_pages>0){const bar=node('progress');bar.max=s.metrics.eligible_pages;bar.value=s.metrics[key];bar.setAttribute('aria-label',`${title} of approved eligible corpus`);row.append(bar);}
      $('progress').append(row);
    }
    for(const event of s.events) {
      const item=node('li');item.append(node('b',`${labels[event.phase]||'Unknown phase'} · ${labels[event.state]||'Unknown state'}`),node('time',date(event.at)),node('small',`${number(event.metrics.pages_generated)} generated · ${number(event.metrics.pages_validated)} validated · ${number(event.metrics.pages_published)} published`));$('events').append(item);
    }
    for(const [key,title] of [['discovered','Discovered'],['indexed','Indexed'],['class_impressions','Class-page impressions'],['class_clicks','Class-page clicks']])metric($('google'),title,s.gsc[key]);
    $('googleWindow').textContent=s.gsc.observed_at?`Measured ${date(s.gsc.window_start)} to ${date(s.gsc.window_end)}; observed ${date(s.gsc.observed_at)}.`:'No current Google observation has been imported. Sitemap and publication counts do not prove indexing.';
    $('privateView').hidden=false;
  }
  async function poll() {
    if(stopped||document.hidden)return;
    if(active){rerun=true;return;}
    clearTimeout(timer);const version=epoch,stamp=auth.snapshot(),controller=new AbortController();active=controller;
    const timeout=setTimeout(()=>controller.abort(),15000);
    try {
      const response=await auth.fetch(API,{signal:controller.signal});
      if(!response.ok)throw Error('status_unavailable');
      const payload=await response.json();
      if(version!==epoch||stopped||!auth.current(stamp))return;
      render(payload);lastPoll=Date.now();$('pollAge').textContent=`Last successful read: ${date(lastPoll)} · checks every 20 seconds. This does not advance the job heartbeat.`;
    } catch {
      if(version===epoch&&!stopped){clear('Archive status is unavailable. Retrying in 20 seconds.');$('pollAge').textContent=lastPoll?`Last successful read: ${date(lastPoll)}. Current counts are hidden until a verified response returns.`:'No successful status read yet. Owner access or status delivery may need repair.';}
    } finally {
      clearTimeout(timeout);active=null;
      if(!stopped&&!document.hidden){timer=setTimeout(poll,rerun?0:20000);rerun=false;}
    }
  }
  function lock() {epoch++;stopped=true;rerun=false;clearTimeout(timer);active?.abort();clear('Owner access changed. Reopening your private workspace…');$('pollAge').textContent='Private checkpoint details cleared.';}
  function resume() {epoch++;stopped=false;if(active){rerun=true;active.abort();}else poll();}
  if(!auth){clear('Owner sign-in could not load. Reload this page.');return;}
  auth.onLock(lock);window.addEventListener('admin-auth-refresh',resume);
  document.addEventListener('visibilitychange',()=>{if(document.hidden){epoch++;clearTimeout(timer);active?.abort();clear('Monitor paused while this tab is hidden.');}else resume();});
  $('signOut').addEventListener('click',()=>auth.clear());
  $('copyDiagnostics').addEventListener('click',async()=>{
    const diagnostics={url:location.origin+location.pathname,page_id:'archive-rebuild',build_id:'issue229-owner-monitor-r4',deployment_timestamp:null,asset_version:'20260914-archive4',last_successful_poll:lastPoll?new Date(lastPoll).toISOString():null,checkpoint_commit:lastCheckpoint?.provenance.commit||null};
    try{await navigator.clipboard.writeText(JSON.stringify(diagnostics,null,2));$('diagnosticStatus').textContent='Copied';}catch{$('diagnosticStatus').textContent='Copy unavailable in this browser';}
  });
  poll();
})();
