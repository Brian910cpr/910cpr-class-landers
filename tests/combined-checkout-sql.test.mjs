import test from 'node:test';import {proveCombinedCheckout} from './combined-checkout-proof.mjs';
test('combined checkout allocates real aggregate payment to distinct canonical orders atomically and idempotently',async()=>{const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();try{await proveCombinedCheckout(db);}finally{await db.close();}});
