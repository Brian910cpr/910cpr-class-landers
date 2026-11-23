"""The class directory may be empty without suppressing dynamic course availability."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from scripts import build_index_and_sitemap as catalog
from scripts import refresh_class_finder_index as finder
from scripts import refresh_class_registration_routes as routes
from scripts import refresh_public_class_artifacts as bundle


class ZeroSeatedInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "docs/data/schedule_future.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.other = self.root / "absent_authoritative_report.json"
        self.now = datetime(2026, 11, 20, 14, 30, tzinfo=ZoneInfo("America/New_York"))

    def write_source(self, rows=None, when=None, count=None):
        rows = [] if rows is None else rows
        self.path.write_text(json.dumps({
            "build": {"generated_at": (when or self.now).isoformat(),
                      "counts": {"sessions_output": len(rows) if count is None else count}},
            "sessions": rows,
        }), encoding="utf-8")

    def render(self):
        with patch.object(finder, "SCHEDULE_FUTURE_FILE", self.path), \
             patch.object(finder, "CANONICAL_CLASS_REPORT_FILE", self.other), \
             patch.object(catalog, "SCHEDULE_FUTURE_FILE", self.path), \
             patch.object(catalog, "CANONICAL_CLASS_REPORT_FILE", self.other):
            return finder.render_current_class_finder(self.now)

    def test_public_cards_are_chronological_across_month_boundary(self):
        # A displayed month name is not a sortable timestamp. In production,
        # this placed December cards ahead of upcoming November classes.
        def public_session(session_id, starts_at):
            return {
                "session_id": session_id,
                "course_id": "209806",
                "course_number": "209806",
                "course_name": "AHA BLS Provider (Initial)",
                "start_at": starts_at,
                "location_name": ":: Wilmington; Shipyard Blvd - B",
                "session_status": "active",
                "registration_status": "open",
                "public_direct_booking": True,
                "registration_url": (
                    "https://coastalcprtraining.enrollware.com/enroll?id="
                    + session_id
                ),
            }

        self.write_source([
            public_session("15000102", "2026-12-01T09:00:00-05:00"),
            public_session("15000101", "2026-11-21T09:00:00-05:00"),
        ])
        html, ids = self.render()
        self.assertEqual(ids, {"15000101", "15000102"})
        self.assertLess(
            html.index('href="/classes/15000101.html"'),
            html.index('href="/classes/15000102.html"'),
        )

    def test_stale_linked_legacy_mirrors_are_not_public_classes(self):
        # A fresh iCal file can still carry an old canonical reconciliation.
        # Location prefix and an inherited external URL do not make it public.
        def legacy_row(sid, **extra):
            return {
                "session_id": sid,
                "course_id": "209806",
                "course_number": "209806",
                "course_name": "AHA BLS Provider (Initial)",
                "start_at": "2026-11-22T13:00:00-05:00",
                "location_name": ":: Wilmington; Shipyard Blvd - B",
                "session_status": "active",
                "registration_status": "open",
                "public_direct_booking": True,
                "registration_url": (
                    "https://coastalcprtraining.enrollware.com/enroll?id=" + sid
                ),
                **extra,
            }

        self.write_source([
            legacy_row("15000101", canonical_session_id="private-mirror",
                       demand_status="stale_reconciliation"),
            legacy_row("15000102", visibility="unlisted"),
            legacy_row("15000103"),
            legacy_row("15000104", canonical_session_id="unresolved-link",
                       demand_status="external_reconciliation_required"),
            legacy_row("15000105", canonical_session_id="confirmed-public",
                       demand_status="current", visibility="public"),
            legacy_row("15000106", canonical_session_id="moved-link",
                       demand_status="stale_anchor"),
        ])
        html, ids = self.render()
        self.assertEqual(ids, {"15000103", "15000104", "15000105"})
        self.assertNotIn("/classes/15000101.html", html)
        self.assertNotIn("/classes/15000102.html", html)
        self.assertIn("/classes/15000103.html", html)

    def test_recent_valid_zero_inventory_renders_no_phantom_class(self):
        self.write_source()
        html, ids = self.render()
        self.assertEqual(ids, set())
        self.assertIn("0 classes found", html)
        self.assertNotIn('class="class-finder-card', html)
        self.assertNotIn('class="class-finder-primary"', html)
        self.assertIn("/classes/index.html", html)

    def test_private_only_source_is_not_a_public_class(self):
        self.write_source([{"session_id": "private-1", "start_at": "2026-11-21T12:00:00-05:00",
                            "location_name": "Private offsite appointment",
                            "session_status": "active"}])
        html, ids = self.render()
        self.assertEqual(ids, set())
        self.assertNotIn("private-1", html)

    def test_missing_stale_corrupt_and_incoherent_source_cannot_erase_finder(self):
        cases = ["missing", "stale", "unzonened", "corrupt", "count"]
        for case in cases:
            with self.subTest(case=case):
                if self.path.exists():
                    self.path.unlink()
                if case == "stale":
                    self.write_source(when=self.now - timedelta(hours=3))
                if case == "unzonened":
                    self.path.write_text(json.dumps({"build": {"generated_at": "2026-11-20T14:30:00"}, "sessions": []}))
                if case == "corrupt":
                    self.path.write_text('{"build":', encoding="utf-8")
                if case == "count":
                    self.write_source(count=3)
                with self.assertRaises(ValueError):
                    self.render()

    def test_corrupt_canonical_report_cannot_resurrect_legacy_public_cards(self):
        # A malformed authoritative report previously caused BOTH source
        # selectors to fall back to a fresh but potentially privacy-stale iCal
        # feed. The class finder and direct route must fail closed together.
        self.write_source([{
            "session_id": "15000109", "course_id": "209806",
            "course_number": "209806", "course_name": "AHA BLS Provider",
            "start_at": "2026-11-22T13:00:00-05:00",
            "location_name": ":: Wilmington; Shipyard Blvd - B",
            "session_status": "active", "registration_status": "open",
            "public_direct_booking": True,
            "registration_url": "https://coastalcprtraining.enrollware.com/enroll?id=15000109",
        }])
        self.assertEqual(self.render()[1], {"15000109"})
        for corrupt in ('{"build":', '{"sessions": []}', '[]'):
            with self.subTest(corrupt=corrupt):
                self.other.write_text(corrupt, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Canonical class report"):
                    self.render()
                with (
                    patch.object(catalog, "SCHEDULE_FUTURE_FILE", self.path),
                    patch.object(catalog, "CANONICAL_CLASS_REPORT_FILE", self.other),
                ):
                    with self.assertRaisesRegex(ValueError, "Canonical class report"):
                        catalog.load_schedule_future_sessions()

    def test_nonempty_finder_cannot_publish_from_stale_or_missing_snapshot(self):
        # A plausible, future-facing class is NOT proof that its source is fresh.
        card = {"session_id": "15000001", "display_date": "November 21, 2026"}
        html = '<a class="class-finder-secondary" href="/classes/15000001.html">Details</a>'
        future_row = {"_parsed_start": self.now + timedelta(days=1)}
        with (
            patch.object(finder, "load_schedule_future_sessions", return_value=[future_row]),
            patch.object(finder, "schedule_future_to_public_session", return_value=card),
            patch.object(finder, "render_classes_finder_index", return_value=html),
        ):
            self.write_source()
            self.assertEqual(self.render()[1], {"15000001"})
            self.write_source(when=self.now - timedelta(hours=3))
            with self.assertRaisesRegex(ValueError, "Unverified zero-class source"):
                self.render()
            self.path.unlink()
            with self.assertRaisesRegex(ValueError, "Unverified zero-class source"):
                self.render()

    def test_routes_use_same_authoritative_source_as_public_finder(self):
        # The finder may select the canonical class report, while the fallback
        # schedule contains different class IDs. Route rewriting must never
        # silently attach a public card to the fallback's class data.
        clock = datetime.now(ZoneInfo("America/New_York"))
        start = (clock + timedelta(days=2)).replace(minute=0, second=0, microsecond=0)
        def row(sid):
            return {
                "session_id": sid,
                "course_id": "209806",
                "course_number": "209806",
                "course_name": "AHA BLS Provider (Initial)",
                "start_at": start.isoformat(),
                "location_name": ":: Wilmington; Shipyard Blvd - B",
                "session_status": "active",
                "registration_status": "open",
                "public_direct_booking": True,
                "registration_url": (
                    "https://coastalcprtraining.enrollware.com/enroll?id=" + sid
                ),
            }

        fallback_id, authoritative_id = "15000101", "15000102"
        self.write_source([row(fallback_id)], when=clock)
        report_path = self.root / "docs/data/canonical_schedule_from_class_report.json"
        report_path.write_text(json.dumps({
            "build": {
                "source_mode": "class_report_authoritative",
                "generated_at": clock.isoformat(),
                "counts": {"sessions_output": 1},
            },
            "sessions": [row(authoritative_id)],
        }), encoding="utf-8")
        index = self.root / "docs/classes/index.html"
        index.parent.mkdir(parents=True, exist_ok=True)
        detail = self.root / "docs/classes" / (authoritative_id + ".html")
        detail.write_text('<div class="cta-panel"><p class="cta-panel-label">Details</p>'
                          '<p class="cta-panel-copy">Request</p>'
                          '<div class="cta-row"><a class="button primary" '
                          'href="/classes/">More</a></div></div>', encoding="utf-8")

        with (
            patch.object(finder, "SCHEDULE_FUTURE_FILE", self.path),
            patch.object(finder, "CANONICAL_CLASS_REPORT_FILE", report_path),
            patch.object(catalog, "SCHEDULE_FUTURE_FILE", self.path),
            patch.object(catalog, "CANONICAL_CLASS_REPORT_FILE", report_path),
        ):
            html, ids = finder.render_current_class_finder(clock)
            self.assertEqual(ids, {authoritative_id})
            index.write_text(html, encoding="utf-8")
            result = routes.refresh(root=self.root)
            self.assertEqual(result["listed"], 1)
            self.assertEqual(result["files"], 2)

            # A stale/fallback ID accidentally left in the index must fail
            # before rewriting or committing any card or detail.
            mismatched = html.replace(
                "/classes/" + authoritative_id + ".html",
                "/classes/" + fallback_id + ".html",
            )
            index.write_text(mismatched, encoding="utf-8")
            before = detail.read_bytes()
            with self.assertRaisesRegex(ValueError, "mismatches current eligible source"):
                routes.refresh(root=self.root)
            self.assertEqual(detail.read_bytes(), before)

    def test_hidden_legacy_detail_pages_are_retired_without_erasing_public_inventory(self):
        # Previously generated numeric pages remain directly reachable after a
        # card disappears from the index. They must not publish unlisted times
        # or stale Enrollware routes, even when the card itself is hidden.
        def row(sid, **extra):
            return {
                "session_id": sid,
                "course_id": "209806",
                "course_number": "209806",
                "course_name": "AHA BLS Provider (Initial)",
                "start_at": "2026-11-22T13:00:00-05:00",
                "location_name": ":: Wilmington; Shipyard Blvd - B",
                "session_status": "active",
                "registration_status": "open",
                "public_direct_booking": True,
                "registration_url": (
                    "https://coastalcprtraining.enrollware.com/enroll?id=" + sid
                ),
                **extra,
            }

        stale, unlisted, public, unrelated, offsite = (
            "15000101", "15000102", "15000103", "15000104", "15000106"
        )
        self.write_source([
            row(stale, canonical_session_id="simulated-private-mirror",
                demand_status="stale_reconciliation"),
            row(unlisted, visibility="unlisted"),
            # A private-location row is filtered from ordinary class-card
            # loading; its old numeric detail page must STILL be retired.
            row(offsite, location_name="Private workplace appointment",
                visibility="private"),
            row(public),
        ])
        index = self.root / "docs/classes/index.html"
        index.parent.mkdir(parents=True, exist_ok=True)
        index_html = (
            '<a class="class-finder-secondary" href="/classes/' + public
            + '.html">Details</a>'
        )
        index.write_text(index_html, encoding="utf-8")
        for sid in (stale, unlisted, offsite, public):
            (index.parent / (sid + ".html")).write_text(
                'Confidential source class detail ' + sid
                + ' https://coastalcprtraining.enrollware.com/enroll?id=' + sid,
                encoding="utf-8",
            )
        unrelated_detail = index.parent / (unrelated + ".html")
        unrelated_detail.write_text("unrelated historic page", encoding="utf-8")
        with (
            patch.object(finder, "render_current_class_finder",
                         return_value=(index_html, {public})),
            patch.object(catalog, "SCHEDULE_FUTURE_FILE", self.path),
            patch.object(catalog, "CANONICAL_CLASS_REPORT_FILE", self.other),
        ):
            result = routes.refresh(root=self.root)
        self.assertEqual(result, {"listed": 1, "files": 5})
        for sid in (stale, unlisted, offsite):
            redacted = (index.parent / (sid + ".html")).read_text(encoding="utf-8")
            self.assertIn('name="robots" content="noindex,nofollow"', redacted)
            self.assertIn("Browse current classes", redacted)
            self.assertNotIn("Confidential source class detail", redacted)
            self.assertNotIn(sid, redacted)
            self.assertNotIn("enrollware.com", redacted)
        self.assertIn("Confidential source class detail",
                      (index.parent / (public + ".html")).read_text(encoding="utf-8"))
        self.assertEqual(unrelated_detail.read_text(encoding="utf-8"),
                         "unrelated historic page")

    def test_verified_empty_finder_still_retires_known_nonpublic_detail(self):
        private_id = "15000105"
        self.write_source([{
            "session_id": private_id,
            "start_at": "2026-11-22T13:00:00-05:00",
            "location_name": ":: Wilmington; Shipyard Blvd - B",
            "visibility": "private",
        }])
        index = self.root / "docs/classes/index.html"
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text("0 classes found", encoding="utf-8")
        detail = index.parent / (private_id + ".html")
        detail.write_text("Old private session advert", encoding="utf-8")
        with (
            patch.object(finder, "render_current_class_finder",
                         return_value=("0 classes found", set())),
            patch.object(catalog, "SCHEDULE_FUTURE_FILE", self.path),
            patch.object(catalog, "CANONICAL_CLASS_REPORT_FILE", self.other),
        ):
            result = routes.refresh(root=self.root)
        self.assertEqual(result, {"listed": 0, "files": 1})
        self.assertIn("not publicly listed", detail.read_text(encoding="utf-8"))
        self.assertNotIn("Old private session advert",
                         detail.read_text(encoding="utf-8"))

    def test_safe_route_refresh_accepts_only_verified_empty_finder(self):
        self.write_source()
        html, ids = self.render()
        index = self.root / "docs/classes/index.html"
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text(html, encoding="utf-8")
        with patch.object(finder, "render_current_class_finder", return_value=(html, ids)):
            result = routes.refresh(root=self.root)
        self.assertEqual(result, {"listed": 0, "files": 0})
        self.assertEqual(index.read_text(encoding="utf-8"), html)

        with patch.object(finder, "render_current_class_finder", return_value=(html, {"9876"})):
            with self.assertRaisesRegex(ValueError, "mismatches"):
                routes.refresh(root=self.root)

        index.write_text(html + '<article class="class-finder-card">phantom</article>', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unexpected class cards"):
            routes.refresh(root=self.root)


    def test_source_absent_tombstone_refresh_scrubs_sitemap_and_archive(self):
        # A prior private detail may outlive its source row. The guarded
        # publisher must repair any remaining discovery URL, not leave the
        # next scheduled refresh failing on the same sitemap indefinitely.
        self.write_source()
        index = self.root / "docs/classes/index.html"
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text("0 classes found", encoding="utf-8")
        tombstone = index.parent / "333.html"
        tombstone.write_text(
            '<meta name="robots" content="noindex,nofollow">'
            '<h1>This class is not publicly listed</h1>', encoding="utf-8",
        )
        sitemap = self.root / "docs/sitemap.xml"
        sitemap.write_text(
            '<urlset>\\n'
            '<url><loc>https://www.910cpr.com/classes/333.html</loc></url>\\n'
            '<url><loc>https://www.910cpr.com/classes/444.html</loc></url>\\n'
            '<url><loc>https://www.910cpr.com/bls.html</loc></url>\\n'
            '</urlset>\\n', encoding="utf-8",
        )
        archive = self.root / "docs/topics/bls.html"
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_text(
            '<article><p>Private appointment date</p>'
            '<a href="/classes/333.html">Old detail</a></article>'
            '<article><a href="/classes/444.html">Unrelated public archive</a></article>',
            encoding="utf-8",
        )
        with (
            patch.object(finder, "render_current_class_finder",
                         return_value=("0 classes found", set())),
            patch.object(catalog, "SCHEDULE_FUTURE_FILE", self.path),
            patch.object(catalog, "CANONICAL_CLASS_REPORT_FILE", self.other),
        ):
            result = routes.refresh(root=self.root)
        self.assertEqual(result, {"listed": 0, "files": 2})
        self.assertNotIn("/classes/333.html", sitemap.read_text(encoding="utf-8"))
        self.assertIn("/classes/444.html", sitemap.read_text(encoding="utf-8"))
        self.assertIn("/bls.html", sitemap.read_text(encoding="utf-8"))
        updated_archive = archive.read_text(encoding="utf-8")
        self.assertNotIn("Private appointment date", updated_archive)
        self.assertNotIn("/classes/333.html", updated_archive)
        self.assertIn("/classes/444.html", updated_archive)
        self.assertIn("not publicly listed", tombstone.read_text(encoding="utf-8"))


    def test_sitemap_drops_verified_unlisted_class_without_erasing_other_urls(self):
        # A numeric detail tombstone is not enough if sitemap discovery still
        # points search engines directly at the formerly private class.
        private_id, historical_id = "15000107", "15000108"
        self.write_source([{
            "session_id": private_id,
            "start_at": "2026-11-22T13:00:00-05:00",
            "location_name": ":: Wilmington; Shipyard Blvd - B",
            "session_status": "active",
            "visibility": "unlisted",
        }])
        index = self.root / "docs/classes/index.html"
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text("0 classes found", encoding="utf-8")
        sitemap = self.root / "docs/sitemap.xml"
        original = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            '  <url><loc>https://www.910cpr.com/classes/' + private_id + '.html</loc></url>\n'
            '  <url><loc>https://www.910cpr.com/classes/' + historical_id + '.html</loc></url>\n'
            '  <url><loc>https://www.910cpr.com/bls.html</loc></url>\n'
            '</urlset>\n'
        )
        sitemap.write_text(original, encoding="utf-8")
        with (
            patch.object(finder, "render_current_class_finder",
                         return_value=("0 classes found", set())),
            patch.object(catalog, "SCHEDULE_FUTURE_FILE", self.path),
            patch.object(catalog, "CANONICAL_CLASS_REPORT_FILE", self.other),
        ):
            result = routes.refresh(root=self.root)
        self.assertEqual(result, {"listed": 0, "files": 1})
        updated = sitemap.read_text(encoding="utf-8")
        self.assertNotIn("/classes/" + private_id + ".html", updated)
        self.assertIn("/classes/" + historical_id + ".html", updated)
        self.assertIn("https://www.910cpr.com/bls.html", updated)
        self.assertEqual(index.read_text(encoding="utf-8"), "0 classes found")



    def test_private_uuid_detail_is_retired_without_touching_historical_pages(self):
        # Canonical appointment UUID routes require the same retirement and
        # sitemap privacy behavior as numeric Enrollware details.
        sid = "22222222-2222-4222-8222-222222222222"
        historic = "12345678"
        self.write_source([{
            "session_id": sid, "start_at": "2026-11-22T13:00:00-05:00",
            "location_name": ":: Wilmington; Shipyard Blvd - B",
            "session_status": "active", "visibility": "private",
        }])
        index = self.root / "docs/classes/index.html"
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text("0 classes found", encoding="utf-8")
        direct = index.parent / (sid + ".html")
        direct.write_text("Private time and enrollment", encoding="utf-8")
        archive = index.parent / (historic + ".html")
        archive.write_text("Historical archive", encoding="utf-8")
        sitemap = self.root / "docs/sitemap.xml"
        sitemap.write_text(
            "<urlset>\n"
            "  <url><loc>https://www.910cpr.com/classes/" + sid + ".html</loc></url>\n"
            "  <url><loc>https://www.910cpr.com/classes/" + historic + ".html</loc></url>\n"
            "</urlset>\n", encoding="utf-8",
        )
        with (
            patch.object(finder, "render_current_class_finder",
                         return_value=("0 classes found", set())),
            patch.object(catalog, "SCHEDULE_FUTURE_FILE", self.path),
            patch.object(catalog, "CANONICAL_CLASS_REPORT_FILE", self.other),
        ):
            result = routes.refresh(root=self.root)
        self.assertEqual(result["files"], 2)
        self.assertIn("noindex,nofollow", direct.read_text(encoding="utf-8"))
        self.assertNotIn("Private time", direct.read_text(encoding="utf-8"))
        self.assertNotIn(sid, sitemap.read_text(encoding="utf-8"))
        self.assertIn(historic, sitemap.read_text(encoding="utf-8"))
        self.assertEqual(archive.read_text(encoding="utf-8"), "Historical archive")

    def test_bundle_restores_uuid_detail_after_partial_route_failure(self):
        sid = "22222222-2222-4222-8222-222222222222"
        index = self.root / "docs/classes/index.html"
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text("Original finder", encoding="utf-8")
        direct = index.parent / (sid + ".html")
        direct.write_text("Original private UUID detail", encoding="utf-8")
        def failed_routes(**kwargs):
            direct.write_text("Partial private tombstone", encoding="utf-8")
            raise OSError("injected route failure")
        with (
            patch.object(bundle.finder, "render_current_class_finder",
                         return_value=("0 classes found", set())),
            patch.object(bundle.routes, "refresh", side_effect=failed_routes),
        ):
            with self.assertRaisesRegex(OSError, "injected route failure"):
                bundle.refresh(root=self.root)
        self.assertEqual(index.read_text(encoding="utf-8"), "Original finder")
        self.assertEqual(direct.read_text(encoding="utf-8"), "Original private UUID detail")

    def test_absent_expired_previous_card_tombstones_detail_and_sitemap(self):
        # Missing from the current source is distinct from a currently present
        # explicitly private row. Only previously PUBLICLY LISTED IDs may be
        # retired on this basis; untouched historical pages must remain intact.
        old_id, historic_id = "14917169", "12345678"
        self.write_source([])
        index = self.root / "docs/classes/index.html"
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text("0 classes found", encoding="utf-8")
        old = index.parent / (old_id + ".html")
        old.write_text("Old published class date and registration", encoding="utf-8")
        historic = index.parent / (historic_id + ".html")
        historic.write_text("Historical archive", encoding="utf-8")
        sitemap = self.root / "docs/sitemap.xml"
        sitemap.write_text(
            "<urlset>\n"
            "  <url><loc>https://www.910cpr.com/classes/" + old_id + ".html</loc></url>\n"
            "  <url><loc>https://www.910cpr.com/classes/" + historic_id + ".html</loc></url>\n"
            "</urlset>\n",
            encoding="utf-8",
        )
        with (
            patch.object(finder, "render_current_class_finder",
                         return_value=("0 classes found", set())),
            patch.object(catalog, "SCHEDULE_FUTURE_FILE", self.path),
            patch.object(catalog, "CANONICAL_CLASS_REPORT_FILE", self.other),
        ):
            result = routes.refresh(root=self.root, retired_previous_ids={old_id})
        self.assertEqual(result["listed"], 0)
        self.assertEqual(result["files"], 2)
        self.assertIn("noindex,nofollow", old.read_text(encoding="utf-8"))
        self.assertNotIn("Old published class date", old.read_text(encoding="utf-8"))
        self.assertNotIn(old_id, sitemap.read_text(encoding="utf-8"))
        self.assertIn(historic_id, sitemap.read_text(encoding="utf-8"))
        self.assertEqual(historic.read_text(encoding="utf-8"), "Historical archive")

    def test_same_id_stale_finder_content_cannot_rewrite_public_routes(self):
        # ID-only reconciliation misses a reschedule, course change or a
        # stale/wrong Register action retaining the same numeric class ID.
        # Keep ALL public discovery surfaces unchanged if any differs from
        # the freshly validated, same-source finder.
        sid = "15000999"
        index = self.root / "docs/classes/index.html"
        index.parent.mkdir(parents=True, exist_ok=True)
        initial = (
            '<article class="class-finder-card">'
            '<span>December 07, 2026 | 5:30 PM | BLS Renewal</span>'
            '<a class="class-finder-primary" href="/register/?session=' + sid + '">Register</a>'
            '<a class="class-finder-secondary" href="/classes/' + sid + '.html">Details</a>'
            '</article>'
        )
        index.write_text(initial, encoding="utf-8")
        detail = index.parent / (sid + ".html")
        detail.write_text("Existing public class detail", encoding="utf-8")
        sitemap = self.root / "docs/sitemap.xml"
        sitemap.write_text("<urlset><url><loc>https://www.910cpr.com/classes/" +
                           sid + ".html</loc></url></urlset>", encoding="utf-8")
        for changed in (
            initial.replace("5:30 PM", "2:00 PM"),
            initial.replace("BLS Renewal", "Heartsaver CPR AED"),
            initial.replace("/register/?session=" + sid,
                            "/register/?session=other"),
        ):
            with self.subTest(changed=changed):
                with patch.object(finder, "render_current_class_finder",
                                  return_value=(changed, {sid})):
                    with self.assertRaisesRegex(
                            ValueError, "listing content mismatches"):
                        routes.refresh(root=self.root)
                self.assertEqual(index.read_text(encoding="utf-8"), initial)
                self.assertEqual(detail.read_text(encoding="utf-8"),
                                 "Existing public class detail")
                self.assertIn(sid, sitemap.read_text(encoding="utf-8"))

    def test_bundle_passes_removed_public_ids_before_rewriting_routes(self):
        old_id = "14917169"
        index = self.root / "docs/classes/index.html"
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text(
            '<a class="class-finder-secondary" href="/classes/' +
            old_id + '.html">Details</a>', encoding="utf-8")
        with (
            patch.object(bundle.finder, "render_current_class_finder",
                         return_value=("0 classes found", set())),
            patch.object(bundle.routes, "refresh",
                         return_value={"listed": 0, "files": 1}) as rewriter,
        ):
            result = bundle.refresh(root=self.root)
        rewriter.assert_called_once_with(
            root=self.root, retired_previous_ids={old_id})
        self.assertEqual(result["retired_previous"], 1)
        self.assertEqual(index.read_text(encoding="utf-8"), "0 classes found")

    def test_bundle_restores_finder_on_unverified_route_failure(self):
        index = self.root / "docs/classes/index.html"
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text("original listing", encoding="utf-8")
        with (
            patch.object(bundle.finder, "render_current_class_finder",
                         return_value=("0 classes found", set())),
            patch.object(bundle.routes, "refresh",
                         side_effect=ValueError("source changed")),
        ):
            with self.assertRaisesRegex(ValueError, "source changed"):
                bundle.refresh(root=self.root)
        self.assertEqual(index.read_text(encoding="utf-8"), "original listing")


    def test_bundle_rolls_back_partial_detail_and_sitemap_writes(self):
        # A successful finder update followed by a failed detail/sitemap write
        # must not leave mixed public artifacts in the runner or next commit.
        old_id, archive_id = "14917169", "12345678"
        index = self.root / "docs/classes/index.html"
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text(
            '<a class="class-finder-secondary" href="/classes/' +
            old_id + '.html">Details</a>', encoding="utf-8")
        detail = index.parent / (old_id + ".html")
        archive = index.parent / (archive_id + ".html")
        sitemap = self.root / "docs/sitemap.xml"
        detail.write_text("original public class detail", encoding="utf-8")
        archive.write_text("unrelated historical archive", encoding="utf-8")
        sitemap.write_text(
            "<urlset><url><loc>https://www.910cpr.com/classes/" +
            old_id + ".html</loc></url></urlset>", encoding="utf-8")
        originals = {path: path.read_bytes()
                     for path in (index, detail, archive, sitemap)}

        def fail_after_partial_write(*, root, retired_previous_ids):
            self.assertEqual(retired_previous_ids, {old_id})
            detail.write_text("partially rewritten route", encoding="utf-8")
            sitemap.write_text("<urlset>partial</urlset>", encoding="utf-8")
            raise OSError("simulated route write failure")

        with (
            patch.object(bundle.finder, "render_current_class_finder",
                         return_value=("0 classes found", set())),
            patch.object(bundle.routes, "refresh",
                         side_effect=fail_after_partial_write),
        ):
            with self.assertRaisesRegex(OSError, "route write failure"):
                bundle.refresh(root=self.root)
        for path, original in originals.items():
            self.assertEqual(path.read_bytes(), original,
                             f"Public bundle left a partial artifact: {path.name}")


    def test_private_archive_card_is_removed_but_public_neighbors_remain(self):
        # An old topic index must not disclose the private date after its
        # direct detail has been redacted. Preserve distinct public history.
        self.write_source()
        classes = self.root / "docs/classes"
        classes.mkdir(parents=True, exist_ok=True)
        (classes / "index.html").write_text("0 classes found", encoding="utf-8")
        (classes / "222.html").write_text(
            '<meta name="robots" content="noindex,nofollow">'
            '<h1>This class is not publicly listed</h1>',
            encoding="utf-8",
        )
        archive = self.root / "docs/topics/bls.html"
        archive.parent.mkdir(parents=True)
        archive.write_text(
            '<main><article><h2>Confidential appointment on Tuesday</h2>'
            '<a href="/classes/222.html">Private class</a></article>'
            '<article><h2>Historic public class</h2>'
            '<a href="/classes/444.html">Old public listing</a></article>'
            '<ul><li><a href="/classes/222.html">Private December time</a></li>'
            '<li><a href="/classes/444.html">Unrelated historical item</a></li></ul>'
            '</main>', encoding="utf-8",
        )
        with (
            patch.object(finder, "render_current_class_finder",
                         return_value=("0 classes found", set())),
            patch.object(catalog, "SCHEDULE_FUTURE_FILE", self.path),
            patch.object(catalog, "CANONICAL_CLASS_REPORT_FILE", self.other),
        ):
            result = routes.refresh(root=self.root)
        output = archive.read_text(encoding="utf-8")
        self.assertEqual(result["listed"], 0)
        self.assertIn("Historic public class", output)
        self.assertIn("/classes/444.html", output)
        self.assertNotIn("Confidential appointment", output)
        self.assertNotIn("Private December time", output)
        self.assertNotIn("/classes/222.html", output)

    def test_compound_archive_card_fails_closed_without_rewriting(self):
        self.write_source()
        classes = self.root / "docs/classes"
        classes.mkdir(parents=True, exist_ok=True)
        index = classes / "index.html"
        index.write_text("0 classes found", encoding="utf-8")
        (classes / "222.html").write_text(
            '<meta name="robots" content="noindex,nofollow">'
            '<h1>This class is not publicly listed</h1>', encoding="utf-8",
        )
        archive = self.root / "docs/topics/bls.html"
        archive.parent.mkdir(parents=True)
        original = (
            '<article><h2>Mixed unverified class grouping</h2>'
            '<a href="/classes/222.html">Private</a>'
            '<a href="/classes/444.html">Public</a></article>'
        )
        archive.write_text(original, encoding="utf-8")
        with (
            patch.object(finder, "render_current_class_finder",
                         return_value=("0 classes found", set())),
            patch.object(catalog, "SCHEDULE_FUTURE_FILE", self.path),
            patch.object(catalog, "CANONICAL_CLASS_REPORT_FILE", self.other),
        ):
            with self.assertRaisesRegex(ValueError, "compound archived card"):
                routes.refresh(root=self.root)
        self.assertEqual(archive.read_text(encoding="utf-8"), original)
        self.assertEqual(index.read_text(encoding="utf-8"), "0 classes found")

    def test_unstructured_archive_private_reference_fails_closed(self):
        self.write_source()
        classes = self.root / "docs/classes"
        classes.mkdir(parents=True, exist_ok=True)
        index = classes / "index.html"
        index.write_text("0 classes found", encoding="utf-8")
        (classes / "222.html").write_text(
            '<meta name="robots" content="noindex,nofollow">'
            '<h1>This class is not publicly listed</h1>', encoding="utf-8",
        )
        archive = self.root / "docs/topics/bls.html"
        archive.parent.mkdir(parents=True)
        original = '<aside><a href="/classes/222.html">Private date</a></aside>'
        archive.write_text(original, encoding="utf-8")
        with (
            patch.object(finder, "render_current_class_finder",
                         return_value=("0 classes found", set())),
            patch.object(catalog, "SCHEDULE_FUTURE_FILE", self.path),
            patch.object(catalog, "CANONICAL_CLASS_REPORT_FILE", self.other),
        ):
            with self.assertRaisesRegex(ValueError, "ambiguous archived reference"):
                routes.refresh(root=self.root)
        self.assertEqual(archive.read_text(encoding="utf-8"), original)
        self.assertEqual(index.read_text(encoding="utf-8"), "0 classes found")

    def test_bundle_restores_archive_after_mid_publish_failure(self):
        classes = self.root / "docs/classes"
        classes.mkdir(parents=True, exist_ok=True)
        index = classes / "index.html"
        index.write_text("Original finder", encoding="utf-8")
        archive = self.root / "docs/topics/bls.html"
        archive.parent.mkdir(parents=True)
        archive.write_text("Original archive card", encoding="utf-8")
        def broken_refresh(*, root, retired_previous_ids):
            archive.write_text("Partial archived privacy scrub", encoding="utf-8")
            raise OSError("injected archive write failure")
        with (
            patch.object(bundle.finder, "render_current_class_finder",
                         return_value=("0 classes found", set())),
            patch.object(bundle.routes, "refresh", side_effect=broken_refresh),
        ):
            with self.assertRaisesRegex(OSError, "archive write failure"):
                bundle.refresh(root=self.root)
        self.assertEqual(index.read_text(encoding="utf-8"), "Original finder")
        self.assertEqual(archive.read_text(encoding="utf-8"), "Original archive card")


if __name__ == "__main__":
    unittest.main()
