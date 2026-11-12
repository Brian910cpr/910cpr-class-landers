import test from 'node:test';
import {setupFullOfferLease,proveLeaseBasics} from './native-full-offer-lease-proof.mjs';
for(const full of [false,true])test(`${full?'Heartsaver-extended':'BLS-only'} materializer enforces original lease without changing paid recovery`,async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{const fixture=await setupFullOfferLease(db,{full});await proveLeaseBasics(db,fixture);}finally{await db.close();}
});
