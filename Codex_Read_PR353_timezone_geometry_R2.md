# PR353 timezone geometry repair

The external occupancy parser now converts offset-bearing timestamps to America/New_York before removing timezone metadata for the existing local-clock contract. Naive local inputs remain unchanged.

Regression verifies equivalent native local and externally prefixed UTC representations yield one occupied interval, one seated anchor, and only legitimate 11:00/13:00 skills edges around a 12:00 booking. Winter and DST conversions tested.

Validation: 69 targeted adapter, generic-normalizer, room-alias, publication and cache tests passed. Actual-source probe pending after push. No booking changes, no secrets accessed, no merge/activation/deployment. The existing release hold remains respected. Other catalog and explicit-availability acceptance questions remain open.

Changed: scripts/generate_dynamic_offers.py; tests/test_layered_selector_adapter.py.
