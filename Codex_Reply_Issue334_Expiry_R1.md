# Incident 334: public offer expiry

Timestamp: 2026-10-01 15:54 America/New_York.
Branch: main.
Substantive commit: 328eb83aa7dbb2eb8caffa13a2e5240204a5a088.
State: IN_PROGRESS. Evidence: BUILT, production refresh running.

Root cause proven: finalize_selector_payload set publication expiry 20 minutes ahead, shorter than the 30-minute public refresh cadence. Live Heartsaver JSON generated 14:40 ET expired 15:02 ET and remained served at 15:50 ET; all 14,770 offers shared the expired timestamp.

Changed scripts/apply_anchor_policy.py only: 90-minute publication validity, allowing two 30-minute refresh intervals and 30-minute build/deploy/queue budget. Source-specific freshness caps, canonical reconciliation and conflict checks remain enforced. Owner explicitly requested this emergency extension.

Validation: python -m unittest tests.test_apply_anchor_policy tests.test_anchor_state, 24 passed.

Push to main triggered Refresh admin availability run 36917433386. Publication output and live customer UI proof pending. Previous PR333 branch anchor-policy CI failure is unrelated to this one-line lease change; that branch is untouched.

Additional finding: GitHub scheduled-event history's latest entries are September 11. Both refresh workflows report active via public Actions workflows API. Missing scheduled executions remain unresolved. A longer lease cannot compensate for an indefinitely absent publisher.

Expected cadence: admin 10 minutes; public 30 minutes. Staleness condition: current publication past validUntil or no renewal before expiry. Current observer is this incident investigation; autonomous observer health not established. Recovery: fresh publication from main, inspect job failure if any, verify live JSON expiry and visible offers before closing incident.

Next action: wait for run 36917433386 and resulting Pages deployment, verify live payload and customer booking page, and restore/observe recurring publication. No user account action currently required. Do not claim site healthy until end-to-end verification.
