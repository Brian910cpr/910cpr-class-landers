(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.SkillsReservationClient=api;})(globalThis,function(){
  function reservationState(body,httpOK){
    return httpOK&&body?.ok===true&&body.status==='reserved'&&body.registrationId&&body.sessionId
      ? {state:'reserved',message:body.paymentStatus==='paid'?'Your skills date is reserved.':'Your skills date is reserved. Payment is pending.'}
      : {state:'unconfirmed',message:'Your date has not been reserved. Please choose another available time or retry.'};
  }
  return {reservationState};
});
