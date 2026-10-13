// Prepared transport only: no page imports this module until the UI release gate.
const endpoint='https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/customer-interactions';
const operations=new Set(['save','save_task','interrupt','resume']);
const canonical=value=>value&&typeof value==='object'?
  (Array.isArray(value)?value.map(canonical):Object.fromEntries(Object.keys(value).sort().map(key=>[key,canonical(value[key])]))):value;
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
    const expected=JSON.parse(body).input;
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
        // Reject malformed save acknowledgments before caching: identical retry
        // must be able to retrieve a corrected server receipt. Use the immutable
        // envelope rather than caller input that may have changed during flight.
        if(operation==='save'&&(data.interaction.id!==expected.id||
          !Number.isInteger(data.interaction.version)||data.interaction.version<=expected.expected_version))
          throw Error('Invalid checkpoint identity/version; preserve draft and retry the same request.');
        if(operation==='save_task'){
          const task=data.task;
          const due=value=>{
            if(value==null)return null;
            if(typeof value!=='string'||!Number.isFinite(Date.parse(value)))return NaN;
            const fraction=value.match(/\.(\d+)(?:Z|[+-]\d{2}:\d{2})$/)?.[1]??'';
            return Date.parse(value)+':'+fraction.padEnd(6,'0').slice(3,6);
          };
          // Task completion/navigation must not trust an unrelated or partial
          // HTTP-200 acknowledgment. Compare immutable linkage/provenance and
          // the exact submitted disposition before caching an idempotent result.
          if(!['id','case_id','interaction_id','source_key','title','status'].every(key=>task[key]===expected[key])||
            !Number.isInteger(task.version)||task.version!==expected.expected_version+1||
            JSON.stringify(canonical(task.provenance))!==JSON.stringify(canonical(expected.provenance))||
            !Object.hasOwn(task,'due_at')||due(task.due_at)!==due(expected.due_at))
            throw Error('Invalid task receipt; retain disposition and retry the same request.');
        }
        if(operation==='interrupt'||operation==='resume'){
          const result=data.switch;
          const matches=(record,input)=>record&&record.id===input.id&&record.case_id===input.case_id&&
            record.status===input.status&&Number.isInteger(record.version)&&record.version===input.expected_version+1&&
            ['kind','source','source_id'].every(key=>record[key]===input[key])&&
            (record.person_id??null)===(input.person_id??null)&&
            JSON.stringify(canonical(record.document))===JSON.stringify(canonical(input.document));
          if(result.request_id!==JSON.parse(body).request_id||result.operation!==operation||
            !matches(result.previous,expected.previous)||!matches(result.active,expected.active))
            throw Error('Invalid atomic switch receipt; retain both drafts and retry the same request.');
        }
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
