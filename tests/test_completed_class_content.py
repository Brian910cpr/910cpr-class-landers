import json
import unittest
from pathlib import Path
from scripts.completed_class_content import calendar_context, render_completed_content

ROOT = Path(__file__).resolve().parents[1]


class CompletedClassContentTests(unittest.TestCase):
    def setUp(self):
        self.pages = json.loads((ROOT / 'data/config/block_schedule_pages.json').read_text(encoding='utf-8'))

    def test_each_configured_course_maps_to_existing_family_feed(self):
        for key, page in self.pages['pages'].items():
            for option in page.get('course_options', []):
                with self.subTest(key=key, course_id=option['course_id']):
                    context = calendar_context(option['course_id'], self.pages)
                    occurrences = sum(any(str(item.get('course_id')) == str(option['course_id']) for item in candidate.get('course_options', [])) for candidate in self.pages['pages'].values())
                    if occurrences > 1:
                        self.assertIsNone(context)
                        continue
                    self.assertIsNotNone(context)
                    self.assertEqual(str(option['course_id']), context['course_id'])
                    self.assertTrue((ROOT / 'docs' / context['availability_url'].lstrip('/')).is_file())
                    self.assertEqual('/' + page['output_path'].removeprefix('docs/'), context['course_page_url'])

    def test_unknown_does_not_guess_a_family_or_delivery(self):
        for course_id in ('', 'unknown', None):
            self.assertIsNone(calendar_context(course_id, self.pages))

    def test_ambiguous_course_fails_closed(self):
        page = {'output_path': 'docs/bls.html', 'course_options': [{'course_id': '1'}]}
        self.assertIsNone(calendar_context('1', {'pages': {'one': page, 'two': page}}))

    def test_verified_source_page_disambiguates_shared_ids(self):
        for course_id in ('209809', '329495'):
            self.assertIsNone(calendar_context(course_id, self.pages))
            for key in ('heartsaver', 'uscg-first-aid-cpr-aed'):
                with self.subTest(course_id=course_id, page=key):
                    context = calendar_context(course_id, self.pages, verified_page_key=key)
                    self.assertEqual(context['course_id'], course_id)
                    self.assertEqual(context['page_key'], key)
                    self.assertEqual(context['availability_url'],
                                     f'/data/block-selector-availability/{key}.json')

    def test_source_page_never_overrides_exact_course_membership(self):
        for key in ('unknown', '', 'acls'):
            self.assertIsNone(calendar_context('209809', self.pages, verified_page_key=key))
        self.assertIsNone(calendar_context('unknown', self.pages,
                                          verified_page_key='heartsaver'))

    def test_invalid_output_path_fails_closed_even_with_verified_page(self):
        for output in ('../outside.html', 'docs/../outside.html', '/docs/bls.html',
                       'docs/bls.js'):
            pages = {'pages': {'one': {'output_path': output,
                                     'course_options': [{'course_id': '1'}]}}}
            with self.subTest(output=output):
                self.assertIsNone(calendar_context('1', pages, verified_page_key='one'))

    def test_compact_order_context_and_escaping(self):
        rendered = render_completed_content(course_name='ACLS <HeartCode>', date_label='September 24, 2026',
            location='Shipyard & Wilmington', calendar_html='<div id="calendar"></div>',
            fallback_html='<a href="/classes/2.html">Next class</a>')
        self.assertLess(rendered.index('This class has passed'), rendered.index('calendar'))
        self.assertLess(rendered.index('calendar'), rendered.index('/classes/2.html'))
        self.assertLess(rendered.index('/classes/2.html'), rendered.index('Original class'))
        self.assertIn('ACLS &lt;HeartCode&gt;', rendered)
        self.assertIn('Shipyard &amp; Wilmington', rendered)
        self.assertNotIn('Reserve your seat', rendered)
        self.assertNotIn('Continue to Registration', rendered)
        self.assertLess(len(rendered), 1200)


if __name__ == '__main__':
    unittest.main()
