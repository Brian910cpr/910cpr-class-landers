import test from 'node:test';
import {proveSkillsSeats} from './native-skills-seated-proof.mjs';
test('native skills second-seat end-to-end local proof',async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{await proveSkillsSeats(db);}finally{await db.close();}
});
