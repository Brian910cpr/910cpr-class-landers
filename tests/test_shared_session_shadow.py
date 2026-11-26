import unittest
from dataclasses import replace
from scripts.shared_session_shadow import (
    ARC_SESSION_CAPACITIES, Session, options, remaining, revalidate,
)


class SharedSessionTests(unittest.TestCase):
    def setUp(self):
        self.mapping = {'adult': 'ARC_GENERAL_SKILLS', 'first_aid': 'ARC_GENERAL_SKILLS',
                        'pediatric': 'ARC_GENERAL_SKILLS', 'bls': 'ARC_BLS', 'aha': 'AHA'}
        self.capacities = {**ARC_SESSION_CAPACITIES, 'AHA': 12}
        self.session = Session('nine-am', 'ARC_GENERAL_SKILLS', 4,
                               (('adult', 2), ('first_aid', 1)), 3)

    def query(self, sessions, product='pediatric'):
        return options(product, sessions, ['13:00'], self.mapping, self.capacities)

    def test_mixed_products_share_one_bucket(self):
        self.assertEqual(remaining(self.session, self.mapping), 1)
        self.assertEqual(self.query([self.session])[0]['session_id'], 'nine-am')
        full = replace(self.session, items=self.session.items + (('pediatric', 1),))
        self.assertEqual(remaining(full, self.mapping), 0)
        self.assertEqual(self.query([full]), [dict(mode='new_session', product='pediatric',
                          family='ARC_GENERAL_SKILLS', start='13:00', capacity=4)])
        self.assertEqual(full.items[-1][0], 'pediatric')

    def test_no_legal_later_start_no_offer(self):
        full = replace(self.session, items=(('adult', 4),))
        self.assertEqual(options('adult', [full], [], self.mapping, self.capacities), [])

    def test_bls_separate_and_other_capacity_preserved(self):
        bls = Session('bls', 'ARC_BLS', 4, (('bls', 1),), 1)
        self.assertEqual(self.query([self.session, bls], 'bls')[0]['remaining_seats'], 3)
        aha = Session('aha', 'AHA', 12, (('aha', 4),), 1)
        self.assertEqual(self.query([aha], 'aha')[0]['remaining_seats'], 8)
        self.assertEqual(self.query([], 'aha')[0]['capacity'], 12)

    def test_unknown_and_incompatible_fail_closed(self):
        for items in [(('adult', None),), (('bls', 1),), (('adult', True),), (('adult', -1),)]:
            with self.subTest(items=items), self.assertRaises(ValueError):
                self.query([replace(self.session, items=items)])
        with self.assertRaises(ValueError):
            self.query([], 'unmapped')

    def test_closed_and_overfull_are_not_offered(self):
        for session in [replace(self.session, state='cancelled'),
                        replace(self.session, items=(('adult', 5),))]:
            self.assertEqual(self.query([session])[0]['mode'], 'new_session')

    def test_fourth_seat_revision_contract(self):
        self.assertTrue(revalidate(self.session, 'pediatric', 1, 3, self.mapping))
        committed = replace(self.session, items=self.session.items + (('pediatric', 1),), revision=4)
        self.assertFalse(revalidate(committed, 'first_aid', 1, 3, self.mapping))
        self.assertFalse(revalidate(committed, 'first_aid', 1, 4, self.mapping))
        self.assertFalse(revalidate(self.session, 'bls', 1, 3, self.mapping))
        self.assertFalse(revalidate(self.session, 'adult', 2, 3, self.mapping))

    def test_duplicate_session_rejected(self):
        with self.assertRaises(ValueError):
            self.query([self.session, self.session])


if __name__ == '__main__':
    unittest.main()
