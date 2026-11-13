import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const sql=readFileSync(new URL('../supabase/reviewed/native-checkout-basket-membership.sql',import.meta.url),'utf8');
test('optional basket schema preserves single checkout and blocks child checkout independently of activation',async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{
  await db.exec('create role anon;create role authenticated;create role service_role;');
  await db.exec(sql);await db.exec(sql);
  const id='11111111-1111-4111-8111-111111111111';
  const member=async()=> (await db.query('select native_checkout_basket_contains_order($1) as member',[id])).rows[0].member;
  assert.equal(await member(),false);
  await db.exec('create table native_checkout_basket_items(order_id uuid);');
  assert.equal(await member(),false);
  await db.query('insert into native_checkout_basket_items values($1)',[id]);
  assert.equal(await member(),true);
  for(const role of ['anon','authenticated']) assert.equal((await db.query("select has_function_privilege($1,'native_checkout_basket_contains_order(uuid)','EXECUTE') as allowed",[role])).rows[0].allowed,false);
  assert.equal((await db.query("select has_function_privilege('service_role','native_checkout_basket_contains_order(uuid)','EXECUTE') as allowed")).rows[0].allowed,true);
  await db.exec('alter table native_checkout_basket_items rename column order_id to unexpected;');
  await assert.rejects(member,/order_id/);
  await db.exec("create or replace function native_checkout_basket_contains_order(p_order_id uuid) returns boolean language sql as 'select false';");
  await assert.rejects(db.exec(sql),/basket_membership_source_mismatch/);await db.exec('rollback');
 }finally{await db.close();}
});
