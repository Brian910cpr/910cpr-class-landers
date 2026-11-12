import {dispatchNativeLearnerCodes} from './native-learner-code-consumer.mjs';
import {sendNativeLearnerCode,nativeMailConfigured} from './native-resend-adapter.mjs';

// This service never proves delivery or enables policy. The database owns both.
export function nativeLearnerCodeService({rpc,env,request,report=()=>{}}) {
  const mailOptions=()=>({apiKey:env('RESEND_API_KEY'),
    from:env('RESEND_FROM_EMAIL')||env('REQUIREMENT_FROM_EMAIL')||'910CPR <brian@910cpr.com>',replyTo:'brian@910cpr.com',request});
  const configured=()=>nativeMailConfigured(mailOptions());
  const health=()=>rpc('native_learner_code_health',{});
  const readiness=()=>rpc('native_learner_code_runtime_readiness',{});
  async function deliver(orderId=null,{limit=10}={}) {
    const config=configured();
    const empty={configured:config,claimed:0,accepted:0,rejected:0,ambiguous:0,blocked:0,actualDeliveryConfirmed:false};
    // A failed poll write stops before claiming or preparing any code.
    try {await rpc('native_learner_code_runtime_tick',{p_phase:'poll',p_configured:config,p_fault:!config});}
    catch {return {...empty,stopped:'code_runtime_unknown'};}
    if(!config)return {...empty,stopped:'mail_unconfigured'};
    const result=await dispatchNativeLearnerCodes({orderId,limit,
      claim:args=>rpc('native_claim_learner_code',args),
      prepare:args=>rpc('native_prepare_learner_code',args),
      settle:args=>rpc('native_settle_learner_code',args),
      send:data=>sendNativeLearnerCode(data,mailOptions())});
    if(result.pendingSettlement){
      const outcome=result.pendingSettlement;let settled;
      try {settled=await rpc('native_settle_learner_code',outcome);} catch { /* Never resend the email. */ }
      if(settled?.settled===true || settled?.replay===true){
        result[outcome.p_outcome]++;
        result.stopped=outcome.p_outcome==='ambiguous'?'provider_ambiguous':null;
        result.continuationRequired=true;
      } else {
        try {report({event:'native_code_settlement_unknown',...outcome});} catch { /* Preserve sanitized result. */ }
      }
      delete result.pendingSettlement;
    }
    const fault=Boolean(result.stopped || result.ambiguous || result.rejected);
    // Disabled lanes never acquire completion freshness. Faults record failure
    // without claiming that the consumer finished a trustworthy cycle.
    try {
      if(!result.disabled)await rpc('native_learner_code_runtime_tick',{
        p_phase:fault?'poll':'completed',p_configured:config,p_fault:fault});
    } catch {result.stopped='code_runtime_unknown';}
    return {configured:config,...result};
  }
  return {configured,deliver,health,readiness};
}
