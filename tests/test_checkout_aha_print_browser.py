"""Synthetic intercepted link activation; no AHA shopping or registration calls."""
import unittest
from tests import test_checkout_three_step_ux_browser as base

SHOP='https://shopcpr.heart.org/all-products?associated_course=49&format=84'

class AhaPrintTests(base.CheckoutUXTests):
 def activate(self,page,student=0,keyboard=False):
  link=page.locator('.student').nth(student).locator('[data-select-print]')
  self.assertEqual(link.get_attribute('href'),SHOP)
  self.assertEqual(link.get_attribute('target'),'_blank')
  self.assertEqual(set(link.get_attribute('rel').split()),{'noopener','noreferrer'})
  shop_requests=[]
  # Override the inherited catch-all: only a local empty response reaches the popup.
  page.context.route('https://shopcpr.heart.org/**',lambda r:(shop_requests.append(r.request.url),r.fulfill(body='<title>Intercepted external shop</title>'))[-1])
  original=page.url
  with page.expect_popup() as popup:
   if keyboard:link.focus();page.keyboard.press('Enter')
   else:link.click()
  other=popup.value;other.wait_for_load_state()
  self.assertEqual(other.url,SHOP);self.assertEqual(shop_requests,[SHOP])
  self.assertIsNone(other.evaluate('window.opener'))
  self.assertEqual(page.url,original)
  self.assertTrue(page.locator('.student').nth(student).locator('[data-manual-choice][value=physical]').is_checked())
  other.close()
 def test_pointer_selects_adjacent_second_student_preserving_first_and_other_options(self):
  page,requests,_=self.open();self.fill(page)
  page.locator('[data-manual-choice][value=ebook]').check()
  page.locator('[data-first-aid-choice][value=online]').check()
  page.locator('#add-student').click()
  second=page.locator('.student').nth(1)
  second.locator('[data-manual-choice][value=ebook]').check()
  second.locator('[data-first-aid-choice][value=in-person]').check()
  self.activate(page,1)
  self.assertTrue(page.locator('[data-manual-choice][value=ebook]').first.is_checked())
  self.assertTrue(page.locator('[data-first-aid-choice][value=online]').first.is_checked())
  self.assertTrue(second.locator('[data-first-aid-choice][value=in-person]').is_checked())
  self.assertIn('$277.49',page.locator('#continue').inner_text())
  self.assertEqual(page.locator('[data-field=email]').first.input_value(),'synthetic@example.invalid')
  self.assertEqual(requests,[])
 def test_keyboard_uses_normal_change_path_and_existing_copy_opt_in(self):
  page,requests,_=self.open();page.locator('#add-student').click()
  page.locator('[data-same-for-all]').check()
  page.locator('[data-manual-choice][value=ebook]').first.check()
  self.assertTrue(page.locator('[data-manual-choice][value=ebook]').nth(1).is_checked())
  self.activate(page,0,keyboard=True)
  self.assertTrue(page.locator('[data-manual-choice][value=physical]').nth(1).is_checked())
  self.assertIn('$150.00',page.locator('#continue').inner_text())
  self.assertEqual(requests,[])
 def test_keyboard_without_copy_opt_in_changes_only_first_student(self):
  page,requests,_=self.open();page.locator('#add-student').click()
  page.locator('[data-manual-choice][value=ebook]').first.check()
  self.activate(page,0,keyboard=True)
  self.assertTrue(page.locator('[data-manual-choice][value=own-copy]').nth(1).is_checked())
  self.assertIn('$150.00',page.locator('#continue').inner_text())
  self.assertEqual(requests,[])
 def test_product_information_link_does_not_select_print(self):
  page,requests,_=self.open()
  page.context.route('https://shopcpr.heart.org/**',lambda r:r.fulfill(body='<title>Intercepted information</title>'))
  link=page.locator('.product-choice a').first
  with page.expect_popup() as popup:link.click()
  popup.value.close()
  self.assertTrue(page.locator('[data-manual-choice][value=own-copy]').is_checked())
  self.assertEqual(requests,[])
 def test_second_student_link_never_changes_first_even_with_copy_opt_in(self):
  page,requests,_=self.open();page.locator('#add-student').click()
  page.locator('[data-same-for-all]').check()
  page.locator('[data-manual-choice][value=ebook]').first.check()
  self.activate(page,1)
  self.assertTrue(page.locator('[data-manual-choice][value=ebook]').first.is_checked())
  self.assertIn('$167.49',page.locator('#continue').inner_text())
  self.assertEqual(requests,[])
 def test_intercepted_payload_records_preference_not_an_aha_purchase(self):
  page,requests,_=self.open();self.fill(page);self.activate(page)
  self.assertIn('$75.00',page.locator('#continue').inner_text())
  page.locator('#continue').click();page.wait_for_url('**/register/?order=*&paid=1')
  student=requests[0]['body']['students'][0]
  self.assertEqual(student['manualChoice'],'physical');self.assertEqual(student['addons'],[])
  self.assertFalse(any('paid' in k.lower() or 'purchased' in k.lower() for k in student))
  self.assertNotIn('price',student)
 def test_opening_shop_again_for_selected_print_does_not_recopy_other_students(self):
  page,requests,_=self.open();page.locator('#add-student').click()
  page.locator('[data-same-for-all]').check();self.activate(page)
  page.locator('[data-manual-choice][value=ebook]').nth(1).check()
  self.activate(page)
  self.assertTrue(page.locator('[data-manual-choice][value=ebook]').nth(1).is_checked())
  self.assertIn('$167.49',page.locator('#continue').inner_text());self.assertEqual(requests,[])

if __name__=='__main__':unittest.main()
