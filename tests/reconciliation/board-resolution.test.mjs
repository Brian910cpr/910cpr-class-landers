import {PGlite} from '@electric-sql/pglite';
import fs from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';

test('resolution transaction: replay, stale writers, reopen, rollback and privileges', async () => {
  const db = new PGlite();
  try {
    await db.exec(`create role anon; create role authenticated; create role service_role bypassrls;`);
    await db.exec(fs.readFileSync(new URL('../../supabase/migrations/20260812161043_production_board.sql', import.meta.url),'utf8'));
    await db.exec(fs.readFileSync(new URL('../../data/audit/issue380_resolution_transaction_draft.sql', import.meta.url),'utf8'));
    const id = (await db.query('select id from production_board_cards limit 1')).rows[0].id;
    const request = '00000000-0000-4000-8000-000000000001';
    const args = [id,1,request,'owner-fixture','handled_manually','Fixed externally','fixture','2026-10-12T12:00:00Z'];
    const call = async (a=args) => (await db.query('select production_board_resolve($1,$2,$3,$4,$5,$6,$7,$8) result',a)).rows[0].result;
    await db.exec('set role service_role');
    assert.deepEqual(await call(),{replayed:false,version:2,state:'handled_manually'});
    assert.equal((await call()).replayed,true);
    await assert.rejects(call([...args.slice(0,5),'different',...args.slice(6)]),/idempotency_conflict/);
    await assert.rejects(call([id,1,'00000000-0000-4000-8000-000000000002',...args.slice(3)]),/stale_card_version/);
    assert.equal((await db.query('select count(*)::int n from production_board_resolution_events')).rows[0].n,1);
    // Ordinary legacy updates must invalidate worker/editor versions too.
    await db.query('update production_board_cards set summary=$1 where id=$2',['changed',id]);
    const reopen=[id,3,'00000000-0000-4000-8000-000000000003','owner-fixture','unresolved','New regression','fixture',args[7]];
    assert.equal((await call(reopen)).version,4);
    assert.equal((await call()).version,2,'replay is original result, never current execution permission');
    await assert.rejects(db.exec('delete from production_board_resolution_events'),/permission denied/);
    await assert.rejects(db.exec("update production_board_resolution_events set actor='altered'"),/permission denied/);
    await db.exec('reset role');
    // Force audit failure after UPDATE to prove whole transaction rolls back.
    await db.exec(`create function fail_resolution_audit() returns trigger language plpgsql as $$ begin
      if new.action='resolution_transition' then raise exception 'fixture_audit_failure'; end if; return new; end $$;
      create trigger fail_audit before insert on production_board_activity for each row execute function fail_resolution_audit();`);
    await db.exec('set role service_role');
    await assert.rejects(call([id,4,'00000000-0000-4000-8000-000000000004',...args.slice(3)]),/fixture_audit_failure/);
    assert.deepEqual((await db.query('select row_version::int v,resolution_state s from production_board_cards where id=$1',[id])).rows[0],{v:4,s:'unresolved'});
    assert.equal((await db.query('select count(*)::int n from production_board_resolution_events')).rows[0].n,2);
    for (const role of ['anon','authenticated']) {
      await db.exec(`reset role; set role ${role}`);
      await assert.rejects(call(),/permission denied/);
      await assert.rejects(db.query('select * from production_board_resolution_events'),/permission denied/);
    }
  } finally { await db.close(); }
});
