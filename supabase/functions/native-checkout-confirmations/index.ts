import {authorizedOwner} from '../_shared/owner-auth.ts';
import {ownerRest} from '../_shared/owner-session.ts';
import {nativeConfirmationService} from '../_shared/native-confirmation-service.mjs';
import {nativeConfirmationHandler} from './handler.mjs';
const service=nativeConfirmationService({
 rpc:(name:string,args:unknown)=>ownerRest(`rpc/${name}`,{method:'POST',body:JSON.stringify(args)}),
 env:(name:string)=>Deno.env.get(name),request:fetch,
 // Private operational receipt only; contains no recipient, body or credentials.
 report:(receipt:unknown)=>console.error(JSON.stringify(receipt))
});
Deno.serve(nativeConfirmationHandler({authorized:authorizedOwner,service}));
