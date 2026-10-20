// Never persist provider messages, recipient addresses, bodies, credentials or arbitrary error text.
const providerNames=new Set(['validation_error','missing_api_key','restricted_api_key','suspended_api_key','invalid_permission','invalid_idempotency_key','concurrent_idempotent_requests','invalid_idempotent_request','missing_required_field','missing_required_parameter','invalid_parameter','daily_quota_exceeded','monthly_quota_exceeded','rate_limit_exceeded','application_error','service_unavailable']);
export function providerFailure(status,result){
 const name=providerNames.has(result?.name)?result.name:'unclassified';
 const message=String(result?.message||'').toLowerCase();
 const reason=status===403&&name==='validation_error'
  ? /only send testing emails|testing emails to your own/.test(message)?'test_sender_only'
    : /domain.*not verified|verify.*domain/.test(message)?'sender_domain_unverified'
    : /permission|not authorized/.test(message)?'sender_permission_denied':''
  : '';
 return Object.assign(new Error('provider_rejected'),{deliveryCode:`provider_http_${status}:${name}${reason?':'+reason:''}`});
}
export function deliveryFailure(stage,error){
 if(stage==='provider_response'&&typeof error?.deliveryCode==='string'&&/^provider_http_\d{3}:[a-z_]+(?::(?:test_sender_only|sender_domain_unverified|sender_permission_denied))?$/.test(error.deliveryCode))return error.deliveryCode;
 const kind=['TimeoutError','AbortError'].includes(error?.name)?'timeout':'failed';
 return `${stage}_${kind}`;
}
