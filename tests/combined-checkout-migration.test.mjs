import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {prepareCombinedCheckout,proveCombinedCheckout} from './combined-checkout-proof.mjs';
const migration=readFileSync(new URL('../supabase/migrations/20261113133919_native_combined_checkout_guarded.sql',import.meta.url),'utf8');
const reviewed=readFileSync(new URL('../supabase/reviewed/native-combined-checkout.sql',import.meta.url),'utf8').replaceAll('\r\n','\n');
const dbNew=async()=>{const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');return new PGlite();};
const rejected=async(db,pattern)=>{await assert.rejects(db.exec(migration),pattern);await db.exec('rollback');};
test('tracked wrapper embeds reviewed runtime unchanged after additive preflight',()=>{
 assert.equal(migration.slice(migration.indexOf('create table public.native_checkout_basket_course_policy')),reviewed.slice(reviewed.indexOf('create table public.native_checkout_basket_course_policy')));
 assert.match(migration,/set local lock_timeout='2s'/);assert.match(migration,/set local statement_timeout='30s'/);
});
test('missing prerequisite rejects before creating ledger or modifying existing state',async()=>{
 const db=await dbNew();try{
  await db.exec('create table public.existing_fixture(id integer primary key);insert into public.existing_fixture values(42);');
  await rejected(db,/basket_install_missing_prerequisite/);
  assert.deepEqual((await db.query('select * from existing_fixture')).rows,[{id:42}]);
  assert.equal((await db.query("select to_regclass('public.native_checkout_baskets') as relation")).rows[0].relation,null);
 }finally{await db.close();}
});
test('partial install is never overwritten and membership drift fails closed',async()=>{
 const db=await dbNew();try{
  await prepareCombinedCheckout(db);
  await db.exec(`create table native_checkout_baskets(sentinel text);insert into native_checkout_baskets values('keep');`);
  await rejected(db,/basket_install_existing_object/);
  assert.equal((await db.query('select sentinel from native_checkout_baskets')).rows[0].sentinel,'keep');
  await db.exec('drop table native_checkout_baskets;'); // Only this isolated fixture's sentinel.
  await db.exec("create or replace function public.native_checkout_basket_contains_order(p_order_id uuid) returns boolean language sql as 'select false';");
  await rejected(db,/basket_install_membership_source_drift/);
  assert.equal((await db.query("select to_regclass('public.native_checkout_basket_items') as relation")).rows[0].relation,null);
 }finally{await db.close();}
});
test('reapplication preserves completed synthetic orders, seats, inventory and policy',async()=>{
 const db=await dbNew();try{
  await proveCombinedCheckout(db);
  const tables=['landerware_public_orders','landerware_public_order_students','registrations','class_sessions','product_inventory_units','native_checkout_baskets','native_checkout_basket_items','native_checkout_basket_course_policy'];
  const snapshot=async()=>Object.fromEntries(await Promise.all(tables.map(async name=>[name,(await db.query(`select to_jsonb(t) as value from public.${name} t order by to_jsonb(t)::text`)).rows])));
  const before=await snapshot();
  await rejected(db,/basket_install_existing_object/);
  assert.deepEqual(await snapshot(),before);
 }finally{await db.close();}
});

test('late finalizer source drift rolls back every new table and preserves installed functions',async()=>{
 const db=await dbNew();try{
  await prepareCombinedCheckout(db);
  const source=(await db.query("select pg_get_functiondef('public.native_checkout_finalize_order(uuid,text,jsonb)'::regprocedure) as source")).rows[0].source;
  const changed=source.replaceAll('payment_evidence_mismatch','fixture_changed_guard');
  assert.notEqual(changed,source);await db.exec(changed);
  await rejected(db,/basket_finalizer_source_drift/);
  assert.equal((await db.query("select to_regclass('public.native_checkout_baskets') as relation")).rows[0].relation,null);
  assert.equal((await db.query("select pg_get_functiondef('public.native_checkout_finalize_order(uuid,text,jsonb)'::regprocedure) as source")).rows[0].source,changed);
 }finally{await db.close();}
});
