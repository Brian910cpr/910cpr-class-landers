# HSI blocked-time publication trace

## Root cause

HSI hub rendered static appointment offers from the legacy slug-hub dynamic-offer presentation path instead of the selector-resolved availability authority. That path consumed public_sellable_offers_preview/dynamic_offer_presentation_policy and embedded appointment URLs in docs/hsi.html.

## Old generator path

- data/audit/live_availability_snapshot_preview.json
- scripts/generate_dynamic_offers.py -> data/runtime/audit_previews/dynamic_offers_preview.json
- scripts/filter_public_sellable_offers.py -> data/runtime/audit_previews/public_sellable_offers_preview.json
- scripts/dynamic_offer_presentation_policy.py -> data/audit/dynamic_offer_presentation_policy_report.json
- scripts/build_slug_hubs.py -> docs/hsi.html static appointment cards

## New authority path

- data/audit/live_availability_snapshot_preview.json
- data/sessions_current.json + docs/data/schedule_future.json + blocked live-calendar intervals as occupancy
- data/inventory/course_consumption_rules.json
- scripts/block_start_time_selector.py
- scripts/build_deployed_selector_pages.py
- docs/data/block-selector-availability/hsi.json
- docs/hsi-schedule.html browser fetch with cache no-store and fail-closed shell

## Counts

- Legacy public-sellable HSI offers: 17
- Legacy rendered HSI offers: 7
- New selector HSI offers: 1107
- New HSI course IDs: {'463743': 519, '445670': 588}

## Where the blocked interval was lost

scripts/build_slug_hubs.py consumed render_offers from dynamic_offer_presentation_policy and wrote static HSI appointment cards. HSI was not in scripts.build_deployed_selector_pages.DEPLOYED_SELECTOR_PAGE_KEYS, so it did not use selector-resolved-availability.v1.

## Observed blocked example

The 3:00 PM-9:00 PM blocked-window case is now covered by `test_blocked_calendar_interval_occupancy_rejects_hsi_overlap_boundaries`, which rejects 5:45 PM, 6:00 PM, 6:15 PM, starts inside the block, partial overlaps, and surrounding intervals, while preserving exact end/start boundaries.
