import json,re,unittest
from pathlib import Path
from urllib.parse import parse_qs,urlsplit
from scripts.class_registration_routing import registration_action,owned_registration,rewrite_detail_routes,CAPABILITIES,public_location_display
ROOT=Path(__file__).resolve().parents[1]
class ClassRoutingTests(unittest.TestCase):
 def records(self):
  return {sid:dict(session_id=sid,course_id=c['course_id'],course_number=c['course_id'],start_at=c['starts_at'],location_display=c['location'],course_name='BLS Initial',registration_url='https://coastalcprtraining.enrollware.com/enroll?id='+sid,session_status='active') for sid,c in json.loads(CAPABILITIES.read_text())['sessions'].items()}
 def test_six_capabilities_use_own_ids(self):
  self.assertEqual(len(self.records()),6)
  for sid,row in self.records().items():
   self.assertEqual(registration_action(row)['href'],'https://www.910cpr.com/register/?session='+sid)
 def test_mismatch_missing_closed_and_ambiguous_fields_fail_closed(self):
  row=self.records()['15026275']
  for change in ({'start_at':''},{'start_at':'2026-11-20T11:30:00-05:00'},{'course_number':'359474'},{'course_id':'359474'},{'location_display':'Another site'},{'registration_status':'closed'},{'is_full':True}):
   with self.subTest(change=change):self.assertEqual(registration_action(dict(row,**change))['mode'],'request')
 def test_request_preserves_selected_class_not_confirmation(self):
  row=dict(session_id='999',course_id='359474',course_name='BLS Renewal',start_at='2026-12-01T10:00:00-05:00',location_display='Shipyard')
  action=registration_action(row);self.assertEqual(action['label'],'Request this class')
  body=parse_qs(urlsplit(action['href']).query)['body'][0]
  for value in ['BLS Renewal','2026-12-01T10:00:00-05:00','Shipyard','/classes/999.html','not a confirmed reservation']:self.assertIn(value,body)
 def test_owned_routes_validate_host_identity_course_and_duplicates(self):
  good='/register/?session=999&course=359474'
  self.assertEqual(owned_registration(good,'999','359474'),'https://www.910cpr.com'+good)
  for url in ['https://example.pages.dev'+good,'//untrusted.invalid'+good,'https://www.910cpr.com.evil.invalid'+good,good+'&session=777',good.replace('359474','209806'),good+'#fragment']:
   self.assertEqual(owned_registration(url,'999','359474'),'')
 def test_detail_rewrite_preserves_price_and_is_idempotent(self):
  row=dict(session_id='999',course_id='359474',course_name='BLS Renewal',start_at='2026-12-01T10:00:00-05:00',location_display='Shipyard')
  original='''<script type="application/ld+json">{"offers":{"price":"75.00","url":"https://coastalcprtraining.enrollware.com/enroll?id=999"}}</script><div class="cta-panel"><p class="cta-panel-label">Reserve your seat</p><p class="cta-panel-copy">Direct registration</p><div class="cta-row"><a class="button primary" href="/register/?session=999">Continue to Registration</a></div></div><a href="https://coastalcprtraining.enrollware.com/schedule#ct359474">Full schedule</a><script>const pageContext={register_url: "/register/?session=999",schedule_url: "external",class_status: "scheduled"};if (!shouldForward || !pageContext.register_url) return;</script>'''
  output=rewrite_detail_routes(original,row,{'999':row})
  self.assertIn('Request this class',output);self.assertNotIn('Reserve your seat',output)
  self.assertNotIn('coastalcprtraining.enrollware.com',output)
  self.assertIn('href="/classes/"',output)
  self.assertIn('startsWith("https://www.910cpr.com/register/")',output)
  self.assertEqual(json.loads(re.search(r'application/ld\+json">(.*?)</script>',output)[1])['offers']['price'],'75.00')
  self.assertEqual(rewrite_detail_routes(output,row,{'999':row}),output)
 def test_current_listings_and_details_match_actions(self):
  html=(ROOT/'docs/classes/index.html').read_text(encoding='utf8')
  ids=re.findall(r'class="class-finder-secondary" href="/classes/(\d+)\.html"',html)
  rows=json.loads((ROOT/'docs/data/schedule_future.json').read_text(encoding='utf8'))['sessions'];source={str(r['session_id']):r for r in rows}
  cards=re.findall(r'<article class="class-finder-card[^>]*>.*?</article>',html,re.S)
  self.assertEqual(len(ids),len(cards))
  from html import unescape
  for sid,card in zip(ids,cards):
   action=registration_action(source[sid]);href=unescape(re.search(r'class="class-finder-primary" href="([^"]+)"',card)[1])
   self.assertEqual(href,action['href']);self.assertIn('>'+action['label']+'</a>',card)
   self.assertNotIn('https://coastalcprtraining.enrollware.com',(ROOT/'docs/classes'/(sid+'.html')).read_text(encoding='utf8'))
  self.assertNotIn('https://coastalcprtraining.enrollware.com',html)
 def test_canonical_generator_integration(self):
  from scripts import build_index_and_sitemap as index,build_landers as detail
  rows=index.load_schedule_future_sessions();normalized=[index.schedule_future_to_public_session(r) for r in rows];normalized=[r for r in normalized if r]
  self.assertNotIn('coastalcprtraining.enrollware.com',index.render_classes_finder_index(normalized))
  for row in self.records().values():
   public=index.schedule_future_to_public_session(row);self.assertIsNotNone(public)
   self.assertEqual(registration_action(public)['mode'],'native')
   self.assertEqual(detail.public_registration_url(row),registration_action(row)['href'])
 def test_customer_location_redacts_internal_room_without_changing_native_match(self):
  from scripts.build_landers import clean_location_display
  for raw in [':: Wilmington; Shipyard Blvd - B','Wilmington; Shipyard Blvd - B', "NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office"]:
   self.assertEqual(public_location_display(raw),'Wilmington; Shipyard Blvd')
   self.assertEqual(clean_location_display(raw),'Wilmington; Shipyard Blvd')
  self.assertEqual(public_location_display('Another offsite venue'),'Another offsite venue')
  row=dict(session_id='999',course_id='359474',course_name='BLS Renewal',start_at='2026-12-01T10:00:00-05:00',location_display='Wilmington; Shipyard Blvd - B')
  body=parse_qs(urlsplit(registration_action(row)['href']).query)['body'][0]
  self.assertIn('Location: Wilmington; Shipyard Blvd',body)
  self.assertNotIn('Room B',body)
  self.assertNotIn('Shipyard Blvd - B',body)
  for sid,existing in self.records().items():
   self.assertEqual(registration_action(existing)['mode'],'native',sid)
 def test_generated_heartsaver_detail_is_request_only_and_public_office(self):
  page=(ROOT/'docs/classes/14114232.html').read_text(encoding='utf8')
  self.assertIn('no seat is reserved until confirmed',page)
  self.assertIn('Request only. No seat is reserved',page)
  self.assertNotIn('with direct registration after the class details below',page)
  self.assertNotIn('Shipyard Blvd - B',page)
  self.assertNotIn('Shipyard+Blvd+-+B',page)
  self.assertIn('Wilmington; Shipyard Blvd',page)
 def test_request_hero_never_promises_direct_registration(self):
  row=dict(session_id='999',course_id='359474',course_name='BLS Renewal',start_at='2026-12-01T10:00:00-05:00',location_display='Wilmington; Shipyard Blvd - B')
  body='<p class="subhead">Morning session in Wilmington with direct registration after the class details below.</p><div class="cta-panel"><p class="cta-panel-label">Reserve your seat</p><p class="cta-panel-copy">Direct registration</p><div class="cta-row"><a class="button primary" href="/register/?session=999">Continue to Registration</a></div></div><script>const pageContext={register_url: "/register/?session=999",class_status: "scheduled"};</script>'
  output=rewrite_detail_routes(body,row,{'999':row})
  self.assertNotIn('with direct registration after the class details below',output)
  self.assertIn('no seat is reserved until confirmed',output)
  self.assertIn('Request this class',output)
  self.assertEqual(output,rewrite_detail_routes(output,row,{'999':row}))
  sid='15026275'
  native=self.records()[sid]
  native_html=body.replace('session=999','session='+sid)
  native_output=rewrite_detail_routes(native_html,native,{sid:native})
  self.assertIn('with direct registration after the class details below',native_output)
  self.assertIn('Continue to Registration',native_output)
 def test_related_cards_and_sidebar_hide_unverified_or_private_occurrences(self):
  # A refreshed directory may drop an old private or expired listing while
  # retained public detail HTML still advertises it in related suggestions.
  src='''<section class="js-live-session-group">
<div class="upcoming-card js-session-item" data-session-id="101" data-start="2026-12-01T10:00:00-05:00">
  <div class="upcoming-date">December 1, 2026</div>
  <div class="upcoming-actions"><a href="/classes/101.html">Register</a></div>
</div>
<div class="upcoming-card js-session-item" data-session-id="102" data-start="2026-12-07T17:30:00-05:00">
  <div class="upcoming-date">Private date must disappear</div>
  <div class="upcoming-actions"><a href="/classes/102.html">Register</a></div>
</div>
</section>
<aside class="current-courses-sidebar"><ul><li><a href="/classes/102.html">Private sidebar time</a></li><li><a href="/classes/101.html">Public sidebar time</a></li></ul></aside>
'''
  session={'session_id':'101','course_id':'359474','course_name':'AHA BLS Renewal','start_at':'2026-12-01T10:00:00-05:00','location_display':'Wilmington; Shipyard Blvd'}
  verified={'101':session}
  output=rewrite_detail_routes(src,session,verified)
  self.assertIn('data-session-id="101"',output)
  self.assertIn('Public sidebar time',output)
  for secret in ['data-session-id="102"','Private date must disappear','Private sidebar time','/classes/102.html']:
   self.assertNotIn(secret,output)
  self.assertEqual(rewrite_detail_routes(output,session,verified),output)
 def test_related_recommendations_with_uuid_or_missing_id_fail_closed(self):
  # The generator writes arbitrary source session IDs into related cards;
  # a private canonical UUID is not a numeric Enrollware identity.
  public_id='11111111-1111-4111-8111-111111111111'
  private_id='22222222-2222-4222-8222-222222222222'
  src='''<section class="js-live-session-group">
<div class="upcoming-card js-session-item" data-session-id="'''+public_id+'''" data-start="2026-12-01T10:00:00-05:00">
  <div class="upcoming-date">Verified public date</div>
</div>
<div class="upcoming-card js-session-item" data-session-id="'''+private_id+'''" data-start="2026-12-07T17:30:00-05:00">
  <div class="upcoming-date">Private UUID date</div>
</div>
<div class="upcoming-card js-session-item" data-start="2026-12-08T12:00:00-05:00">
  <div class="upcoming-date">Unattributed private date</div>
</div>
</section>
<aside class="current-courses-sidebar"><ul><li><a href="/classes/'''+public_id+'''.html">Public sidebar date</a></li><li><a href="/classes/'''+private_id+'''.html">Private UUID sidebar date</a></li></ul></aside>
'''
  public={'session_id':public_id,'course_id':'359474','course_name':'BLS Renewal','start_at':'2026-12-01T10:00:00-05:00','location_display':'Wilmington; Shipyard Blvd'}
  output=rewrite_detail_routes(src,public,{public_id:public})
  self.assertIn('Verified public date',output)
  self.assertIn('Public sidebar date',output)
  for secret in (private_id,'Private UUID date','Private UUID sidebar date','Unattributed private date','2026-12-07T17:30:00-05:00'):
   self.assertNotIn(secret,output)
  self.assertEqual(output,rewrite_detail_routes(output,public,{public_id:public}))
if __name__=='__main__':unittest.main()
