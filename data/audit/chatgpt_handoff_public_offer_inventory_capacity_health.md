# Public Offer Inventory & Capacity Health handoff

## Checkpoint and isolation

- Parent checkpoint: `a1d8f4ce465` (`fix: expose public availability by actual service fit`)
- FIT_ONLY_DEBUG behavior was read but not modified.
- No public scheduler/site generator was run.
- The existing Inventory Control Center is the integration surface.

## Authoritative inputs

- Public dynamic offers: the seven existing family block-schedule audit JSON files produced by `scripts/block_start_time_selector.py`.
- Actual seated public sessions: `docs/data/schedule_future.json`, deduplicated by durable session ID.
- Genuinely usable time and real blocking state: `data/audit/live_availability_snapshot_preview.json`.
- Operating start policy: `data/config/public_offer_policy.json`.
- The capacity end assumption is latest permitted public start plus the minimum 60-minute appointment, currently 08:00-20:00.

## Metric definitions

- Candidate starts and course alternatives are collapsed into one physical dynamic offer window per date/source availability block/instructor/location.
- Capacity uses merged physical intervals. Overlapping courses or starts cannot inflate exposed minutes.
- Hidden capacity is merged usable time minus merged public-offer exposure.
- Explicit `creation_origin`/`origin` wins. Explicit anchor-stack presentation is BARNACLE. LanderWare dynamic windows default ANCHOR. Legacy imported seated sessions default MANUAL and retain `origin_basis=source_provenance_default` so the limitation is visible.

## Real-data result as of 2026-08-11

- August: 31 distinct sessions = 28 Anchor + 0 Barnacle + 3 Manual.
- July: 22 distinct sessions = 0 Anchor + 0 Barnacle + 22 Manual.
- Observed 2-month average: 26.5 sessions/month.
- Month-over-month: +9 sessions / +40.9%.
- Remainder of August: 28 sessions, 21 calendar days, 1.33/day, ABOVE PACE versus the available July comparison.
- Remainder usable capacity: 197.0 hours.
- Remainder publicly exposed capacity: 195.2 hours.
- Remainder hidden usable capacity: 1.8 hours.
- Capacity exposed: 99.1%.
- Previous-month/typical capacity exposure is unavailable because retained live-availability coverage begins on 2026-08-11.

## Manual reconciliation

- 2026-08-12: 600 usable minutes, 600 exposed, 0 hidden, 100%.
- 2026-08-13: 720 usable minutes, 720 exposed, 0 hidden, 100%.
- The seven remaining hidden windows are each 15 minutes, totaling 105 minutes, and are listed in the generated panel payload.

## Files

- `scripts/public_offer_capacity_health.py`
- `scripts/build_inventory_control_center_data.py`
- `tests/test_public_offer_capacity_health.py`
- `docs/control-center/inventory/index.html`
- `docs/control-center/inventory/inventory-control-center.js`
- `docs/control-center/inventory/inventory-control-center.css`

The targeted builder updates `debug/inventory_control_center_data.json`, but that generated file is excluded from the analytics commit because rebuilding it also refreshes unrelated age/timestamp warnings. Run `python scripts/build_inventory_control_center_data.py` to reproduce the panel payload locally.

## Validation

- Python syntax validation passed.
- Six focused unit tests passed.
- JavaScript syntax validation passed with `node --check`.
- `git diff --check` passed.
- Local browser verification confirmed the compact three-card layout and expandable session/usable/exposed/hidden drill-downs.
