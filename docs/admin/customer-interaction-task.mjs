// Task write coordinator used by default-off Studio follow-up capture.
// Freeze the submitted draft until confirmation; never infer external completion.
export function createFollowUpTaskWrite(client,input){
  const snapshot=structuredClone(input),write=client.prepare('save_task',snapshot);
  let state='unsaved',error=null,flight=null;
  const view=()=>({input:structuredClone(snapshot),requestId:write.requestId,state,error:error?.message??null});
  async function send(){
    if(state==='conflict')throw error;
    if(flight)return structuredClone(await flight);
    state='saving';error=null;
    flight=(async()=>{
      try{const receipt=(await write.send()).task;state='saved';return structuredClone(receipt)}
      catch(e){error=e;state=e.reconcile||(e.status>=400&&e.status<500)?'conflict':'error';throw e}
    })();
    try{return structuredClone(await flight)}finally{flight=null}
  }
  // NEXT may consult this only after the interaction checkpoint is confirmed too.
  // A task receipt confirms bookkeeping, never completion of a Board item/action.
  return Object.freeze({view,send,canLeave:()=>state==='saved'});
}
// Build a status-only mutation from a fetched, versioned task. Never let a UI
// selection replace linkage, source evidence, or concurrency version.
export function createFollowUpTaskDisposition(client,record,{status,evidence,dueAt}={}){
  if(!record||!Number.isInteger(record.version)||record.version<1||
    !['proposed','pending','snoozed','complete'].includes(record.status)||
    !['id','case_id','interaction_id','source_key','title'].every(key=>typeof record[key]==='string'&&record[key].trim())||
    !record.provenance||typeof record.provenance.evidence!=='string'||!record.provenance.evidence.trim())
    throw Error('Load a versioned stored follow-up before changing status.');
  if(!['pending','snoozed','complete'].includes(status)||status===record.status)
    throw Error('Choose a different supported follow-up status.');
  if(typeof evidence!=='string'||!evidence.trim())
    throw Error('Explicit owner disposition evidence is required.');
  if(status==='snoozed'&&(typeof dueAt!=='string'||!Number.isFinite(Date.parse(dueAt))))
    throw Error('Snooze requires an explicit valid due time; no reminder is scheduled.');
  const input={id:record.id,case_id:record.case_id,interaction_id:record.interaction_id,
    source_key:record.source_key,title:record.title,provenance:structuredClone(record.provenance),
    expected_version:record.version,status,due_at:status==='snoozed'?dueAt:(record.due_at??null),
    disposition_evidence:evidence.trim()};
  if(status==='complete')input.completion_evidence=evidence.trim();
  return createFollowUpTaskWrite(client,input);
}
