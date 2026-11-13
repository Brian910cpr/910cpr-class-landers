// Test-only loopback capture. Never connects to the actual mail provider.
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {nativeConfirmationService} from '../supabase/functions/_shared/native-confirmation-service.mjs';
export async function proveLocalRecoveryCapture({orderId,sql,rpc}){
 assert(/^[0-9a-f-]{36}$/.test(orderId));
 // Seed only a clearly synthetic recovery notice for an existing unpaid fixture.
 sql(`update landerware_checkout_delivery_config set enabled=true,provider='resend',not_before=now()-interval '1 hour',course_ids=array['209806'] where id;
 insert into landerware_messages(template_key,recipient,subject,body_text,delivery_provider,delivery_status,idempotency_key)
 select 'retail-checkout-recovery-v2',payer_email,'Synthetic checkout recovery','Synthetic local capture only','resend','pending','public-order-recovery:'||id::text from landerware_public_orders where id='${orderId}' and status='held' and payer_email='edge-fixture@example.invalid';`);
 const captured=[];let captureError;
 const server=createServer(async(req,res)=>{try{
  assert.equal(req.method,'POST');assert.equal(req.url,'/capture');assert.equal(req.headers.authorization,'Bearer local-capture-only-not-provider-key');
  let body='';for await(const chunk of req){body+=chunk;assert(body.length<262144);}
  const payload=JSON.parse(body);assert.deepEqual(payload.to,['edge-fixture@example.invalid']);assert.match(payload.text,/registration|payment/i);
  assert.match(req.headers['idempotency-key'],/^native-checkout-[0-9a-f-]{36}$/);captured.push(payload);
  res.writeHead(200,{'content-type':'application/json'});res.end(JSON.stringify({id:'local_capture_receipt'}));
 }catch(error){captureError=error;res.writeHead(400);res.end('{}');}});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try{
  const target='http://127.0.0.1:'+server.address().port+'/capture';
  const service=nativeConfirmationService({rpc,env:name=>({RESEND_API_KEY:'local-capture-only-not-provider-key',RESEND_FROM_EMAIL:'Fixture <fixture@example.invalid>'})[name],
   request:async(url,options)=>{assert.equal(url,'https://api.resend.com/emails');return fetch(target,{...options,redirect:'error'});}});
  const first=await service.deliver(orderId,{limit:2});if(captureError)throw captureError;
  assert.equal(first.accepted,1);assert.equal(first.actualDeliveryConfirmed,false);assert.equal(first.stopped,null);assert.equal(captured.length,1);
  const replay=await service.deliver(orderId,{limit:2});assert.equal(replay.accepted,0);assert.equal(captured.length,1,'settled notice must not resend');
  assert.equal(sql(`select count(*) from landerware_checkout_delivery_attempts where provider_id='local_capture_receipt' and state='sent';`),'1');
  assert.equal(sql(`select status from landerware_public_orders where id='${orderId}';`),'held','recovery capture cannot mark payment');
  console.log('PASS: real isolated queue/render/loopback capture/accepted settlement/replay suppression; unpaid order preserved.');
  console.log('NOT PROVEN: external provider delivery or post-payment confirmation; capture is local and synthetic.');
 }finally{await new Promise(resolve=>server.close(resolve));sql("update landerware_checkout_delivery_config set enabled=false where id;");}
}
