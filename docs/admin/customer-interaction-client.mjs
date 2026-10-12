// Prepared transport only: no page imports this module until the UI release gate.
const endpoint='https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/customer-interactions';
const operations=new Set(['save','save_task','interrupt','resume']);
export function createInteractionClient(auth,{enabled=false,uuid=()=>crypto.randomUUID()}={}) {
  function ready(){
    if(!enabled) throw Object.assign(Error('Durable CRM is not enabled.'),{status:503});
    if(!auth?.get()) throw Object.assign(Error('Owner sign-in required.'),{status:401});
  }
  // Prepared writes hold an immutable envelope in memory. Never persist customer
  // notes or the owner session in localStorage/sessionStorage as a recovery queue.
  function prepare(operation,input){
    ready();
    if(!operations.has(operation)) throw Error('Unsupported CRM operation.');
    const stamp=auth.snapshot();
    const body=JSON.stringify({request_id:uuid(),...(operation==='save'?{}:{operation}),input});
    const resultKey=operation==='save'?'interaction':operation==='save_task'?'task':'switch';
    let running=null,receipt=null,terminal=null;
    async function send(){
      ready();
      if(!auth.current(stamp)) throw Object.assign(Error('Sign-in changed; reload stored work and reconcile before saving.'),{status:409,reconcile:true});
      if(terminal) throw terminal;
      if(receipt) return structuredClone(receipt);
      if(running) return structuredClone(await running);
      running=(async()=>{
        const response=await auth.fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body});
        if(!response.ok){
          const error=Object.assign(Error(response.status===409?'Conflict: reload stored work and reconcile.':'Save not confirmed; preserve your draft.'),{status:response.status,reconcile:response.status===409,retryable:response.status>=500});
          if(response.status<500) terminal=error;
          throw error;
        }
        const data=await response.json();
        if(!auth.current(stamp)) throw Object.assign(Error('Sign-in changed; reconcile stored work.'),{status:409,reconcile:true});
        if(!data||!Object.hasOwn(data,resultKey)||!data[resultKey]||typeof data[resultKey]!=='object') throw Error('Invalid save receipt; preserve your draft and retry the same request.');
        receipt=structuredClone(data);
        return structuredClone(receipt);
      })();
      try{return structuredClone(await running)}finally{running=null}
    }
    return Object.freeze({requestId:JSON.parse(body).request_id,send});
  }
  async function list(filters={}){
    ready();
    const stamp=auth.snapshot();
    const query=new URLSearchParams(filters);
    const response=await auth.fetch(endpoint+'?'+query,{method:'GET'});
    if(!response.ok) throw Object.assign(Error('Stored CRM work unavailable; retry loading.'),{status:response.status});
    const data=await response.json();
    if(!auth.current(stamp)) throw Object.assign(Error('Sign-in changed.'),{status:401});
    if(!Array.isArray(data?.items)) throw Error('Invalid CRM collection response.');
    return data;
  }
  return Object.freeze({prepare,list});
}
