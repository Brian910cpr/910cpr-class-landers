// Synthetic PostgreSQL-backed adapter for the return tests, never production.
import {createPg} from './native-return-postgres.mjs';
import {fileURLToPath} from 'node:url';
let number=121210;
export class PGlite {
 constructor(){this.ready=createPg(fileURLToPath(new URL('../../',import.meta.url)),'skills_claim_test_'+number++);}
 async exec(...args){return (await this.ready).exec(...args);}
 async query(...args){return (await this.ready).query(...args);}
 async close(){return (await this.ready).close();}
}
