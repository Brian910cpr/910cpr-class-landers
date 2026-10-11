from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from scripts import audit_sitewide_links, build_slug_hubs as builder
from scripts import validate_sitewide_links_strict


class CourseBookingLinkTests(TestCase):
    def session(self):
        return {
            'session_id': 'lw-eb020e4a-b74a-443e-acd8-05727c2a8170',
            'course_id': '209809',
            'course_name': 'AHA Heartsaver First Aid CPR AED',
            'start_at': '2026-10-13T09:00:00-04:00',
            'end_at': '2026-10-13T11:00:00-04:00',
            'location_name': ':: Wilmington; Shipyard Blvd',
            'active_registration_count': 2,
            'registration_url': 'https://www.910cpr.com/register/?session=lw-eb020e4a-b74a-443e-acd8-05727c2a8170',
            'registration_backend': 'landerware',
        }

    def test_canonical_occurrence_without_class_input_uses_direct_booking_and_passes_audit(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / 'docs'
            courses = docs / 'courses'
            courses.mkdir(parents=True)
            (docs / 'register').mkdir()
            (docs / 'register' / 'index.html').write_text('<html></html>', encoding='utf-8')
            debug = root / 'debug'
            debug.mkdir()
            session = self.session()
            with patch.object(builder, 'OUTPUT_DIR', docs):
                rendered = builder.render_session_card(session, group_mode=False, page_slug='heartsaver')
            self.assertIn('href="' + session['registration_url'] + '"', rendered)
            self.assertNotIn('#ForwardToEnrollware', rendered)
            self.assertIn('Book This Class', rendered)
            (courses / 'heartsaver-first-aid-cpr-aed.html').write_text(rendered, encoding='utf-8')
            with (
                patch.object(audit_sitewide_links, 'ROOT', root),
                patch.object(audit_sitewide_links, 'DOCS_DIR', docs),
                patch.object(audit_sitewide_links, 'DEBUG_DIR', debug),
                patch.object(audit_sitewide_links, 'CSV_PATH', debug / 'links.csv'),
                patch.object(audit_sitewide_links, 'MD_PATH', debug / 'links.md'),
            ):
                self.assertEqual(validate_sitewide_links_strict.main(), 0)

    def test_existing_class_page_keeps_forward_link(self):
        with TemporaryDirectory() as tmp:
            classes = Path(tmp) / 'classes'
            classes.mkdir()
            session = self.session()
            (classes / (session['session_id'] + '.html')).write_text('<span id="ForwardToEnrollware"></span>', encoding='utf-8')
            with patch.object(builder, 'OUTPUT_DIR', Path(tmp)):
                rendered = builder.render_session_card(session, group_mode=False, page_slug='heartsaver')
            self.assertIn('/classes/' + session['session_id'] + '.html#ForwardToEnrollware', rendered)

    def test_existing_session_action_uses_same_missing_page_fallback(self):
        with TemporaryDirectory() as tmp:
            session = self.session()
            with patch.object(builder, 'OUTPUT_DIR', Path(tmp)):
                label, url, original = builder.session_action(session, page_slug='heartsaver')
            self.assertEqual(label, 'Book This Class')
            self.assertEqual(url, session['registration_url'])
            self.assertEqual(original, url)
