"""Exercise the workflow's actual PowerShell renewal gate against local feeds only."""
import datetime,json,re,shutil,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/'.github/workflows/refresh-public-site.yml'
NOW=datetime.datetime(2026,10,2,10,43,tzinfo=datetime.timezone.utc)
class PublicationRenewalTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.source=WORKFLOW.read_text();cls.shell=shutil.which('pwsh')
  if not cls.shell:raise unittest.SkipTest('PowerShell Core required, as in production workflow')
  start=cls.source.index('          $renewBefore =');end=cls.source.index('\n\n      - name: Upload canonical',start)
  cls.gate='\n'.join(line[10:] for line in cls.source[start:end].splitlines())
  cls.gate=cls.gate.replace('[DateTimeOffset]::UtcNow',"[DateTimeOffset]::Parse('"+NOW.isoformat()+"')")
 def evaluate(self,minutes=90,current='same',previous='same',bad=None,missing=None,root=None):
  def run(directory):
   folder=directory/'docs/data/block-selector-availability';folder.mkdir(parents=True,exist_ok=True)
   for key in ['bls','heartsaver','acls','pals']:
    p=folder/(key+'.json')
    if key==missing:
     if p.exists():p.unlink()
     continue
    p.write_text(json.dumps({'validUntil':bad if key=='bls' and bad is not None else (NOW+datetime.timedelta(minutes=minutes)).isoformat()}))
   before={p.name:p.read_bytes() for p in folder.glob('*.json')};output=directory/'output.txt';output.write_text('')
   script="$currentHash='"+current+"';$previousHash='"+previous+"';$env:GITHUB_OUTPUT='"+str(output).replace("'","''")+"'\n"+self.gate
   result=subprocess.run([self.shell,'-NoProfile','-NonInteractive','-Command',script],cwd=directory,capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(before,{p.name:p.read_bytes() for p in folder.glob('*.json')},'renewal gate must not extend/mutate published leases')
   return dict(line.split('=',1) for line in output.read_text(encoding='utf-8-sig').splitlines())['changed']=='true'
  if root:return run(root)
  with tempfile.TemporaryDirectory() as d:return run(Path(d))
 def test_due_before_next_cycle_and_processing(self):self.assertTrue(self.evaluate(minutes=37))
 def test_exact_margin_boundary(self):self.assertTrue(self.evaluate(minutes=45))
 def test_just_outside_margin_unchanged(self):self.assertFalse(self.evaluate(minutes=45.1))
 def test_already_expired(self):self.assertTrue(self.evaluate(minutes=-1))
 def test_no_change_and_not_due(self):self.assertFalse(self.evaluate())
 def test_inventory_change_still_rebuilds(self):self.assertTrue(self.evaluate(current='new'))
 def test_missing_or_invalid_lease_renews(self):
  self.assertTrue(self.evaluate(missing='pals'));self.assertTrue(self.evaluate(bad='not-a-date'))
 def test_queued_contender_rechecks_new_publication(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.assertTrue(self.evaluate(minutes=20,root=root));self.assertFalse(self.evaluate(minutes=90,root=root))
 def test_concurrent_publication_guards_preserved(self):
  self.assertRegex(self.source,r'concurrency:\s*\n\s*group: schedule-publish-main\s*\n\s*cancel-in-progress: false')
  self.assertIn('ref: main',self.source);self.assertIn('if ($remoteMain -ne $baseCommit)',self.source)
  self.assertIn('Refusing to replay generated output onto a different source tree',self.source)
 def test_cadence_and_budget_cover_observed_run(self):
  self.assertIn('cron: "13,43 * * * *"',self.source)
  margin=int(re.search(r'\$renewBefore = .*AddMinutes\((\d+)\)',self.source).group(1))
  self.assertGreaterEqual(margin,30+7+8)
if __name__=='__main__':unittest.main()
