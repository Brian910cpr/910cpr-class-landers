import copy
import json
from pathlib import Path
import unittest

from scripts.arc_catalog_pricing import quote

ROOT = Path(__file__).resolve().parents[1]
COURSES = json.loads((ROOT / 'data/config/course_catalog.json').read_text())['courses']
PRODUCTS = [r for r in COURSES if r.get('commercial_choices')]


class ArcCatalogTests(unittest.TestCase):
    def test_eight_unique_primary_products_and_seo_identities(self):
        self.assertEqual(len(PRODUCTS), 8)
        self.assertEqual(len({r['arc_product_sku'] for r in PRODUCTS}), 8)
        self.assertEqual(len({r['customer_product']['seo_slug'] for r in PRODUCTS}), 8)
        self.assertEqual(len({r['course_id'] for r in COURSES}), len(COURSES))

    def test_source_costs_names_and_qualifications(self):
        expected = {'510':35,'511':35,'512':35,'513':35,'514':43,'515':43,'516':43,'101':30}
        for r in PRODUCTS:
            code = r['arc_product_sku'].split('-')[1][-3:]
            self.assertEqual(r['arc_cost_usd'], expected[code])
            self.assertTrue(r['arc_source_name'].endswith('-BL'))
            self.assertEqual(r['arc_source_effective_date'], '2027-01-01')
            family = 'ARC_BLS' if code == '101' else 'ARC_GENERAL_SKILLS'
            cert = 'ARC_BLS_INSTRUCTOR_R25' if code == '101' else 'ARC_FA_CPR_AED_INSTRUCTOR_R25'
            self.assertEqual(r['session_family'], family)
            self.assertEqual(r['session_capacity'], 4)
            self.assertEqual(r['required_instructor_certifications'], [cert])
            self.assertEqual(r['activation_state'], 'CATALOG_PREPARATION_ONLY')

    def test_approved_prices_and_fulfillment_references(self):
        totals = {30:'87.40',35:'92.80',43:'101.44'}
        skills = {11:'66.88',16:'72.28'}
        by_sku = {r.get('arc_product_sku'):r for r in COURSES if r.get('arc_product_sku')}
        for r in PRODUCTS:
            self.assertEqual(quote(r, 'ONLINE_PLUS_SKILLS')['total_usd'], totals[r['arc_cost_usd']])
            q = quote(r, 'SKILLS_SESSION_ONLY')
            if r.get('skills_session_sku', 'UNKNOWN') == 'UNKNOWN':
                self.assertEqual(q, {'state':'BLOCKED','reason':'unconfirmed_arc_fulfillment','total_usd':None})
            else:
                self.assertEqual(q['total_usd'], skills[r['skills_session_arc_cost_usd']])
                self.assertEqual(by_sku[q['fulfillment_sku']]['arc_cost_usd'], r['skills_session_arc_cost_usd'])

    def test_updated_cost_is_computed_without_mutating_source(self):
        r = copy.deepcopy(PRODUCTS[0])
        r['arc_cost_usd'] = 40
        before = copy.deepcopy(r)
        self.assertEqual(quote(r, 'ONLINE_PLUS_SKILLS')['total_usd'], '98.20')
        self.assertEqual(r, before)

    def test_unknown_cost_does_not_become_zero_fee(self):
        r = copy.deepcopy(PRODUCTS[0])
        r['arc_cost_usd'] = 'UNKNOWN'
        self.assertIsNone(quote(r, 'ONLINE_PLUS_SKILLS')['total_usd'])


if __name__ == '__main__':
    unittest.main()
