// One immutable two-record transaction. The UI must freeze editing/navigation
// until confirmation; a failed switch never becomes two independent saves.
export function createInteractionSwitch(client,operation,input){
  if(!['interrupt','resume'].includes(operation))throw Error('Invalid switch operation.');
  const snapshot=structuredClone(input),write=client.prepare(operation,snapshot);
  let state='unsaved',error=null,receipt=null,flight=null;
  const view=()=>({operation,input:structuredClone(snapshot),requestId:write.requestId,state,error:error?.message??null,receipt:receipt&&structuredClone(receipt)});
  async function send(){
    if(state==='conflict')throw error;
    if(receipt)return structuredClone(receipt);
    if(flight)return flight;
    state='saving';error=null;
    flight=(async()=>{
      try{receipt=(await write.send()).switch;state='saved';return structuredClone(receipt)}
      catch(e){error=e;state=e.reconcile||[400,401,403,409].includes(e.status)?'conflict':'error';throw e}
    })();
    try{return await flight}finally{flight=null}
  }
  return Object.freeze({view,send});
}

// Recovery reads immutable links across all pages, never guesses from names or
// a latest-100 list. Current versions are fetched separately before resumption.
export async function findInteractionInterruption(client,activeId){
  let cursor=null;
  const seen=new Set();
  do{
    const page=await client.list({collection:'interruptions',...(cursor??{})});
    const event=page.items.find(e=>e.input?.operation==='interrupt'&&e.input?.active?.id===activeId);
    if(event)return event;
    cursor=page.next_cursor;
    if(cursor){const key=JSON.stringify(cursor);if(seen.has(key))throw Error('Repeated interruption cursor; recovery is incomplete.');seen.add(key)}
  }while(cursor);
  return null;
}
