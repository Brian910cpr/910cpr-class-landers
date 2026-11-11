#!/usr/bin/env node
// Destructive fixture setup is allowed ONLY in a pre-created, empty localhost
// native_demand_snapshot_test database. No DATABASE_URL, credentials, or hosted
// services are used. Requires Node 20+ and a local PostgreSQL 17 psql/server.
import assert from 'node:assert/strict';
import {assertIsolatedPostgresServerAddress} from './helpers/isolated-postgres-address.mjs';
import { spawn } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { randomUUID } from 'node:crypto';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const database = 'native_demand_snapshot_test';
const port = Number(process.env.NATIVE_SNAPSHOT_TEST_PORT || 5432);
assert(Number.isInteger(port) && port > 0 && port < 65536, 'invalid local port');
const env = { ...process.env };
for (const key of Object.keys(env)) if (/^PG/i.test(key) || /DATABASE_URL/.test(key)) delete env[key];
Object.assign(env, {
  PGHOSTADDR: '127.0.0.1', PGCONNECT_TIMEOUT: '3', PGPASSWORD: '',
  PGPASSFILE: process.platform === 'win32' ? 'NUL' : '/dev/null',
  PGOPTIONS: '-c statement_timeout=20000 -c lock_timeout=15000',
});
const args = ['-X', '-w', '-q', '-t', '-A', '-h', '127.0.0.1', '-p', String(port),
  '-U', 'postgres', '-d', database, '-v', 'ON_ERROR_STOP=1'];

class Connection {
  constructor(label) {
    this.label = label;
    this.buffer = '';
    this.stderr = '';
    this.pending = null;
    this.exited = false;
    this.child = spawn('psql', args, { env, stdio: ['pipe', 'pipe', 'pipe'] });
    this.child.stdout.setEncoding('utf8');
    this.child.stderr.setEncoding('utf8');
    this.child.stderr.on('data', chunk => { this.stderr += chunk; });
    this.child.stdout.on('data', chunk => {
      this.buffer += chunk;
      const p = this.pending;
      if (!p) return;
      const index = this.buffer.indexOf(`${p.token}\n`);
      if (index === -1) return;
      const output = this.buffer.slice(0, index).trim();
      this.buffer = this.buffer.slice(index + p.token.length + 1);
      this.pending = null;
      clearTimeout(p.timer);
      p.resolve(output);
    });
    this.child.on('error', error => { this.exited = true; this.fail(error); });
    this.child.stdin.on('error', error => this.fail(error));
    this.child.on('exit', (code, signal) => {
      this.exited = true;
      this.fail(new Error(`${label}: psql exited (${code ?? signal}): ${this.stderr}`));
    });
  }
  fail(error) {
    if (!this.pending) return;
    const p = this.pending;
    this.pending = null;
    clearTimeout(p.timer);
    p.reject(error);
  }
  query(sql) {
    assert(!this.pending, `${this.label}: concurrent command on one connection`);
    assert(!this.exited, `${this.label}: connection already closed`);
    return new Promise((resolve, reject) => {
      const token = `done_${randomUUID().replaceAll('-', '')}`;
      const timer = setTimeout(() => {
        this.fail(new Error(`${this.label}: command timed out: ${this.stderr}`));
        this.child.kill('SIGTERM');
      }, 25000);
      this.pending = { token, resolve, reject, timer };
      this.child.stdin.write(`${sql}\n\\echo ${token}\n`);
    });
  }
  close() { this.child.stdin.end('\\q\n'); this.child.kill('SIGTERM'); }
}

const reader = new Connection('reader');
const writer = new Connection('writer');
const lockKey = 731128194;
const session = '11111111-1111-4111-8111-111111111111';

async function waitForBarrier(pid, blockerPid) {
  const deadline = Date.now() + 12000;
  do {
    const blocked = await writer.query(`SELECT EXISTS (
      SELECT 1 FROM pg_stat_activity
      WHERE pid = ${pid} AND wait_event_type = 'Lock' AND wait_event = 'advisory'
        AND ${blockerPid} = ANY(pg_blocking_pids(pid))
    );`);
    if (blocked === 't') return;
  } while (Date.now() < deadline);
  throw new Error('reader did not reach deterministic advisory-lock barrier');
}

try {
  const server = JSON.parse(await writer.query(`SELECT json_build_object(
    'database', current_database(), 'version', current_setting('server_version_num')::int,
    'recovery', pg_is_in_recovery(), 'address', host(inet_server_addr()));`));
  assert.equal(server.database, database);
  assert.equal(Math.floor(server.version / 10000), 17, 'requires PostgreSQL 17');
  assert.equal(server.recovery, false);
  await assertIsolatedPostgresServerAddress(server.address,{args,env,port,database});
  const count = await writer.query(`SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname NOT IN ('pg_catalog','information_schema') AND n.nspname NOT LIKE 'pg_toast%';`);
  assert.equal(count, '0', 'database must be NEW and empty; refusing to modify existing data');
  const routines = await writer.query(`SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
    WHERE n.nspname NOT IN ('pg_catalog','information_schema');`);
  assert.equal(routines, '0', 'database must have no existing user routines');
  const fixture = await readFile(resolve(root, 'tests/helpers/native-demand-snapshot-schema.sql'), 'utf8');
  const migration = await readFile(resolve(root, 'supabase/migrations/20261111200810_native_scheduling_seat_snapshot.sql'), 'utf8');
  assert(migration.trim(), 'migration is empty');
  await writer.query(fixture);
  const fingerprintSql = `SELECT coalesce(jsonb_agg(jsonb_build_object('oid',p.oid,'definition',pg_get_functiondef(p.oid)) ORDER BY p.oid)::text,'[]')
    FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public'
    AND p.proname IN ('landerware_public_seat_state','native_session_authority_state');`;
  const fingerprints = await writer.query(fingerprintSql);
  await writer.query(migration);
  assert.equal(await writer.query(fingerprintSql), fingerprints, 'migration changed existing helper definitions');
  // The fixture-specific race cases are below. Never use pg_sleep for ordering.
  assert.notEqual(fingerprints, '[]', 'fixture must include the original mutation readers');
  const metadata = JSON.parse(await writer.query(`SELECT json_build_object(
    'stable', p.provolatile='s', 'invoker', NOT p.prosecdef,
    'service', has_function_privilege('service_role',p.oid,'EXECUTE'),
    'anon', has_function_privilege('anon',p.oid,'EXECUTE'),
    'authenticated', has_function_privilege('authenticated',p.oid,'EXECUTE'),
    'legacyVolatile', (SELECT bool_and(provolatile='v') FROM pg_proc
      WHERE pronamespace='public'::regnamespace AND proname IN ('landerware_public_seat_state','native_session_authority_state')))
    FROM pg_proc p WHERE p.oid='public.native_scheduling_seat_snapshot(uuid)'::regprocedure;`));
  assert.deepEqual(metadata, { stable: true, invoker: true, service: true,
    anon: false, authenticated: false, legacyVolatile: true });
  await writer.query('CREATE SCHEMA snapshot_test; GRANT USAGE ON SCHEMA snapshot_test TO service_role;');
  const actualDefinition = await writer.query("SELECT pg_get_functiondef('public.native_scheduling_seat_snapshot(uuid)'::regprocedure);");
  const legacyDefinition = await writer.query("SELECT pg_get_functiondef('public.landerware_public_seat_state(uuid)'::regprocedure);");
  const marker = '-- snapshot_registration_count_captured';
  assert.equal(actualDefinition.split(marker).length, 2, 'exactly one snapshot barrier marker required');
  const barrier = `\n PERFORM pg_catalog.pg_advisory_lock(${lockKey});\n PERFORM pg_catalog.pg_advisory_unlock(${lockKey});\n`;
  const clones = [
    { name: 'stable_reader', stable: true, definition: actualDefinition.replace(marker, marker + barrier) },
    { name: 'volatile_control', stable: false, definition: actualDefinition.replace(marker, marker + barrier).replace(/\bSTABLE\b/, 'VOLATILE') },
    { name: 'legacy_reader', stable: false, definition: legacyDefinition.replace(
      "select count(*) into v_registered from public.registrations where class_session_id=s.id and status in ('registered','confirmed','completed','active');",
      "select count(*) into v_registered from public.registrations where class_session_id=s.id and status in ('registered','confirmed','completed','active');" + barrier) },
  ];
  for (const clone of clones) {
    assert(clone.definition.includes(barrier), `${clone.name}: missing instrumentation point`);
    const oldName = clone.name === 'legacy_reader' ? 'landerware_public_seat_state' : 'native_scheduling_seat_snapshot';
    const definition = clone.definition.replace(`public.${oldName}(`, `snapshot_test.${clone.name}(`);
    assert.notEqual(definition, clone.definition, 'clone rename failed');
    await writer.query(`${definition};\nREVOKE ALL ON FUNCTION snapshot_test.${clone.name}(uuid) FROM PUBLIC;
      GRANT EXECUTE ON FUNCTION snapshot_test.${clone.name}(uuid) TO service_role;`);
  }
  const readerPid = Number(await reader.query('SELECT pg_backend_pid();'));
  const writerPid = Number(await writer.query('SELECT pg_backend_pid();'));
  assert(Number.isInteger(readerPid) && Number.isInteger(writerPid) && readerPid !== writerPid,
    'must use independent PostgreSQL backend connections');
  await reader.query('SET ROLE service_role; SET default_transaction_isolation = \'read committed\';');
  await writer.query('SET default_transaction_isolation = \'read committed\';');

  const registration = '22222222-2222-4222-8222-222222222222';
  const converted = '33333333-3333-4333-8333-333333333333';
  const order = '44444444-4444-4444-8444-444444444444';
  const authority = '55555555-5555-4555-8555-555555555555';
  const student = '66666666-6666-4666-8666-666666666666';
  const scenarios = [
    { name: 'generated unexpired hold becomes registration', generated: true, reserve: false, paid: false },
    { name: 'adopted protected paid hold becomes registration', generated: false, reserve: false, paid: true },
    { name: 'adopted inherited reserve becomes imported registration', generated: false, reserve: true, paid: false },
  ];
  async function seed(scenario) {
    const external = scenario.generated ? `lw-${session}` : '123456';
    await writer.query(`BEGIN;
      TRUNCATE public.landerware_public_order_students, public.landerware_public_orders,
        public.registrations, public.native_checkout_generated_sessions,
        public.landerware_session_authority_events, public.landerware_public_session_inventory,
        public.class_sessions;
      INSERT INTO public.class_sessions(id,external_class_id,record_scope,registration_backend,
        max_students,source,external_session_evidence,status,registration_status,visibility)
      VALUES ('${session}','${external}','operational','landerware',2,'landerware_event',
        '{"materializedBy":"native_full_course"}','scheduled','open','public');
      INSERT INTO public.registrations(id,class_session_id,status,registration_source)
        VALUES ('${registration}','${session}','registered','native');
      ${scenario.generated ? `INSERT INTO public.native_checkout_generated_sessions(class_session_id,identity_hash,state)
        SELECT id,public.native_checkout_generated_identity(s),'holding' FROM public.class_sessions s WHERE id='${session}';`
        : `INSERT INTO public.landerware_session_authority_events(id,class_session_id,revision,enabled,
          session_identity,capacity_ceiling,anonymous_reserved_seats,unmatched_external_ids)
          SELECT '${authority}',id,1,true,jsonb_build_array(course_id,start_at,end_at,consumption_start_at,
            consumption_end_at,lead_instructor_id,location_id,resource_id,organization_id,external_class_id,record_scope),
            2,0,${scenario.reserve ? "ARRAY['external-seat-1']::text[]" : 'ARRAY[]::text[]'}
          FROM public.class_sessions WHERE id='${session}';`}
      ${scenario.reserve ? '' : `INSERT INTO public.landerware_public_orders(id,class_session_id,status,hold_expires_at,payment_evidence)
        VALUES ('${order}','${session}','checkout_open',now() ${scenario.paid ? '-' : '+'} interval '1 hour',
          '${scenario.paid ? '{"payment_status":"paid","seat_hold_protected":"true"}' : '{}'}');
        INSERT INTO public.landerware_public_order_students(id,order_id) VALUES ('${student}','${order}');`}
      COMMIT;`);
  }
  const occupied = state => state.registered + state.holds + (state.unreconciledReserved || 0);
  const readActual = async () => JSON.parse(await reader.query(`SELECT public.native_scheduling_seat_snapshot('${session}');`));
  let passed = 0;
  for (const scenario of scenarios) {
    for (const clone of clones) {
      await seed(scenario);
      const before = await readActual();
      assert.equal(occupied(before), 2, 'starting occupancy must fill capacity');
      assert.equal(before.remaining, 0);
      await writer.query(`SELECT pg_advisory_lock(${lockKey});`);
      // Attach rejection handling immediately so a failed barrier cannot produce
      // an unhandled rejection while the other connection is being inspected.
      const pending = reader.query(`SELECT snapshot_test.${clone.name}('${session}');`)
        .then(value => ({ value }), error => ({ error }));
      try {
        await waitForBarrier(readerPid, writerPid);
        // Atomic conversion: no committed state ever has fewer than two seats.
        await writer.query(`BEGIN;
          INSERT INTO public.registrations(id,class_session_id,status,registration_source,external_registration_id)
          VALUES ('${converted}','${session}','registered',
            '${scenario.reserve ? 'enrollware' : 'native'}',${scenario.reserve ? "'external-seat-1'" : 'NULL'});
          ${scenario.reserve ? '' : `UPDATE public.landerware_public_orders SET status='completed' WHERE id='${order}';`}
          COMMIT;
          SELECT pg_advisory_unlock(${lockKey});`);
      } catch (error) {
        // Closing the holder releases the lock even after a failed SQL command.
        writer.close();
        await pending;
        throw error;
      }
      const result = await pending;
      if (result.error) throw result.error;
      const during = JSON.parse(result.value);
      assert.equal(occupied(during), clone.stable ? 2 : 1, `${scenario.name}: ${clone.name} occupied`);
      assert.equal(during.remaining, clone.stable ? 0 : 1, `${scenario.name}: ${clone.name} remaining`);
      if (clone.stable) assert.deepEqual(during, before, 'STABLE clone must retain the complete starting snapshot');
      const after = await readActual();
      assert.equal(occupied(after), 2, 'actual uninstrumented function must see complete committed occupancy');
      assert.equal(after.registered, 2);
      assert.equal(after.holds, 0);
      assert.equal(after.unreconciledReserved, 0);
      assert.equal(after.remaining, 0);
      console.log(`PASS ${clone.name}: ${scenario.name}`);
      passed++;
    }
  }
  assert.equal(await writer.query(fingerprintSql), fingerprints, 'test instrumentation modified legacy helpers');
  assert.equal(await writer.query("SELECT pg_get_functiondef('public.native_scheduling_seat_snapshot(uuid)'::regprocedure);"),
    actualDefinition, 'test instrumentation modified the actual reader');
  console.log(`PASS ${passed} deterministic independent-connection races on PostgreSQL ${server.version}; actual and legacy definitions unchanged`);
  console.log('Fixture intentionally retained for inspection. Drop/recreate the local test database before rerunning.');
} finally {
  reader.close();
  writer.close();
}
