import {createFollowUpTaskWrite,createFollowUpTaskDisposition} from './customer-interaction-task.mjs?v=20261014-taskcontrols1';
import {createInteractionClient} from './customer-interaction-client.mjs?v=20261014-taskcontrols1';
import {createInteractionCheckpoint} from './customer-interaction-checkpoint.mjs?v=20261014-taskcontrols1';

import {createInteractionSwitch,findInteractionInterruption} from './customer-interaction-switch.mjs?v=20261014-taskcontrols1';

// Default-off integration. The gate controls rollout only; the server still
// authorizes every request. Never import sessionStorage prototype drafts.
export function mountInteractionStudio({document,window,auth,enabled=false,client,uuid=()=>crypto.randomUUID(),delay=700}) {
  if(!enabled)return null;
  client??=createInteractionClient(auth,{enabled:true});
  const $=id=>document.getElementById(id);
  const fields=['customer','contact','callNotes','intent','evidence','plan','resolution','recipient','subject','reply','feedback'];
  let checkpoint=null,rows=[],cursor=null,timer=null,loading=false,locked=false,remote=null,switching=null,interruption=null,taskWrite=null,selectedTask=null,tasks=[],switchTasks=[];
  const notify=message=>{$('storageStatus').textContent=message;};
  const taskDirty=()=>Boolean(taskWrite&&!taskWrite.canLeave())||Boolean(selectedTask)||Boolean($('followUpTitle').value.trim()||$('followUpEvidence').value.trim());
  function controls(){
    const view=checkpoint?.view();
    const frozen=locked||loading||Boolean(switching)||Boolean(taskWrite&&!taskWrite.canLeave());
    for(const f of fields)$(f).disabled=frozen||Boolean(selectedTask)||!checkpoint;
    $('kind').disabled=true;
    for(const id of ['followUpTitle','followUpEvidence'])$(id).disabled=frozen||Boolean(selectedTask)||!checkpoint;
    $('saveFollowUp').disabled=frozen||Boolean(selectedTask)||!checkpoint?.canLeave()||!$('followUpTitle').value.trim()||!$('followUpEvidence').value.trim();
    for(const id of ['taskStatus','taskDispositionEvidence','taskDueAt'])$(id).disabled=frozen||!selectedTask;
    $('saveTaskDisposition').disabled=frozen||!selectedTask||!checkpoint?.canLeave()||!$('taskDispositionEvidence').value.trim()||$('taskStatus').value===selectedTask.status;
    $('cancelTaskDisposition').disabled=frozen||!selectedTask;
    for(const button of document.querySelectorAll('[data-task-disposition]'))button.disabled=frozen||Boolean(selectedTask)||!checkpoint?.canLeave()||taskDirty();
    $('retryFollowUp').disabled=locked||loading||taskWrite?.view().state!=='error';
    $('resumePrevious').textContent='Finish call / resume previous (checks follow-ups)';
    $('saveCheckpoint').disabled=frozen||Boolean(selectedTask)||!view||view.state==='saving'||view.state==='conflict';
    $('retryCheckpoint').disabled=locked||loading||(switching?switching.view().state!=='error':view?.state!=='error');
    $('reviewConflict').disabled=frozen||view?.state!=='conflict';
    $('keepConflictDraft').disabled=frozen||!remote;
    $('reloadStored').disabled=frozen||Boolean(checkpoint&&(!checkpoint.canLeave()||taskDirty()));
    $('loadMoreStored').disabled=frozen||!cursor||Boolean(checkpoint&&(!checkpoint.canLeave()||taskDirty()));
    $('newEmail').disabled=frozen||Boolean(checkpoint&&(!checkpoint.canLeave()||taskDirty()));
    // First slice permits one interruption level; save all edits before switching.
    $('newCall').disabled=frozen||Boolean(checkpoint&&(!checkpoint.canLeave()||taskDirty()||!['email','manual'].includes(view.draft.kind)||!['new','in_progress','awaiting_data','awaiting_approval','follow_up_due'].includes(view.draft.status)));
    $('resumePrevious').disabled=frozen||!interruption||(!checkpoint?.canLeave()||taskDirty())||view?.draft.status!=='in_progress';
    for(const id of ['finish','clearCase'])$(id).disabled=true;
    for(const id of ['copyCase','downloadCase','copyReply'])$(id).disabled=locked||!checkpoint;
  }
  function state(){
    const v=checkpoint?.view();controls();
    if(taskWrite&&!taskWrite.canLeave()){const t=taskWrite.view();notify(t.state==='saving'?'Saving follow-up… keep this page open.':t.state==='conflict'?'Follow-up conflict. Draft retained; export and reload for server review.':'Follow-up not confirmed. Draft retained; Retry follow-up reuses the same request.');return;}
    if(switching){const v=switching.view();notify(v.state==='saving'?'Saving atomic interruption/resume... keep this page open.':v.state==='conflict'?'Atomic switch conflict. Both drafts retained. Export both drafts before reloading and reviewing current server work.':'Atomic switch not confirmed. Both drafts retained; Retry reuses the same request.');return;}
    if(!v)return;
    if(taskDirty()){notify('Unsaved follow-up — save it before navigating.');return;}
    const messages={saved:'Saved on server. No external action executed.',unsaved:'Unsaved changes — keep this page open.',saving:'Saving checkpoint… keep this page open.',error:'Save not confirmed. Keep this page open; Retry reuses the same request.',conflict:'Conflict or sign-in changed. Draft retained; review stored work before saving.'};
    notify(messages[v.state]+(v.error?' '+v.error:''));
  }
  function populate(){
    const draft=checkpoint?.view().draft;
    for(const f of fields)$(f).value=typeof draft?.document?.[f]==='string'?draft.document[f]:'';
    $('kind').value=draft?.kind||'phone';state();render();
  }
  function guard(){if(locked||loading||switching||checkpoint&&(!checkpoint.canLeave()||taskDirty())){notify('Confirm all edits on server before navigating. Your draft is retained.');return false}return true}
  function render(){
    const host=$('queueList');host.replaceChildren();
    for(const row of rows){
      const button=document.createElement('button');button.type='button';
      button.textContent=(row.document?.customer||'Unidentified contact')+' · '+row.kind+' · '+row.status;
      button.setAttribute('aria-current',String(row.id===checkpoint?.view().draft.id));
      button.onclick=async()=>{if(!guard())return;await open(row.id)};host.append(button);
    }
    const hostTasks=$('storedFollowUps');hostTasks.replaceChildren();
    for(const task of tasks){const p=document.createElement('p');p.textContent=task.title+' · '+task.status+' · No reminder scheduled';hostTasks.append(p);const button=document.createElement('button');button.type='button';button.textContent='Change follow-up status';button.setAttribute('data-task-disposition',task.id);button.onclick=()=>chooseTask(task);hostTasks.append(button)}
    controls();
    if(!rows.length){const p=document.createElement('p');p.textContent='No stored interactions loaded.';host.append(p)}
  }
  async function readTasks(id){
    let cursor=null;const found=[],seen=new Set();
    do{
      const page=await client.list({collection:'tasks',interaction_id:id,...(cursor??{})});
      if(page.items.some(t=>t.interaction_id!==id||!['proposed','pending','snoozed','complete'].includes(t.status)))throw Error('Unexpected follow-up linkage; reload and review.');
      found.push(...page.items);cursor=page.next_cursor;
      if(cursor){const key=JSON.stringify(cursor);if(seen.has(key))throw Error('Repeated task cursor; follow-up recovery incomplete.');seen.add(key)}
    }while(cursor);
    return [...new Map(found.map(t=>[t.id,t])).values()];
  }
  function clearDisposition(){selectedTask=null;$('taskDispositionEvidence').value='';$('taskDueAt').value='';$('taskDispositionTitle').textContent='Select a stored follow-up to change status.';}
  function chooseTask(task){
    if(!guard()||taskDirty()||!checkpoint?.canLeave())return;
    selectedTask=structuredClone(task);$('taskStatus').value=task.status==='complete'?'pending':'complete';$('taskDispositionTitle').textContent=task.title+' - stored version '+task.version;state();
  }
  async function saveDisposition(){
    if(locked||loading||switching||!selectedTask||!checkpoint?.canLeave()||taskWrite)return;
    try{taskWrite=createFollowUpTaskDisposition(client,selectedTask,{status:$('taskStatus').value,evidence:$('taskDispositionEvidence').value,dueAt:$('taskDueAt').value?new Date($('taskDueAt').value).toISOString():undefined});await sendTask()}
    catch(e){notify('Disposition unavailable: '+e.message);controls()}
  }
  function resetTasks(){clearDisposition();taskWrite=null;tasks=[];$('followUpTitle').value='';$('followUpEvidence').value='';}
  async function sendTask(){
    if(locked||!taskWrite)return;
    const pending=taskWrite;
    try{const flight=pending.send();state();const task=await flight;
      if(locked||pending!==taskWrite)return;
      tasks=[task,...tasks.filter(t=>t.id!==task.id)];taskWrite=null;clearDisposition();$('followUpTitle').value='';$('followUpEvidence').value='';render();state();
    }catch{if(!locked)state()}
  }
  async function saveTask(){
    if(locked||loading||switching||!checkpoint?.canLeave()||taskWrite&&!taskWrite.canLeave())return;
    const title=$('followUpTitle').value.trim(),evidence=$('followUpEvidence').value.trim();
    if(!title||!evidence||selectedTask)return;
    const current=checkpoint.view().draft,id=uuid();
    try{taskWrite=createFollowUpTaskWrite(client,{id,case_id:current.case_id,interaction_id:current.id,expected_version:0,source_key:'manual:'+id,title,status:'pending',provenance:{evidence,source:'owner_studio',interaction_version:current.expected_version}});await sendTask()}
    catch(e){notify('Follow-up unavailable: '+e.message);controls()}
  }
  async function open(id){
    loading=true;controls();notify('Loading current server version…');
    try{
      const data=await client.list({collection:'interactions',interaction_id:id});
      if(locked)return;
      const record=data.items.find(r=>r.id===id);if(!record)throw Error('Stored interaction unavailable.');
      // A fetched server version is already a confirmed checkpoint.
      // Seed through the constructor's explicit confirmed option, not a write.
      const recovered=record.kind==='phone'&&record.status==='in_progress'?await findInteractionInterruption(client,record.id):null;
      if(locked)return;
      const recoveredTasks=await readTasks(id);if(locked)return;
      resetTasks();tasks=recoveredTasks;interruption=recovered;checkpoint=createInteractionCheckpoint(client,{...record,expected_version:record.version},{confirmed:true});
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
    window.clearTimeout(timer);timer=null;if(locked||switching||selectedTask||taskWrite&&!taskWrite.canLeave()||!checkpoint)return;
    const current=checkpoint;
    try{const flight=current.save();state();await flight;if(locked||current!==checkpoint)return;
      const d=current.view().draft;const row={...d,version:d.expected_version};rows=[row,...rows.filter(r=>r.id!==d.id)];render();state();
      if(current.view().state==='unsaved')schedule();
    }catch{if(!locked)state()}
  }
  function schedule(){window.clearTimeout(timer);timer=window.setTimeout(()=>{void save()},delay)}
  function edit(){
    if(locked||switching||selectedTask||taskWrite&&!taskWrite.canLeave()||!checkpoint)return;
    const doc={...checkpoint.view().draft.document};for(const f of fields)doc[f]=$(f).value;
    checkpoint.edit(doc);remote=null;$('serverConflict').textContent='';state();
    if(checkpoint.view().state==='unsaved')schedule();
  }
  function fresh(kind){
    if(!guard())return;
    resetTasks();interruption=null;const id=uuid();checkpoint=createInteractionCheckpoint(client,{id,case_id:uuid(),expected_version:0,kind,status:'in_progress',source:'manual',source_id:id,person_id:null,document:{resolution:'Customer email reply',captured_at:new Date().toISOString()}});
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
  function fromRecord(record){return {...record,expected_version:record.version}}
  function newPhone(){const id=uuid();return {id,case_id:uuid(),expected_version:0,kind:'phone',status:'in_progress',source:'manual',source_id:id,person_id:null,document:{resolution:'Phone recap',captured_at:new Date().toISOString()}}}
  async function sendSwitch(){
    if(locked||!switching)return;
    const pending=switching;
    try{
      const flight=pending.send();state();const result=await flight;
      if(locked||pending!==switching)return;
      const isInterrupt=pending.view().operation==='interrupt';
      rows=[result.previous,result.active,...rows.filter(r=>![result.previous.id,result.active.id].includes(r.id))];
      resetTasks();tasks=switchTasks;switchTasks=[];interruption=isInterrupt?{request_id:result.request_id,input:pending.view().input}:null;
      checkpoint=createInteractionCheckpoint(client,fromRecord(isInterrupt?result.active:result.previous),{confirmed:true});
      switching=null;populate();$('customer').focus();
    }catch{if(!locked)state()}
  }
  async function interrupt(){
    if(!checkpoint){fresh('phone');return}
    if(!guard())return;
    const previous=checkpoint.view().draft;
    if(!['email','manual'].includes(previous.kind))return;
    window.clearTimeout(timer);
    try{switchTasks=[];switching=createInteractionSwitch(client,'interrupt',{previous:{...previous,status:'paused'},active:newPhone()});await sendSwitch()}
    catch(e){notify('Interruption unavailable: '+e.message);controls()}
  }
  async function resume(){
    if(!guard()||!interruption)return;
    loading=true;controls();notify('Loading paused server checkpoint...');
    try{
      const active=checkpoint.view().draft;
      const data=await client.list({collection:'interactions',interaction_id:interruption.input.previous.id});
      if(locked)return;
      const previous=data.items.find(r=>r.id===interruption.input.previous.id);
      if(!previous||previous.status!=='paused')throw Error('Previous work is no longer paused. Reload and review both interactions.');
      // Fresh paginated tasks determine bookkeeping only, never external completion.
      const currentTasks=await readTasks(active.id);if(locked)return;
      switchTasks=await readTasks(previous.id);if(locked)return;
      const hasFollowUp=currentTasks.some(t=>t.status!=='complete');
      switching=createInteractionSwitch(client,'resume',{interrupt_request_id:interruption.request_id,previous:{...fromRecord(previous),status:'in_progress'},active:{...active,status:hasFollowUp?'follow_up_due':'resolved'}});
    }catch(e){notify('Resume unavailable: '+e.message)}
    finally{loading=false;controls()}
    if(switching)await sendSwitch();
  }
  function exportDraft(){if(taskWrite||taskDirty())return {current:checkpoint?.view().draft,pendingTask:taskWrite?.view(),dispositionDraft:selectedTask?{record:selectedTask,status:$('taskStatus').value,evidence:$('taskDispositionEvidence').value,dueAt:$('taskDueAt').value}:null,followUpDraft:{title:$('followUpTitle').value,evidence:$('followUpEvidence').value},tasks};return switching?{pendingSwitch:switching.view(),current:checkpoint?.view().draft}:checkpoint?.view().draft}
  function lock(){
    locked=true;resetTasks();window.clearTimeout(timer);checkpoint=null;rows=[];remote=null;cursor=null;switching=null;interruption=null;switchTasks=[];
    for(const f of fields)$(f).value='';$('serverConflict').textContent='';render();controls();notify('Owner session locked. Reopen after sign-in to load stored work.');
  }
  for(const f of fields)$(f).addEventListener('input',edit);
  for(const id of ['followUpTitle','followUpEvidence'])$(id).addEventListener('input',state);
  for(const id of ['taskStatus','taskDispositionEvidence','taskDueAt'])$(id).addEventListener('input',state);
  $('saveTaskDisposition').onclick=saveDisposition;$('cancelTaskDisposition').onclick=()=>{if(taskWrite||locked)return;clearDisposition();state()};
  $('saveFollowUp').onclick=saveTask;$('retryFollowUp').onclick=sendTask;
  $('saveCheckpoint').onclick=save;$('retryCheckpoint').onclick=()=>switching?sendSwitch():save();
  $('reloadStored').onclick=()=>load();$('loadMoreStored').onclick=()=>load(true);
  $('newEmail').onclick=()=>fresh('email');$('newCall').onclick=interrupt;$('resumePrevious').onclick=resume;
  $('reviewConflict').onclick=review;
  $('keepConflictDraft').onclick=()=>{if(!remote||locked)return;checkpoint.reconcile(remote);remote=null;$('serverConflict').textContent='';state();};
  $('coachButtons').addEventListener('click',event=>{const button=event.target.closest('button[data-coach]');if(!button||!checkpoint||locked||loading||switching||selectedTask||taskWrite&&!taskWrite.canLeave())return;$('feedback').value+='\n['+button.dataset.coach+'] ';edit()});
  $('copyReply').onclick=async()=>{try{await window.navigator.clipboard.writeText($('reply').value);notify('Draft copied; nothing sent.')}catch{notify('Clipboard unavailable. Select and copy draft manually.')}};
  $('copyCase').onclick=async()=>{try{await window.navigator.clipboard.writeText(JSON.stringify(exportDraft(),null,2));notify('Case copied. Review private information before sharing.')}catch{notify('Clipboard unavailable; export the draft.')}};
  $('downloadCase').onclick=()=>{const url=window.URL.createObjectURL(new Blob([JSON.stringify(exportDraft(),null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='customer-interaction-draft.json';a.click();window.setTimeout(()=>window.URL.revokeObjectURL(url),1000)};
  window.addEventListener('beforeunload',event=>{if(switching||checkpoint&&(!checkpoint.canLeave()||taskDirty())){event.preventDefault();event.returnValue=''}});
  document.addEventListener('click',event=>{if(event.target.closest('a[href]')&&(switching||checkpoint&&(!checkpoint.canLeave()||taskDirty()))){event.preventDefault();notify('Save or export pending changes before leaving this page.')}});
  auth?.onLock(lock);
  $('prototypeBanner').textContent='Durable CRM validation mode. Server-confirmed checkpoints only; unsaved changes can be lost on closure. No external actions or customer matching. Follow-ups save explicit owner evidence; no reminders or automatic task discovery are connected. One saved email/manual interaction may be interrupted by a call; resume checks stored follow-ups before closing the call. Existing tab-local drafts are not imported. Production Board attention remains read-only.';
  $('queueTitle').textContent='Stored interactions';$('captureHelp').textContent='Save before switching cases. Interrupt a saved email/manual case; save promised follow-ups before resuming. Stored follow-up status changes require owner evidence. Snooze records a due time only, with no reminder. Nested calls and automatic NEXT are not enabled.';
  $('status').textContent='No outbound action is connected.';controls();void load();
  return Object.freeze({load,save,edit,fresh,view:()=>checkpoint?.view(),lock});
}
