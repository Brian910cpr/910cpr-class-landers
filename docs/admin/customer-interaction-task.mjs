// Prepared task disposition coordinator. Unloaded until Studio task integration.
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
