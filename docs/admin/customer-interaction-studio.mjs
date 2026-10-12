import {createInteractionClient} from './customer-interaction-client.mjs?v=20261012-ui1';
import {createInteractionCheckpoint} from './customer-interaction-checkpoint.mjs?v=20261012-ui1';

// Default-off integration. The gate controls rollout only; the server still
// authorizes every request. Never import sessionStorage prototype drafts.
export function mountInteractionStudio({document,window,auth,enabled=false,client,uuid=()=>crypto.randomUUID(),delay=700}) {
  if(!enabled)return null;
  client??=createInteractionClient(auth,{enabled:true});
  const $=id=>document.getElementById(id);
  const fields=['customer','contact','callNotes','intent','evidence','plan','resolution','recipient','subject','reply','feedback'];
  let checkpoint=null,rows=[],cursor=null,timer=null,loading=false,locked=false,remote=null;
  const notify=message=>{$('storageStatus').textContent=message;};
  function controls(){
    const view=checkpoint?.view();
    for(const f of fields)$(f).disabled=locked||loading||!checkpoint;
    $('kind').disabled=true;
    $('saveCheckpoint').disabled=locked||!view||view.state==='saving'||view.state==='conflict';
    $('retryCheckpoint').disabled=locked||view?.state!=='error';
    $('reviewConflict').disabled=locked||view?.state!=='conflict';
    $('keepConflictDraft').disabled=locked||!remote;
    $('reloadStored').disabled=locked||loading||Boolean(checkpoint&&!checkpoint.canLeave());
    $('loadMoreStored').disabled=locked||loading||!cursor||Boolean(checkpoint&&!checkpoint.canLeave());
    $('newEmail').disabled=locked||loading||Boolean(checkpoint&&!checkpoint.canLeave());
    // Do not degrade an atomic call interruption into independent saves.
    $('newCall').disabled=locked||loading||Boolean(checkpoint);
    for(const id of ['finish','clearCase'])$(id).disabled=true;
    for(const id of ['copyCase','downloadCase','copyReply'])$(id).disabled=locked||!checkpoint;
  }
  function state(){
    const v=checkpoint?.view();controls();
    if(!v)return;
    const messages={saved:'Saved on server. No external action executed.',unsaved:'Unsaved changes — keep this page open.',saving:'Saving checkpoint… keep this page open.',error:'Save not confirmed. Keep this page open; Retry reuses the same request.',conflict:'Conflict or sign-in changed. Draft retained; review stored work before saving.'};
    notify(messages[v.state]+(v.error?' '+v.error:''));
  }
  function populate(){
    const draft=checkpoint?.view().draft;
    for(const f of fields)$(f).value=typeof draft?.document?.[f]==='string'?draft.document[f]:'';
    $('kind').value=draft?.kind||'phone';state();render();
  }
  function guard(){if(locked||loading||checkpoint&&!checkpoint.canLeave()){notify('Confirm all edits on server before navigating. Your draft is retained.');return false}return true}
  function render(){
    const host=$('queueList');host.replaceChildren();
    for(const row of rows){
      const button=document.createElement('button');button.type='button';
      button.textContent=(row.document?.customer||'Unidentified contact')+' · '+row.kind+' · '+row.status;
      button.setAttribute('aria-current',String(row.id===checkpoint?.view().draft.id));
      button.onclick=async()=>{if(!guard())return;await open(row.id)};host.append(button);
    }
    if(!rows.length){const p=document.createElement('p');p.textContent='No stored interactions loaded.';host.append(p)}
  }
  async function open(id){
    loading=true;controls();notify('Loading current server version…');
    try{
      const data=await client.list({collection:'interactions',interaction_id:id});
      if(locked)return;
      const record=data.items.find(r=>r.id===id);if(!record)throw Error('Stored interaction unavailable.');
      // A fetched server version is already a confirmed checkpoint.
      // Seed through the constructor's explicit confirmed option, not a write.
      checkpoint=createInteractionCheckpoint(client,{...record,expected_version:record.version},{confirmed:true});
      remote=null;$('serverConflict').textContent='';populate();
    }catch(e){notify('Load failed: '+e.message+'. Retry loading; current draft is retained.')}
    finally{loading=false;controls()}
  }
  async function load(more=false){
    if(!guard())return;
    loading=true;controls();notify('Loading stored interactions…');
    try{
      const data=await client.list({collection:'interactions',...(more?cursor:{})});
      if(locked)return;
      rows=more?[...new Map([...rows,...data.items].map(r=>[r.id,r])).values()]:data.items;
      cursor=data.next_cursor;render();notify('Stored interactions loaded. Select one to retrieve its current version.');
    }catch(e){notify('Stored interactions unavailable: '+e.message+'. Retry loading.')}
    finally{loading=false;controls()}
  }
  async function save(){
    window.clearTimeout(timer);timer=null;if(locked||!checkpoint)return;
    const current=checkpoint;
    try{const flight=current.save();state();await flight;if(locked||current!==checkpoint)return;
      const d=current.view().draft;const row={...d,version:d.expected_version};rows=[row,...rows.filter(r=>r.id!==d.id)];render();state();
      if(current.view().state==='unsaved')schedule();
    }catch{if(!locked)state()}
  }
  function schedule(){window.clearTimeout(timer);timer=window.setTimeout(()=>{void save()},delay)}
  function edit(){
    if(locked||!checkpoint)return;
    const doc={...checkpoint.view().draft.document};for(const f of fields)doc[f]=$(f).value;
    checkpoint.edit(doc);remote=null;$('serverConflict').textContent='';state();
    if(checkpoint.view().state==='unsaved')schedule();
  }
  function fresh(kind){
    if(!guard())return;
    const id=uuid();checkpoint=createInteractionCheckpoint(client,{id,case_id:uuid(),expected_version:0,kind,status:'in_progress',source:'manual',source_id:id,person_id:null,document:{resolution:'Customer email reply',captured_at:new Date().toISOString()}});
    populate();schedule();$('customer').focus();
  }
  async function review(){
    if(locked||checkpoint?.view().state!=='conflict')return;
    const current=checkpoint;remote=null;controls();
    try{
      const id=current.view().draft.id;const data=await client.list({collection:'interactions',interaction_id:id});
      if(locked||checkpoint!==current)return;
      const record=data.items.find(r=>r.id===id);if(!record)throw Error('No stored version found; retain/export draft for recovery.');
      remote=record;$('serverConflict').textContent=JSON.stringify({version:record.version,document:record.document},null,2);
      notify('Compare stored work below with your retained draft. Explicitly merge edits before choosing Keep reviewed draft.');controls();
    }catch(e){notify('Cannot review conflict: '+e.message);controls()}
  }
  function lock(){
    locked=true;window.clearTimeout(timer);checkpoint=null;rows=[];remote=null;cursor=null;
    for(const f of fields)$(f).value='';$('serverConflict').textContent='';render();controls();notify('Owner session locked. Reopen after sign-in to load stored work.');
  }
  for(const f of fields)$(f).addEventListener('input',edit);
  $('saveCheckpoint').onclick=save;$('retryCheckpoint').onclick=save;
  $('reloadStored').onclick=()=>load();$('loadMoreStored').onclick=()=>load(true);
  $('newEmail').onclick=()=>fresh('email');$('newCall').onclick=()=>fresh('phone');
  $('reviewConflict').onclick=review;
  $('keepConflictDraft').onclick=()=>{if(!remote||locked)return;checkpoint.reconcile(remote);remote=null;$('serverConflict').textContent='';state();};
  $('coachButtons').addEventListener('click',event=>{const button=event.target.closest('button[data-coach]');if(!button||!checkpoint||locked)return;$('feedback').value+='\n['+button.dataset.coach+'] ';edit()});
  $('copyReply').onclick=async()=>{try{await window.navigator.clipboard.writeText($('reply').value);notify('Draft copied; nothing sent.')}catch{notify('Clipboard unavailable. Select and copy draft manually.')}};
  $('copyCase').onclick=async()=>{try{await window.navigator.clipboard.writeText(JSON.stringify(checkpoint.view().draft,null,2));notify('Case copied. Review private information before sharing.')}catch{notify('Clipboard unavailable; export the draft.')}};
  $('downloadCase').onclick=()=>{const url=window.URL.createObjectURL(new Blob([JSON.stringify(checkpoint.view().draft,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='customer-interaction-draft.json';a.click();window.setTimeout(()=>window.URL.revokeObjectURL(url),1000)};
  window.addEventListener('beforeunload',event=>{if(checkpoint&&!checkpoint.canLeave()){event.preventDefault();event.returnValue=''}});
  document.addEventListener('click',event=>{if(event.target.closest('a[href]')&&checkpoint&&!checkpoint.canLeave()){event.preventDefault();notify('Save or export pending changes before leaving this page.')}});
  auth?.onLock(lock);
  $('prototypeBanner').textContent='Durable CRM validation mode. Server-confirmed checkpoints only; unsaved changes can be lost on closure. No external actions, customer matching, interruption/resume or task disposition enabled in this slice. Existing tab-local drafts are not imported. Production Board attention remains read-only.';
  $('queueTitle').textContent='Stored interactions';$('captureHelp').textContent='Save before switching cases. Interruption/resume and follow-up disposition await atomic integration.';
  $('status').textContent='No outbound action is connected.';controls();void load();
  return Object.freeze({load,save,edit,fresh,view:()=>checkpoint?.view(),lock});
}
