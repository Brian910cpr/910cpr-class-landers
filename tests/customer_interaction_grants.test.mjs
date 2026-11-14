import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const {PGlite}=await import(process.env.PGLITE_MODULE||'@electric-sql/pglite');

test('production-like default grants cannot make CRM audit mutable or expose owner records',async()=>{
 const db=new PGlite();
 try {
  await db.exec(`create role anon; create role authenticated; create role service_role bypassrls;
   create table public.landerware_people(id uuid primary key);
   alter default privileges in schema public grant all on tables to anon,authenticated,service_role;
   alter default privileges in schema public grant execute on functions to anon,authenticated,service_role;`);
  for(const name of ['20261010210607_customer_interaction_storage.sql','20261010211804_customer_interaction_interruptions.sql','20261010212019_customer_follow_up_task_mutations.sql'])
   await db.exec(readFileSync(new URL('../supabase/migrations/'+name,import.meta.url),'utf8'));
  const audit=['customer_interaction_events','customer_interruption_events','customer_task_events'];
  const mutable=['customer_cases','customer_interactions','customer_follow_up_tasks'];
  for(const table of [...audit,...mutable]) {
   assert.equal((await db.query('select relrowsecurity from pg_class where oid=$1::regclass',['public.'+table])).rows[0].relrowsecurity,true);
   for(const role of ['anon','authenticated'])
    for(const privilege of ['SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER'])
     assert.equal((await db.query('select has_table_privilege($1,$2,$3) as allowed',[role,'public.'+table,privilege])).rows[0].allowed,false,`${role} ${privilege} ${table}`);
   for(const privilege of ['SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER']) {
    const expected=privilege==='SELECT'||privilege==='INSERT'||(mutable.includes(table)&&privilege==='UPDATE');
    assert.equal((await db.query('select has_table_privilege($1,$2,$3) as allowed',['service_role','public.'+table,privilege])).rows[0].allowed,expected,`service_role ${privilege} ${table}`);
   }
  }
  for(const name of ['save_customer_interaction','switch_customer_interaction','save_customer_follow_up_task']) {
   const signature=`public.${name}(uuid,text,jsonb)`;
   for(const role of ['anon','authenticated','service_role'])
    assert.equal((await db.query("select has_function_privilege($1,$2,'EXECUTE') as allowed",[role,signature])).rows[0].allowed,role==='service_role');
   const row=(await db.query('select prosecdef,proconfig from pg_proc where oid=$1::regprocedure',[signature])).rows[0];
   assert.equal(row.prosecdef,false);assert.deepEqual(row.proconfig,['search_path=""']);
  }
  await db.exec('set role service_role');
  for(const table of audit) {
   await assert.rejects(db.exec(`update public.${table} set actor='overwrite'`),/permission denied/);
   await assert.rejects(db.exec(`delete from public.${table}`),/permission denied/);
   await assert.rejects(db.exec(`truncate public.${table}`),/permission denied/);
  }
 } finally {await db.close();}
});
