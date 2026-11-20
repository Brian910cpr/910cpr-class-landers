"""Intercepted checkout presentation proof. All requests served locally, no submissions."""
import os,unittest
from pathlib import Path
from unittest.mock import patch
from tests import test_checkout_three_step_ux_browser as base

class CheckoutFormatTests(base.CheckoutUXTests):
 def test_other_course_does_not_receive_bls_product_art_or_options(self):
  with patch.dict(base.SESSION,{'courseId':'209809','course':'Synthetic other course'}):
   page,requests,_=self.open()
  self.assertEqual(page.locator('.product-format,.product-choice,.product-image').count(),0)
  self.assertEqual(requests,[])
 def test_format_labels_keyboard_names_and_no_art_gutter(self):
  page,requests,_=self.open()
  self.assertEqual(page.locator('.product-format').count(),6)
  self.assertEqual(page.locator('.product-image').count(),0)
  self.assertEqual(page.locator('.product-choice img').count(),0)
  self.assertEqual(page.locator('.product-format svg[aria-hidden=true][focusable=false]').count(),6)
  ebook=page.get_by_role('radio',name='eBook BLS Provider Manual eBook',exact=False)
  ebook.focus();page.keyboard.press('Space');self.assertTrue(ebook.is_checked())
  page.keyboard.press('ArrowDown')
  physical=page.get_by_role('radio',name='Print book Physical BLS Manual',exact=False)
  self.assertTrue(physical.is_checked());self.assertTrue(physical.evaluate('e=>e===document.activeElement'))
  self.assertIn('not included in this order',physical.locator('..').inner_text())
  self.assertIn('does not replace any required in-person skills',page.get_by_role('radio',name='Online learning AHA Heartsaver First Aid online',exact=False).locator('..').inner_text())
  self.assertEqual(requests,[])
 def test_option_payload_is_unchanged_with_format_labels(self):
  page,requests,_=self.open();self.fill(page)
  page.locator('[data-manual-choice][value=ebook]').check()
  page.locator('[data-first-aid-choice][value=online]').check()
  page.locator('#continue').click();page.wait_for_url('**/register/?order=*&paid=1')
  student=requests[0]['body']['students'][0]
  self.assertEqual(student['manualChoice'],'ebook');self.assertEqual(student['firstAidChoice'],'online')
  self.assertEqual(student['addons'],[{'key':'aha_bls_provider_manual_ebook','quantity':1},{'key':'aha_heartsaver_first_aid_online','quantity':1}])
  self.assertNotIn('productFormat',student);self.assertNotIn('price',student)
 def test_labels_and_selection_mapping_survive_added_student(self):
  page,requests,_=self.open()
  page.locator('[data-manual-choice][value=ebook]').check()
  page.locator('[data-first-aid-choice][value=online]').check()
  page.locator('[data-same-for-all]').check();page.locator('#add-student').click()
  self.assertEqual(page.locator('.product-format').count(),12)
  self.assertTrue(page.locator('[data-manual-choice][value=ebook]').nth(1).is_checked())
  self.assertTrue(page.locator('[data-first-aid-choice][value=online]').nth(1).is_checked())
  self.assertIn('$304.98',page.locator('#continue').inner_text())
  self.assertEqual(requests,[])
 def test_format_visuals_all_sizes_themes_and_screenshots(self):
  destination=os.environ.get('CHECKOUT_VISUAL_EVIDENCE')
  for theme in ('light','dark'):
   for width in (390,1440):
    with self.subTest(theme=theme,width=width):
     page,requests,_=self.open(theme,width)
     self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
     for badge in page.locator('.product-format').all():
      self.assertTrue(badge.is_visible());self.assertGreaterEqual(self.contrast(badge),4.5)
     page.locator('[data-first-aid-choice][value=online]').focus()
     self.assertNotEqual(page.locator('[data-first-aid-choice][value=online]').evaluate('e=>getComputedStyle(e).outlineStyle'),'none')
     if destination:
      folder=Path(destination);folder.mkdir(parents=True,exist_ok=True)
      page.screenshot(path=str(folder/f'checkout-formats-{theme}-{width}.png'),full_page=True)
     self.assertEqual(requests,[])

if __name__=='__main__':unittest.main()
