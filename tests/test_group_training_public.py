import json,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs'
class GroupTrainingPublicTests(unittest.TestCase):
 def test_hub_contract(self):
  h=(DOCS/'group-training.html').read_text(encoding='utf-8')
  self.assertEqual(h.count('GTM-PQS8DCBH'),2);self.assertIn('rel="canonical" href="https://www.910cpr.com/group-training.html"',h)
  self.assertIn('/assets/group-training.css?v=20260906.1',h);self.assertNotIn('—',h)
  for event in ('group_training_view','group_industry_selected','group_location_selected','group_program_recommended','group_program_selected','group_schedule_started','group_date_selected','group_request_submitted'):self.assertIn(event,(DOCS/'assets/group-training.js').read_text())
 def test_authority_pages(self):
  pages=sorted((DOCS/'group-training').glob('*/index.html'));self.assertEqual(len(pages),17)
  titles=[];descriptions=[]
  for p in pages:
   h=p.read_text(encoding='utf-8');self.assertEqual(h.count('GTM-PQS8DCBH'),2,p);self.assertNotIn('noindex',h);self.assertIn('BreadcrumbList',h);self.assertIn('"@type":"Service"',h);self.assertIn('Configure and request this training',h);self.assertNotIn('—',h)
   title=re.search(r'<title>(.*?)</title>',h).group(1);desc=re.search(r'<meta name="description" content="(.*?)">',h).group(1);titles.append(title);descriptions.append(desc)
   canonical=re.search(r'<link rel="canonical" href="([^"]+)">',h).group(1);self.assertTrue(canonical.endswith('/'+p.parent.name+'/'))
  self.assertEqual(len(titles),len(set(titles)));self.assertEqual(len(descriptions),len(set(descriptions)))
 def test_sitemap_and_links(self):
  sm=(DOCS/'sitemap.xml').read_text();hub=(DOCS/'group-training.html').read_text()
  for p in (DOCS/'group-training').glob('*/index.html'):
   slug=p.parent.name;self.assertIn(f'/group-training/{slug}/',sm);self.assertIn(f'/group-training/{slug}/',hub)
 def test_legacy_adapter_preserves_context(self):
  h=(DOCS/'request_group_session.html').read_text();self.assertIn("location.search+location.hash",h);self.assertIn('https://www.910cpr.com/request_group_session.html',h)
 def test_backend_never_claims_instant_reservation(self):
  src=(ROOT/'supabase/functions/group-training/index.ts').read_text();self.assertIn("x.offerType!=='seated_class'",src);self.assertIn("b.reservationMode!=='requires_confirmation'",src);self.assertNotIn("status:'confirmed'",src)
if __name__=='__main__':unittest.main()
