"""Real libpq bridge proof; only GitHub is fixture-controlled."""
import json
import os
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest
import uuid
import board_source_binding_reader as reader
import board_resolution_contention as foundation


class CanonicalBridge(reader.SourceBindingReader):
    @classmethod
    def setUpClass(cls):
        # Do not initialize fixtures or misreport missing transport as SQL proof.
        if not shutil.which('psql'):
            raise RuntimeError('BLOCKED: psql executable required on PATH; libpq/server alone is insufficient')
        super().setUpClass()

    def bridge(self, card, mutation=None, user=None):
        row=self.admin.execute('select issue_id from production_board_dispatch_intake where card_id=%s',(card,)).fetchone()
        issue=row[0] if row else 380
        from psycopg.conninfo import conninfo_to_dict
        info=conninfo_to_dict(foundation.DSN)
        foundation.validate_target(info)
        with tempfile.TemporaryDirectory(prefix='issue380-libpq-') as directory:
            service=Path(directory)/'pg_service.conf'
            service.write_text('[issue380_fixture]\n'+''.join(f'{k}={v}\n' for k,v in {
                'host':'127.0.0.1','port':info.get('port','5432'),
                'dbname':info['dbname'],'user':user or self.login,'connect_timeout':'3'}.items()))
            env=dict(os.environ,PGSERVICEFILE=str(service))
            program="""
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {readCanonicalGitHubSource} from './ops/operator/read-canonical-github-source.mjs';
const run=promisify(execFile);let ghCalls=0;
const execute=async(command,args,options)=>{
  if(command!=='gh')return run(command,args,options);
  ghCalls++;process.stdout.write('GITHUB_BOUNDARY\\n');
  await new Promise(resolve=>process.stdin.once('data',resolve));
  return {stdout:JSON.stringify({number:Number(process.argv[2]),id:123,node_id:'I_fixture',state:'closed',
    updated_at:'2026-10-14T11:00:00Z',
    html_url:'https://github.com/Brian910cpr/910cpr-class-landers/issues/'+process.argv[2],
    url:'https://api.github.com/repos/Brian910cpr/910cpr-class-landers/issues/'+process.argv[2],body:'SECRET'})};
};
const result=await readCanonicalGitHubSource(process.argv[1],'issue380_fixture',{execute});
process.stdout.write(JSON.stringify({result,ghCalls})+'\\n');
"""
            proc=subprocess.Popen(['node','--input-type=module','-e',program,str(card),str(issue)],
                cwd=foundation.ROOT,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,text=True)
            try:
                first=proc.stdout.readline().strip()
                if first=='GITHUB_BOUNDARY':
                    if mutation:mutation()
                    proc.stdin.write('continue\n');proc.stdin.flush()
                    first=proc.stdout.readline().strip()
                out,err=proc.communicate(timeout=15)
                self.assertEqual(proc.returncode,0,err)
                self.assertEqual(out,'')
                result=json.loads(first)
                self.assertNotIn('SECRET',first)
                self.assertFalse(result['result']['can_execute'])
                return result
            finally:
                if proc.poll() is None:proc.kill();proc.communicate()

    def bridge_fixture(self):
        # Other inherited tests deliberately insert unsupported bigint identities.
        issue=self.admin.execute('select coalesce(max(issue_id),1000)+1 from production_board_dispatch_intake where issue_id<1000000').fetchone()[0]
        args=self.publication(issue=issue);self.publish(args)
        return args

    def test_real_psql_service_identity_and_read_only_acquisition(self):
        args=self.bridge_fixture()
        before=self.admin.execute('select row_version from production_board_cards where id=%s',args[:1]).fetchone()
        result=self.bridge(args[0])
        self.assertEqual(result['ghCalls'],1)
        self.assertEqual(result['result']['source_kind'],'github_issue_lifecycle')
        self.assertEqual(result['result']['source_state'],'unknown')
        self.assertEqual(self.admin.execute('select row_version from production_board_cards where id=%s',args[:1]).fetchone(),before)

    def test_real_psql_recheck_discards_version_drift(self):
        args=self.bridge_fixture()
        result=self.bridge(args[0],lambda:self.publish((*args[:2],2,uuid.uuid4(),*args[4:])))
        self.assertEqual(result['result']['reason'],'canonical_binding_changed')
        self.assertNotIn('source_id',result['result'])

    def test_real_psql_resolution_before_and_during_acquisition(self):
        for during in (False,True):
            args=self.bridge_fixture()
            resolve=lambda:self.admin.execute(foundation.CALL,(args[0],2,uuid.uuid4(),'owner','handled_manually','external fix','fixture',args[8]))
            if not during:resolve()
            result=self.bridge(args[0],resolve if during else None)
            self.assertEqual(result['result']['reason'],'card_resolved')
            self.assertEqual(result['ghCalls'],int(during))

    def test_real_psql_missing_and_unprivileged_identity_fail_closed(self):
        self.assertEqual(self.bridge(uuid.uuid4())['ghCalls'],0)
        args=self.bridge_fixture()
        result=self.bridge(args[0],user='anon')
        self.assertEqual(result['ghCalls'],0)
        self.assertEqual(result['result']['reason'],'canonical_source_acquisition_failed')


if __name__=='__main__':
    if not foundation.DSN:raise SystemExit('BLOCKED: explicit disposable ISSUE380_TEST_DSN required')
    unittest.main(verbosity=2)

