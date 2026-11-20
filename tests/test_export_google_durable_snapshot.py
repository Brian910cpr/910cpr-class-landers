import datetime as dt
import io
import json
import unittest

from scripts.export_google_durable_snapshot import (
    EntityExport,
    SnapshotError,
    _content_range_total,
    build_archive,
    fetch_entity,
    verify_archive,
)


class FakeResponse:
    def __init__(self, rows, content_range):
        self._body = json.dumps(rows).encode()
        self.headers = {"Content-Range": content_range}

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class GoogleDurableSnapshotTests(unittest.TestCase):
    def test_content_range_requires_exact_total(self):
        self.assertEqual(_content_range_total("0-4/5"), 5)
        with self.assertRaises(SnapshotError):
            _content_range_total("0-4/*")

    def test_fetch_entity_verifies_total(self):
        opened = []

        def opener(request, timeout):
            opened.append((request.full_url, timeout))
            return FakeResponse([{"id": "a"}, {"id": "b"}], "0-1/2")

        result = fetch_entity("https://example.supabase.co", "secret", "customers", "*", opener)
        self.assertEqual(result.expected_count, 2)
        self.assertEqual(len(result.rows), 2)
        self.assertNotIn("secret", opened[0][0])

    def test_archive_round_trip_is_verified(self):
        exports = [
            EntityExport(name="class_sessions", rows=[{"id": "s1"}], expected_count=1),
            EntityExport(name="registrations", rows=[{"id": "r1"}], expected_count=1),
            EntityExport(name="customers", rows=[{"id": "c1"}], expected_count=1),
        ]
        payload, manifest = build_archive(exports, dt.datetime(2026, 9, 11, tzinfo=dt.timezone.utc))
        verify_archive(payload, manifest)

    def test_zero_core_entity_fails_closed(self):
        exports = [EntityExport(name="class_sessions", rows=[], expected_count=0)]
        with self.assertRaises(SnapshotError):
            build_archive(exports, dt.datetime.now(dt.timezone.utc))

    def test_tampered_archive_fails_verification(self):
        exports = [
            EntityExport(name="class_sessions", rows=[{"id": "s1"}], expected_count=1),
            EntityExport(name="registrations", rows=[{"id": "r1"}], expected_count=1),
            EntityExport(name="customers", rows=[{"id": "c1"}], expected_count=1),
        ]
        payload, manifest = build_archive(exports, dt.datetime.now(dt.timezone.utc))
        tampered = bytearray(payload)
        tampered[-1] ^= 1
        with self.assertRaises(SnapshotError):
            verify_archive(bytes(tampered), manifest)


if __name__ == "__main__":
    unittest.main()
