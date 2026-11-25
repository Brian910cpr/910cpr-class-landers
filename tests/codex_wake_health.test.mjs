import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,writeFileSync,readFileSync,existsSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {spawnSync} from 'node:child_process';
const q=s=>"'"+s.replaceAll("'","''")+"'";
function run(fail=false){
 const dir=mkdtempSync(join(tmpdir(),'wake-health-'));
 try {
  writeFileSync(join(dir,'health-publish.json'),JSON.stringify({comment_id:123}));
  writeFileSync(join(dir,'state.json'),JSON.stringify({worker_state:'held',last_check_at:'2026-10-10T20:00:00Z',blocked_reason:'SECRET',repo_path:'PRIVATE',last_session_id:'session'}));
  writeFileSync(join(dir,'manual-hold.json'),'{}');
  const capture=join(dir,'capture.json');
  const command=`function gh { process { $_ | Set-Content -LiteralPath ${q(capture)}; $global:LASTEXITCODE=${fail?1:0} } }; & ${q(resolve('ops/scripts/Publish-CodexWakeHealth.ps1'))} -StateDirectory ${q(dir)} -LoopProcessId $PID -WorkerProcessId $PID`;
  const result=spawnSync('pwsh',['-NoProfile','-Command',command],{encoding:'utf8'});
  return {result,body:JSON.parse(readFileSync(capture,'utf8').replace(/^\uFEFF/,'' )).body,published:existsSync(join(dir,'published-health.json')),logged:existsSync(join(dir,'loop.log'))};
 } finally {rmSync(dir,{recursive:true,force:true});}
}
test('publishes live loop/session signal and hold without private state',()=>{
 const r=run(); assert.equal(r.result.status,0,r.result.stderr); assert.ok(r.published);
 assert.match(r.body,/910CPR-CODEX-WAKE-HEALTH-V1/); assert.match(r.body,/"execution_process_alive": true/); assert.match(r.body,/"manual_hold": true/);
 assert.doesNotMatch(r.body,/SECRET|PRIVATE/); assert.match(r.body,/"last_session_id": "session"/);
});
test('publication failure keeps intake alive and does not save false publication success',()=>{
 const r=run(true); assert.equal(r.result.status,0,r.result.stderr); assert.equal(r.published,false); assert.ok(r.logged);
});
