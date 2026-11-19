import copy,html,json,re,subprocess,unittest
from pathlib import Path
from scripts import build_bls_block_schedule_pilot as generator
ROOT=Path(__file__).resolve().parents[1]
def base(path):return subprocess.check_output(['git','show','HEAD:'+path],cwd=ROOT).decode('utf8')
def indexed(path):return subprocess.check_output(['git','show',':'+path],cwd=ROOT).decode('utf8')
class AdvancedCopyTests(unittest.TestCase):
 def test_only_advanced_pages_override_request_copy(self):
  config=json.loads((ROOT/'data/config/block_schedule_pages.json').read_text(encoding='utf8'))
  selected={name for name,p in config['pages'].items() if p.get('registration_heading')=='Request a class'}
  self.assertEqual(selected,{'acls','pals'})
  for name in selected:
   c=config['pages'][name];self.assertIn('confirms the date and time',c['meta_description']);self.assertNotIn('register online',c['meta_description']);self.assertIn('request a class',c['documentation_note']['body'])
 def test_four_pages_are_truthful_and_scripts_inventory_routes_unchanged(self):
  for family in ['acls','pals']:
   for name in ['docs/'+family+'.html','docs/'+family.upper()+'.html']:
    after=indexed(name)
    self.assertIn('<h2>Request a class</h2>',after);self.assertIn('910CPR will confirm the date and time.',after);self.assertIn('Your request does not reserve a seat.',after)
    self.assertNotIn('<h2>Register</h2>',after);self.assertNotIn('registration for all three public',after);self.assertNotIn('register online',after)
    scripts=lambda s:[body for attrs,body in re.findall(r'<script([^>]*)>(.*?)</script>',s,re.S) if 'application/ld+json' not in attrs]
    self.assertIn('https://www.910cpr.com/'+family+'.html',after)
 def test_real_generator_persists_copy_and_keeps_bls_default(self):
  configs=generator.load_block_schedule_page_configs()
  for family in ['acls','pals','bls','heartsaver']:
   cfg=configs[family];payload={'pageKey':family,'pageConfig':cfg,'dates':[],'counts':{},'generatedAt':'2031-01-01T00:00:00Z','validUntil':'2031-01-01T00:15:00Z'}
   text=generator.render_html(payload)
   self.assertEqual(text,generator.render_html(payload))
   if family in ['acls','pals']:
    self.assertIn('<h2>Request a class</h2>',text);self.assertIn('Your request does not reserve a seat.',text);self.assertNotIn('registration for all three public',text)
    old=copy.deepcopy(payload)
    for key in ['selector_intro','registration_heading','registration_note']:old['pageConfig'].pop(key,None)
    baseline=generator.render_html(old)
    scripts=lambda t:[body for attrs,body in re.findall(r'<script([^>]*)>(.*?)</script>',t,re.S) if 'application/ld+json' not in attrs]
    self.assertEqual(scripts(baseline),scripts(text))
   else:self.assertIn('<h2>Register</h2>',text)

 def test_configurable_copy_is_html_escaped(self):
  cfg=generator.load_block_schedule_page_configs()['acls'];cfg=copy.deepcopy(cfg);cfg['registration_heading']='<script>unsafe</script>'
  text=generator.render_html({'pageKey':'acls','pageConfig':cfg,'dates':[],'counts':{},'generatedAt':'2031-01-01T00:00:00Z'})
  self.assertIn('&lt;script&gt;unsafe&lt;/script&gt;',text);self.assertNotIn('<h2><script>',text)
if __name__=='__main__':unittest.main()
