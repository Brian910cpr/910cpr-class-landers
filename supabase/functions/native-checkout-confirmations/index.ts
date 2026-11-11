import {authorizedOwner} from '../_shared/owner-auth.ts';
import {ownerRest} from '../_shared/owner-session.ts';
import {nativeConfirmationService} from '../_shared/native-confirmation-service.mjs';
import {nativeOwnerProof} from '../_shared/native-owner-proof.mjs';
import {nativeConfirmationHandler} from './handler.mjs';
import {nativeScheduledHandler} from './scheduled.mjs';
const service=nativeConfirmationService({
 rpc:(name:string,args:unknown)=>ownerRest(`rpc/${name}`,{method:'POST',body:JSON.stringify(args)}),
 env:(name:string)=>Deno.env.get(name),request:fetch,
 // Private operational receipt only; contains no recipient, body or credentials.
 report:(receipt:unknown)=>console.error(JSON.stringify(receipt))
});
const proof=nativeOwnerProof({
 rpc:(name:string,args:unknown)=>ownerRest(`rpc/${name}`,{method:'POST',body:JSON.stringify(args)}),
 env:(name:string)=>Deno.env.get(name),request:fetch,
 report:(receipt:unknown)=>console.error(JSON.stringify(receipt))
});
const ownerHandler=nativeConfirmationHandler({authorized:authorizedOwner,service,proof,
 schedulerStatus:()=>ownerRest('rpc/native_checkout_scheduler_status',{method:'POST',body:'{}'})
});
const scheduledHandler=nativeScheduledHandler({service,
 rpc:(name:string,args:unknown)=>ownerRest(`rpc/${name}`,{method:'POST',body:JSON.stringify(args)})
});
Deno.serve(req=>new URL(req.url).pathname.endsWith('/scheduled')?scheduledHandler(req):ownerHandler(req));
