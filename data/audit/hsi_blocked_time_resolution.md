# HSI blocked-time resolution

- Artifact: `docs/data/block-selector-availability/hsi.json`
- Schema: `selector-resolved-availability.v1`
- HSI offers after repair: 1160
- Offer count by course ID: {'445670': 588, '463743': 572}
- Non-`::` public HSI locations: 0
- Static appointment URLs remaining in `docs/hsi.html`: 0
- Rejection reason counts: {'outside_public_dynamic_hours': 1780, 'conflicts_with_existing_enrollware_occupancy': 720, 'does_not_fit_inside_availability_after_duration_and_buffers': 125, 'inside_minimum_lead_time': 8}
- Blocked-window 2026-07-04 5:45/6:00/6:15 PM offers: 0

The schedule page fetches `selector-resolved-availability.v1` with `cache: 'no-store'`, renders `Checking current class times…` before fetch completion, and does not embed static appointment URLs in HTML.
