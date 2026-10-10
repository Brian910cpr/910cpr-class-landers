import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,writeFileSync,readFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {spawnSync} from 'node:child_process';
const script=resolve('ops/scripts/Invoke-CodexWake.ps1'),repo=process.cwd();
const q=s=>"'"+s.replaceAll("'","''")+"'";
function run(options='',state={},hold=false,fail=false){
 const dir=mkdtempSync(join(tmpdir(),'codex-wake-test-'));
 writeFileSync(join(dir,'state.json'),JSON.stringify(state));if(hold)writeFileSync(join(dir,'manual-hold.json'),'{}');
 const ps=`function gh { if($args[0] -eq 'api'){ '{"number":371,"title":"[CODEX] P1 CRM","url":"fixture","updatedAt":"2026-10-10T16:00:00Z","author":"Brian910cpr"}'; '{"number":999,"title":"[CODEX] P0 untrusted","url":"fixture","updatedAt":"2026-10-10T16:00:00Z","author":"outsider"}' } else { '2026-10-10T16:01:00Z' }; $global:LASTEXITCODE=0 }; function codex.exe { $a=@($args); $o=[Array]::IndexOf($a,'-o'); if(${fail?'$true':'$false'}){ $global:LASTEXITCODE=1; return }; Set-Content -LiteralPath $a[$o+1] -Value 'bounded test final'; '{"type":"thread.started","thread_id":"fixture-session"}'; $global:LASTEXITCODE=0 }; & ${q(script)} -RepoPath ${q(repo)} -StateDirectory ${q(dir)} ${options}`;
 const result=spawnSync('pwsh',['-NoProfile','-Command',ps],{encoding:'utf8'});
 const output=JSON.parse(readFileSync(join(dir,'state.json'),'utf8').replace(/^\uFEFF/,''));rmSync(dir,{recursive:true,force:true});return {result,output};
}
test('queue scan filters untrusted authors and preserves all prior assignments',()=>{const {result,output}=run('-CheckOnly',{completed_issue_updates:{174:'2026-09-10T00:00:00Z'},current_task:214});assert.equal(result.status,0,result.stderr);assert.equal(output.queue_count,1);assert.equal(output.current_task,214);assert.equal(output.completed_issue_updates['174'],'2026-09-10T00:00:00Z')});
test('manual owner stream hold prevents automatic concurrent implementation',()=>{const {result,output}=run('',{},true);assert.equal(result.status,0);assert.equal(output.blocked_reason,'manual_workstream_hold')});
test('bounded proof records an execution session without completing the issue',()=>{const {result,output}=run('-IssueNumber 371 -ProofOnly',{completed_issue_updates:{174:'2026-09-10T00:00:00Z'}});assert.equal(result.status,0,result.stderr);assert.equal(output.last_session_id,'fixture-session');assert.equal(output.last_launch_status,'proof_completed');assert.equal(output.completed_issue_updates['371'],undefined)});
test('failed launch clears the lease and backs off without marking task complete',()=>{const {result,output}=run('-IssueNumber 371 -ProofOnly',{},false,true);assert.equal(result.status,1);assert.equal(output.current_task,null);assert.ok(Date.parse(output.retry_after)>Date.now());assert.equal(output.last_launch_status,'failed')});

