import re,unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs'
class GroupTrainingPublicTests(unittest.TestCase):
 def test_hub_contract(self):
  h=(DOCS/'group-training.html').read_text(encoding='utf-8')
  self.assertEqual(h.count('GTM-PQS8DCBH'),2);self.assertIn('rel="canonical" href="https://www.910cpr.com/group-training.html"',h)
  self.assertIn('/assets/group-training.css?v=20260906.2',h);self.assertIn('/images/PrestonsReady.webp',h);self.assertNotIn('—',h)
  for event in ('group_training_view','group_industry_selected','group_location_selected','group_program_recommended','group_program_selected','group_schedule_started','group_date_selected','group_request_submitted'):self.assertIn(event,(DOCS/'assets/group-training.js').read_text(encoding='utf-8'))
 def test_authority_pages(self):
  pages=sorted((DOCS/'group-training').glob('*/index.html'));self.assertEqual(len(pages),12)
  titles=[];descriptions=[]
  for p in pages:
   h=p.read_text(encoding='utf-8');self.assertEqual(h.count('GTM-PQS8DCBH'),2,p);self.assertNotIn('noindex',h);self.assertIn('BreadcrumbList',h);self.assertIn('"@type":"Service"',h);self.assertIn('Build a training plan for this team',h);self.assertNotIn('—',h)
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
  core=(ROOT/'supabase/functions/group-training/core.mjs').read_text();src=(ROOT/'supabase/functions/group-training/index.ts').read_text();self.assertIn("x.offerType!=='seated_class'",core);self.assertIn('requires_confirmation',core);self.assertNotIn("status:'confirmed'",src)
 def test_transaction_idempotency_dedupe_and_eastern_time(self):
  sql=(ROOT/'supabase/migrations/20260906010000_group_training_requests.sql').read_text()
  self.assertTrue(sql.startswith('begin;'));self.assertTrue(sql.rstrip().endswith('commit;'));self.assertIn('pg_advisory_xact_lock',sql);self.assertIn('lower(trim(display_name))',sql);self.assertIn("at time zone 'America/New_York'",sql);self.assertIn('idempotency_key text not null unique',sql)
  eastern=ZoneInfo('America/New_York')
  self.assertEqual(datetime(2026,1,15,9,tzinfo=eastern).astimezone(ZoneInfo('UTC')).isoformat(),'2026-01-15T14:00:00+00:00')
  self.assertEqual(datetime(2026,7,15,9,tzinfo=eastern).astimezone(ZoneInfo('UTC')).isoformat(),'2026-07-15T13:00:00+00:00')
 def test_cloudflare_asset_boundary(self):
  oversized=[p for p in DOCS.rglob('*') if p.is_file() and p.stat().st_size>25*1024*1024]
  self.assertEqual(oversized,[])
if __name__=='__main__':unittest.main()
