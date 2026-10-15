"""Read-only catalog checks: no generator, scheduler, or remote writes."""
import json
import unittest
from collections import Counter
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / 'data/config/course_catalog.json'


class HSICatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(CATALOG.read_text(encoding='utf-8'))
        cls.courses = cls.payload['courses']
        cls.hsi = [c for c in cls.courses if c['provider'] == 'HSI']

    def test_exact_configuration_delivery_pairs(self):
        configurations = {
            'adult_first_aid', 'adult_cpr_aed', 'adult_child_cpr_aed',
            'adult_infant_cpr_aed', 'adult_child_infant_cpr_aed',
            'adult_first_aid_adult_cpr_aed',
            'adult_first_aid_adult_child_cpr_aed',
            'adult_first_aid_adult_infant_cpr_aed',
            'adult_first_aid_adult_child_infant_cpr_aed',
            'pediatric_first_aid', 'child_infant_cpr_aed',
            'child_infant_adult_cpr_aed',
            'pediatric_first_aid_child_infant_cpr_aed',
            'pediatric_first_aid_child_infant_adult_cpr_aed', 'bls',
        }
        actual = Counter((c['certification_identity'], c['delivery_type'])
                         for c in self.hsi if 'certification_identity' in c)
        self.assertEqual(actual, Counter({('hsi_' + name, mode): 1
                         for name in configurations for mode in ('BL', 'CHALLENGE')}))
        self.assertEqual(len({c['course_id'] for c in self.courses}), len(self.courses))
        self.assertEqual(len({c['course_key'] for c in self.hsi}), len(self.hsi))
        self.assertTrue(any(c['course_id'] == '448630' and c['delivery_type'] == 'IP'
                            for c in self.hsi))

    def test_challenge_is_evaluation_and_review_is_separate(self):
        for c in self.hsi:
            if c['delivery_type'] != 'CHALLENGE':
                continue
            with self.subTest(course=c['course_id']):
                self.assertTrue(c['challenge_written_exam_required'])
                self.assertTrue(c['challenge_skills_evaluation_required'])
                self.assertFalse(c['challenge_instruction_during_evaluation'])
                review = c['optional_review_template']
                self.assertTrue(review['review_is_separate_noncertifying_event'])
                self.assertEqual(review['review_start_offset_minutes'], -60)
                self.assertEqual(review['challenge_start_offset_minutes'], 0)
                self.assertEqual(review['challenge_reserved_minutes'], 45)
                self.assertTrue(review['challenge_only_arrival_allowed'])
                self.assertIn('return later', review['failure_customer_policy'])

    def test_owner_pediatric_cost_basis(self):
        expected = {
            'DCPEDFA-25': (8.47, 8.22), 'DCPEDCPR-25': (8.47, 8.22),
            'DCPEDCPR-25CI': (8.47, 8.22), 'DCPEDCOMBO-25CI': (14.58, 14.14),
            'DCPEDCOMBO-25': (14.58, 14.14), 'HBL-PEDFA-25': (11.96, 11.60),
            'HBL-PEDCPR-25': (11.96, 11.60), 'HBL-PEDCPR-CI25': (11.96, 11.60),
            'HBL-PEDCOMBO-CI25': (16.77, 16.27), 'HBL-PEDCOMBO-25': (16.77, 16.27),
        }
        actual = {c['hsi_product_code']: (c['hsi_list_price_usd'], c['hsi_discounted_cost_usd'])
                  for c in self.hsi if c.get('hsi_product_code') in expected}
        self.assertEqual(actual, expected)
        for c in self.hsi:
            if 'certification_identity' in c:
                self.assertEqual(c['external_hsi_product_id'], c.get('hsi_product_code', 'UNKNOWN'))
            if c.get('hsi_product_code') in expected:
                self.assertTrue(c['hsi_product_code'].startswith('HBL-')
                                if c['delivery_type'] == 'BL' else c['hsi_product_code'].startswith('DC'))

    def test_rsv_and_inventory_are_separate(self):
        products = {p['product_code']: p for c in self.hsi
                    for p in c.get('hsi_alternate_fulfillment_products', [])}
        self.assertEqual(len(products), 9)
        self.assertEqual(products['HRSV-PED-CI25']['discounted_cost_usd'], 'UNKNOWN')
        for p in products.values():
            self.assertTrue(p['requires_separate_delivery_path'])
            self.assertFalse(p['substitutable_for_in_person_skills'])
            self.assertIn(p['mode'], ('RSV', 'RSV_WITH_LOANER_MANIKIN'))
        support = self.payload['hsi_support_products']
        self.assertEqual(len(support), 4)
        for p in support:
            self.assertEqual(p['pack_quantity'], 5)
            self.assertFalse(p['default_certification_fulfillment'])


if __name__ == '__main__':
    unittest.main()
