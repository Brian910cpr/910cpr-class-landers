import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/linkedin_event_sync.py"
SPEC = importlib.util.spec_from_file_location("linkedin_event_sync", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


CONFIG = {
    "organizer_urn": "urn:li:organization:123",
    "background_image_urn": "urn:li:digitalmediaAsset:456",
    "public_location_prefixes": ["::"],
    "promoted_session_ids": [],
    "course_images": {"209806": "docs/images/zoom-bls-aha.png"},
    "location_addresses": {
        ":: Wilmington; Shipyard Blvd": {
            "line1": "4018 Shipyard Blvd",
            "city": "Wilmington",
            "geographicArea": "North Carolina",
            "postalCode": "28403",
            "country": "US",
        }
    },
}


def session(**overrides):
    base = {
        "session_id": "99",
        "course_id": "209806",
        "course_name": "AHA BLS Provider",
        "mapped_clean_title": "AHA BLS Provider",
        "mapped_short_description": "Hands-on BLS training.",
        "start_at": "2099-08-10T09:00:00-04:00",
        "end_at": "2099-08-10T12:00:00-04:00",
        "build_classification": "future",
        "session_status": "active",
        "registration_status": "open",
        "public_direct_booking": True,
        "is_full": False,
        "location_display": ":: Wilmington; Shipyard Blvd - B",
        "registration_url": "https://example.test/enroll?id=99",
    }
    base.update(overrides)
    return base


def test_public_seated_session_is_eligible():
    assert MODULE.eligible(session(), CONFIG) == (True, "public seated class")


def test_private_location_is_not_eligible():
    ok, reason = MODULE.eligible(session(location_display="Private Client"), CONFIG)
    assert not ok
    assert reason == "private location"


def test_payload_uses_session_times_registration_and_address():
    event = MODULE.build_event(session(), CONFIG)
    assert event.payload["organizer"] == "urn:li:organization:123"
    assert event.payload["type"]["inPerson"]["url"].endswith("id=99")
    assert event.payload["type"]["inPerson"]["address"]["line1"] == "4018 Shipyard Blvd"
    assert event.payload["backgroundImage"] == "urn:li:digitalmediaAsset:456"
    assert event.image_path == "docs/images/zoom-bls-aha.png"


def test_remote_event_registration_url_is_detected():
    remote = {"type": {"inPerson": {"url": "https://example.test/enroll?id=99"}}}
    assert MODULE.event_registration_url(remote).endswith("id=99")


def test_promoted_session_can_override_nonpublic_flag_but_not_location_mapping():
    config = {**CONFIG, "promoted_session_ids": ["99"]}
    assert MODULE.eligible(session(public_direct_booking=False), config)[0]
    ok, reason = MODULE.eligible(
        session(public_direct_booking=False, location_display="Private Client"), config
    )
    assert not ok
    assert reason == "unmapped public address"
