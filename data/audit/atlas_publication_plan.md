# Atlas publication plan

Approved by Brian on October 11, 2026. Publish confirmed seated classes first. Later, use selected distant offers for Atlas exposure while preserving LanderWare's ability to shape the near-term schedule organically.

## Phase 1 Confirmed seated classes

Publish upcoming confirmed classes that have at least one paid seat. Use the actual instructor and location. Check existing Atlas listings to avoid duplicates and check actual instructor conflicts. Unpurchased offers and pending-payment requests do not qualify in this phase.

The 27-row working export is a source snapshot, not independent proof of payment for every row. Brian states the intended class list is paid-seat inventory. Verify the source-to-paid-seat relationship during implementation; do not substitute all availability for that list.

## Phase 2 Distant offers

After the other instructors are on board, pepper offers at selected popular times more than four weeks (28 days) in the future. These are offers, not confirmed seated classes.

At 28 days before an offered class starts, remove its Atlas listing unless the class has acquired a paid seat. A class with a paid seat remains listed as a real confirmed seated class. Apply the same rule to unpaid offers discovered inside the 28-day window.

A purchase follows the existing LanderWare Anchor and Barnacle policy and triggers reconciliation of competing offers. Atlas publication must follow that policy without requiring the person managing the listing to know its internal rules. Keep offer overlap distinct from instructor conflicts: actual purchases must not promise one instructor for simultaneous incompatible classes.

Removing an Atlas offer listing does not cancel a paid class, delete its students, or delete the underlying LanderWare class record.

## Operating tradeoff

The goal is broad Atlas visibility farther out, then fewer speculative listings near term. Brian accepts an occasional second office trip if a competing offer sells before cleanup; that is preferable to two trips every day. This tolerance is for teachable separate times, not simultaneous conflicting instructor commitments.

## Implementation details still to resolve

- Exact popular times, publication volume, and which additional instructors participate.
- Exact handling of a temporary payment-pending hold at the removal boundary; a pending request is not a paid seat.
- Refresh cadence, time-zone-aware 28-day calculation, duplicate prevention, and retry/reconciliation after Atlas failures.
- Persist the mapping between source class ID and Atlas listing ID, with publication/removal outcomes.

## Current status and source references

Plan saved; automation and Atlas publication have not been implemented or deployed. Atlas sign-in redirected to AHA maintenance during the October 11 session.

- Page generator: scripts/build_index_and_sitemap.py
- Public schedule input in inspected checkout: docs/data/schedule_future.json
- Current-session intermediate: data/sessions_current.json
- Initial working export: data/audit/atlas_class_entry_working_20261011.json
- Source trace receipt: Codex_Reply_AtlasSourceTrace_20261011.md

Resume with one confirmed seated class: access Atlas, inspect current Create a Class fields and existing listings, map verified source data, create the listing, and verify the public result before processing the rest. Phase 2 remains future work.
