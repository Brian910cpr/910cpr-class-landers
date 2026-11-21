// Studio checkpoint coordinator; page integration remains default-off.
// Server interaction/version is authoritative. Browser drafts never imply a save.
export function createInteractionCheckpoint(client, initial, {confirmed=false}={}) {
  let draft=structuredClone(initial), revision=0, savedRevision=confirmed?0:-1;
  let pending=null, flight=null, state=confirmed?'saved':'unsaved', failure=null;
  const blocked=()=>Object.assign(Error('Confirm the pending checkpoint before leaving this interaction.'),{reconcile:state==='conflict'});
  function view(){return {draft:structuredClone(draft),state,dirty:revision!==savedRevision,pendingRequestId:pending?.write.requestId??null,error:failure?.message??null};}
  function edit(document){
    draft.document=structuredClone(document);revision++;
    if(!pending){state='unsaved';failure=null;}
    return view();
  }
  async function save(){
    if(flight)return flight;
    if(state==='conflict')throw blocked();
    if(!pending&&revision===savedRevision)return view();
    if(!pending)pending={write:client.prepare('save',draft),revision};
    const checkpoint=pending;
    state='saving';failure=null;
    flight=(async()=>{
      try{
        const receipt=await checkpoint.write.send();
        const record=receipt.interaction;
        if(record.id!==draft.id||!Number.isInteger(record.version)||record.version<=draft.expected_version)
          throw Error('Invalid checkpoint identity/version; preserve draft and retry the same request.');
        // A late receipt updates the base version, never text typed during save.
        draft.expected_version=record.version;
        savedRevision=checkpoint.revision;pending=null;
        state=revision===savedRevision?'saved':'unsaved';
        return view();
      }catch(error){
        failure=error;state=error.reconcile||[400,401,403,409].includes(error.status)?'conflict':'error';
        throw error;
      }
    })();
    try{return await flight}finally{flight=null}
  }
  function load(record){
    // Explicit reload is allowed only after confirmation; never discard a draft.
    if(pending||revision!==savedRevision)throw blocked();
    draft=structuredClone({...record,expected_version:record.version});
    revision=0;savedRevision=0;state='saved';failure=null;
    return view();
  }
  function reconcile(record){
    // Caller must fetch/display current server work and explicitly choose to keep
    // this draft. Do not use this to resolve an uncertain transport failure.
    if(state!=='conflict'||flight||record.id!==draft.id||!Number.isInteger(record.version)||record.version<draft.expected_version)
      throw blocked();
    draft.expected_version=record.version;pending=null;failure=null;
    revision++;state='unsaved';return view();
  }
  function canLeave(){return !pending&&revision===savedRevision&&state==='saved';}
  function disposition(status,evidence){
    if(!canLeave())throw blocked();
    if(!['in_progress','resolved','follow_up_due','awaiting_data','awaiting_approval'].includes(status)||!evidence?.trim())
      throw Error('Choose a disposition and provide original owner evidence.');
    draft.status=status;
    return edit({...draft.document,disposition:{status,evidence:evidence.trim(),source:'owner_studio'}});
  }
  return Object.freeze({view,edit,save,load,reconcile,canLeave,disposition});
}
