"""No browser launch: prove synthetic fixtures use the actual generic model."""
import copy
import unittest
from tests.native_bls_browser_fixtures import fixture, seated_fixture, offers, selection, generic_model, public_selector_availability_payload


class BlsBrowserFixtureTests(unittest.TestCase):
    def test_generated_dynamic_and_held_models_share_capacity_but_not_package(self):
        for held in (False, True):
            case, payload = seated_fixture()[:2] if held else fixture()
            feed = public_selector_availability_payload(payload)
            rows = offers(feed)
            self.assertEqual({r['courseId'] for r in rows}, {'509474', '210549'})
            pair = rows[:2]
            self.assertEqual(pair[0]['nativeOfferId'], pair[1]['nativeOfferId'])
            self.assertNotEqual(pair[0]['selectionId'], pair[1]['selectionId'])
            for row in pair:
                packet = generic_model(case, feed, selection(row['registrationUrl']), remaining=1 if held else 2)
                self.assertEqual(packet['status'], 200, packet)
                model = packet['body']
                self.assertEqual(model['session']['capacity'], 2)
                self.assertEqual(model['session']['remainingSeats'], 1 if held else 2)
                self.assertEqual(model['profile']['maxStudents'], 1 if held else 2)
                choices = model['profile']['optionGroups'][0]['choices']
                self.assertEqual(len(choices), 1)
                self.assertEqual(model['profile']['baseCents']+choices[0]['amountCents'], 5500 if row['courseId']=='509474' else 9500)
                self.assertTrue(all(c['name'] not in ('reserve_native_checkout_order', 'native_checkout_receipt') for c in packet['calls']))

    def test_saved55_model_and_status_only_read_original_receipt(self):
        case, payload = fixture()
        feed = public_selector_availability_payload(payload)
        for action in ('form', 'status'):
            result = generic_model(case, feed, {}, saved=True, action=action, bundleEnabled=False,
                                   key='44444444-1111-4111-8111-111111111111')
            self.assertEqual(result['status'], 200, result)
            self.assertEqual(result['body']['receipt']['amountCents'], 5500)
            self.assertEqual(result['body']['receipt']['students'][0]['selectedChoices'], ['skills_only'])
            self.assertTrue(all(c['name']=='native_checkout_receipt' for c in result['calls']))

    def test_legacy_unique55_and_fail_closed_models(self):
        case, payload = fixture()
        feed = public_selector_availability_payload(payload)
        row = next(r for r in offers(feed) if r['courseId']=='509474')
        legacy = dict(course='210549', skillsContext='bls-skills', date=row['date'], startTime=row['startTime'],
                      instructor=row['instructor'], location=row['location'])
        result = generic_model(case, feed, legacy, bundleEnabled=False)
        self.assertEqual(result['status'], 200, result)
        self.assertEqual(result['body']['selection']['course'], '509474')
        self.assertEqual(result['body']['profile']['defaultChoices'], ['skills_only'])
        for selected, data, kwargs in [
            ({'course':'210549','skillsContext':'bls-skills'}, feed, {}),
            (dict(legacy, selectionId='skills:legacy55'), feed, {}),
            (legacy, feed, {'remaining':0}),
            (legacy, feed, {'skillsEnabled':False}),
        ]:
            self.assertEqual(generic_model(case, data, selected, **kwargs)['status'], 409)
        ambiguous = copy.deepcopy(feed)
        for day in ambiguous['dates']:
            for slot in day['startTimes']:
                slot['courses'] += copy.deepcopy(slot['courses'])
        self.assertEqual(generic_model(case, ambiguous, legacy)['status'], 409)


if __name__ == '__main__':
    unittest.main()
