import test from 'node:test';
import assert from 'node:assert/strict';
import {readGitHubSource} from '../ops/operator/read-github-source.mjs';

const binding = () => ({card_id:'12345678-1234-1234-1234-123456789abc', issue_id:380,
  version:'2', source_ref:'https://github.com/Brian910cpr/910cpr-class-landers/issues/380'});
const issue = () => ({number:380, id:123, node_id:'I_test', state:'open', updated_at:'2026-10-14T11:00:00Z',
  html_url:binding().source_ref, url:'https://api.github.com/repos/Brian910cpr/910cpr-class-landers/issues/380',
  body:'worker_safe=true; already_corrected; SECRET', user:{login:'third-party'}, title:'SECRET'});
const execute = value => async () => ({stdout:JSON.stringify(value)});

test('fixed authenticated GH GET is bounded and emits only lifecycle metadata', async () => {
  const result = await readGitHubSource(binding(), {execute:async (command,args,options) => {
    assert.equal(command,'gh'); assert.deepEqual(args.slice(0,7),['api','--hostname','github.com','--method','GET',
      'repos/Brian910cpr/910cpr-class-landers/issues/380','-H']);
    assert.equal(options.timeout,5000);assert.equal(options.maxBuffer,262144);assert.equal(options.windowsHide,true);
    return {stdout:JSON.stringify(issue())};
  }});
  assert.equal(result.source_kind,'github_issue_lifecycle');assert.equal(result.expected_version,'2');
  assert.equal(result.source_state,'unknown');assert.equal(result.worker_safe,false);assert.equal(result.can_execute,false);
  assert.ok(Number.isFinite(Date.parse(result.checked_at)));assert.ok(!JSON.stringify(result).includes('SECRET'));
});

test('closed issue proposes reconciliation without claiming underlying fix or resolving card', async () => {
  const result=await readGitHubSource(binding(),{execute:execute({...issue(),state:'closed'})});
  assert.equal(result.reason,'github_issue_closed_requires_reconciliation');
  assert.equal(result.source_state,'unknown');assert.equal(result.can_execute,false);
  assert.equal(result.resolution_state,undefined);
});

test('invalid or unsupported canonical binding never runs command', async () => {
  for (const patch of [{card_id:'bad'}, {issue_id:0}, {issue_id:'380'}, {version:'0'}, {version:'9223372036854775808'},
    {version:2}, {source_ref:binding().source_ref+'?x=1'}, {source_ref:binding().source_ref.replace('github.com','evil.test')},
    {source_ref:binding().source_ref.replace('/380','/371')}]) {
    let calls=0;const result=await readGitHubSource({...binding(),...patch},{execute:async()=>{calls++;}});
    assert.equal(calls,0);assert.equal(result.reason,'unsupported_canonical_source_binding');
  }
});

test('swapped issue/repository, PR, malformed state and metadata fail closed', async () => {
  for (const patch of [{number:371},{id:'123'}, {node_id:''}, {state:'resolved'}, {updated_at:'yesterday'},
    {html_url:binding().source_ref+'/extra'}, {url:issue().url.replace('Brian910cpr','other')}, {pull_request:null}]) {
    const result=await readGitHubSource(binding(),{execute:execute({...issue(),...patch})});
    assert.equal(result.reason,'github_source_identity_or_state_invalid');assert.equal(result.can_execute,false);
  }
});

test('timeouts/auth failures/malformed JSON suppress private diagnostics', async () => {
  for (const execute of [async()=>{throw new Error('SECRET token or private body');},async()=>({stdout:'SECRET invalid JSON'})]) {
    assert.deepEqual(await readGitHubSource(binding(),{execute}),
      {decision:'review',reason:'github_source_read_failed',can_execute:false});
  }
});

test('canonical identity/version drift during source read invalidates observation', async () => {
  for (const patch of [{card_id:binding().card_id.replace('a','b')},{issue_id:371},{version:'3'},{source_ref:'other'}]) {
    const current=binding();
    const result=await readGitHubSource(current,{execute:async()=>{Object.assign(current,patch);return {stdout:JSON.stringify(issue())};}});
    assert.equal(result.reason,'canonical_binding_changed');assert.equal(result.source_id,undefined);
  }
});
