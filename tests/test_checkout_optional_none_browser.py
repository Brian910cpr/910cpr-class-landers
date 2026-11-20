"""Optional First Aid clear/reselect behavior; server and external requests intercepted."""
import unittest
from unittest.mock import patch
from tests import test_checkout_three_step_ux_browser as base

class OptionalNoneTests(base.CheckoutUXTests):
 def test_none_default_preserves_meaningful_book_default_and_required_fields(self):
  page,requests,_=self.open()
  none=page.get_by_role('radio',name='None No First Aid',exact=False)
  self.assertTrue(none.is_checked())
  self.assertEqual(none.locator('..').locator('svg[aria-hidden=true] path').get_attribute('d'),'M3 12a9 9 0 1 0 18 0 9 9 0 1 0-18 0 M6 6l12 12')
  self.assertTrue(page.locator('[data-manual-choice][value=own-copy]').is_checked())
  self.assertEqual(page.locator('[data-manual-choice][value=none]').count(),0)
  page.locator('#continue').click()
  self.assertEqual(requests,[])
  self.assertTrue(page.locator('[data-field=firstName]').evaluate('e=>e.required&&!e.checkValidity()'))
 def test_touch_clear_reselect_keeps_other_student_and_manual(self):
  new_context=self.browser.new_context
  with patch.object(self.browser,'new_context',side_effect=lambda **kw:new_context(**dict(kw,has_touch=True))):
   page,requests,_=self.open()
  page.locator('#add-student').click()
  first=page.locator('.student').first;second=page.locator('.student').nth(1)
  first.locator('[data-manual-choice][value=ebook]').check()
  second.locator('[data-first-aid-choice][value=in-person]').check()
  first.locator('[data-first-aid-choice][value=online]').click()
  self.assertIn('$277.49',page.locator('#continue').inner_text())
  first.locator('[data-first-aid-choice][value=none]').tap()
  self.assertIn('$217.49',page.locator('#continue').inner_text())
  first.locator('[data-first-aid-choice][value=in-person]').click()
  self.assertIn('$267.49',page.locator('#continue').inner_text())
  self.assertTrue(first.locator('[data-manual-choice][value=ebook]').is_checked())
  self.assertTrue(second.locator('[data-first-aid-choice][value=in-person]').is_checked())
  self.assertEqual(requests,[])
 def test_keyboard_clear_uses_existing_same_for_all_and_excludes_addon_from_payload(self):
  page,requests,_=self.open();self.fill(page);page.locator('[data-same-for-all]').check()
  page.locator('[data-manual-choice][value=ebook]').check()
  online=page.locator('[data-first-aid-choice][value=online]');online.check()
  online.focus();page.keyboard.press('ArrowDown')
  self.assertTrue(page.locator('[data-first-aid-choice][value=none]').is_checked())
  self.assertIn('$92.49',page.locator('#continue').inner_text())
  page.locator('#continue').click();page.wait_for_url('**/register/?order=*&paid=1')
  student=requests[0]['body']['students'][0]
  self.assertEqual(student['firstAidChoice'],'none')
  self.assertEqual(student['addons'],[{'key':'aha_bls_provider_manual_ebook','quantity':1}])
 def test_none_copy_opt_in_clears_only_first_aid_and_keeps_students(self):
  page,requests,_=self.open();page.locator('#add-student').click()
  first=page.locator('.student').first;second=page.locator('.student').nth(1)
  page.locator('[data-same-for-all]').check()
  first.locator('[data-manual-choice][value=ebook]').check()
  first.locator('[data-first-aid-choice][value=online]').check()
  first.locator('[data-first-aid-choice][value=none]').click()
  self.assertTrue(second.locator('[data-first-aid-choice][value=none]').is_checked())
  self.assertTrue(second.locator('[data-manual-choice][value=ebook]').is_checked())
  self.assertIn('$184.98',page.locator('#continue').inner_text());self.assertEqual(requests,[])

if __name__=='__main__':unittest.main()
