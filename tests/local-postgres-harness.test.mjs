import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {localPsql,assertLocalTargetServer,TARGET_POSTGRES_MAJOR} from './helpers/local-postgres.mjs';
import {preProfileFiles,profileMigration,fullCourseMigration,codeDeliveryMigration,codeEventMigration} from './helpers/native-checkout-migration-plan.mjs';

test('isolated psql plan pins loopback and removes inherited production connection/credential settings without connecting',()=>{
 const original={PATH:'fixture-path',PGHOSTADDR:'production.invalid',PGHOST:'production.invalid',PGSERVICE:'production',PGSERVICEFILE:'/private/service',PGPASSWORD:'never-use-this',PGPASSFILE:'/private/password',PGOPTIONS:'-c search_path=untrusted',PgHoStAdDr:'another.invalid'};
 const p=localPsql('native_checkout_test',original);
 assert.equal(p.env.PGHOSTADDR,'127.0.0.1');assert.equal(p.env.PGPASSWORD,'');assert.notEqual(p.env.PGPASSFILE,original.PGPASSFILE);assert.equal(p.env.PGSERVICE,undefined);assert.equal(p.env.PGSERVICEFILE,undefined);assert.equal(p.env.PgHoStAdDr,undefined);assert.equal(p.env.PGHOST,undefined);
 assert.equal(p.env.PATH,original.PATH);assert.equal(original.PGPASSWORD,'never-use-this');
 assert.ok(p.args.includes('-X'));assert.ok(p.args.includes('-w'));assert.equal(p.args[p.args.indexOf('-h')+1],'127.0.0.1');assert.equal(p.args[p.args.indexOf('-d')+1],'native_checkout_test');assert.match(p.env.PGOPTIONS,/statement_timeout=30000/);
});
test('test database and port guards reject production names, URLs and malformed configuration',()=>{
 for(const db of ['postgres','production','postgresql://remote/db','skills_claim_test;drop','',null])assert.throws(()=>localPsql(db,{}),/isolated_test_database_required/);
 for(const port of ['0','-1','65536','5432 --host=remote','nan'])assert.throws(()=>localPsql('native_checkout_test',{SKILLS_TEST_PORT:port}),/invalid_test_port/);
 assert.equal(localPsql('skills_claim_test_1',{SKILLS_TEST_PORT:'6543'}).args.includes('6543'),true);
});
test('shared fixture plan contains all eight new migrations in order and every referenced source exists',()=>{
 const files=[...preProfileFiles,profileMigration,fullCourseMigration,codeDeliveryMigration,codeEventMigration];for(const p of files)assert.ok(existsSync(new URL('../'+p,import.meta.url)),p);
 const names=files.filter(p=>/migrations\/20261108/.test(p)).map(p=>p.split('/').at(-1));
 assert.deepEqual(names,['20261108142206_skills_checkout_and_optional_certificate.sql','20261108145719_bls_native_checkout_integrity.sql','20261108145720_bls_heartcode_bundle_contract.sql','20261108153759_checkout_confirmation_delivery_gate.sql','20261108175130_native_checkout_course_profiles.sql']);
 assert.equal(files.at(-3),'supabase/migrations/20261109120000_native_full_course_materialization.sql');
 assert.equal(files.at(-2),'supabase/migrations/20261109130000_native_learner_code_delivery.sql');
 assert.equal(files.at(-1),'supabase/migrations/20261109140000_native_code_delivery_events.sql');
 for(const n of ['generic-checkout-concurrency.mjs','skills-native-concurrency.mjs','skills-checkout-concurrency.mjs'])assert.match(readFileSync(new URL(n,import.meta.url),'utf8'),/env:psql.env/);
});

test('workflow separately triggers new private delivery and full-course source/test paths',()=>{
 const y=readFileSync(new URL('../.github/workflows/verify-skills-native-claim.yml',import.meta.url),'utf8');
 for(const p of ['tests/local-postgres-harness.test.mjs','tests/full-course-materialization.test.mjs','tests/learner-code-delivery.test.mjs','worker/learner-code-delivery.mjs','supabase/migrations/*native_full_course*.sql','supabase/migrations/*native_learner_code*.sql'])assert.ok(y.includes("'"+p+"'"),p);
 assert.ok(!y.includes("'tests/local-postgres-harness.test.mjs tests/"));
});

test('target major17 guard accepts observed minor version and rejects mismatched majors, replica and database without connecting',()=>{
 const target={database:'native_checkout_test',version:170006,recovery:false};
 assert.equal(TARGET_POSTGRES_MAJOR,17);assert.deepEqual(assertLocalTargetServer(target,'native_checkout_test'),{major:17,version:170006,database:'native_checkout_test'});
 for(const version of [160014,180000,0,NaN,Infinity,'170006',170006.5])assert.throws(()=>assertLocalTargetServer({...target,version},'native_checkout_test'),/postgresql17_target_required/);
 assert.throws(()=>assertLocalTargetServer({...target,recovery:true},'native_checkout_test'),/isolated_primary_required/);
 assert.throws(()=>assertLocalTargetServer({...target,database:'production'},'native_checkout_test'),/isolated_test_database_mismatch/);
 assert.throws(()=>assertLocalTargetServer({...target,database:'production'},'production'),/isolated_test_database_required/);
 for(const name of ['generic-checkout-concurrency.mjs','skills-native-concurrency.mjs','skills-checkout-concurrency.mjs'])assert.match(readFileSync(new URL(name,import.meta.url),'utf8'),/assertLocalTargetServer\(server,database\)/);
 const workflow=readFileSync(new URL('../.github/workflows/verify-skills-native-claim.yml',import.meta.url),'utf8');assert.match(workflow,/image: postgres:17/);assert.ok(!workflow.includes('image: postgres:16'));
});


test('current race gate includes deployed profile columns and both inactive Heartsaver draft paths without using hosted databases',()=>{
 assert.ok(preProfileFiles.includes('supabase/migrations/20261110195617_native_checkout_profile_columns_only.sql'));
 const race=readFileSync(new URL('generic-checkout-concurrency.mjs',import.meta.url),'utf8');
 assert.ok(race.includes("['209809','351632']"));assert.ok(race.includes('three claims for two session-override seats'));
 const workflow=readFileSync(new URL('../.github/workflows/verify-skills-native-claim.yml',import.meta.url),'utf8');
 assert.ok(workflow.includes('tests/heartsaver-checkout-drafts.test.mjs'));
 assert.ok(workflow.includes("'supabase/migrations/*heartsaver_inactive_checkout_drafts.sql'"));
});
