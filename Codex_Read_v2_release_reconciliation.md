# V2 release reconciliation

Branch codex/v2-production-reconciliation, source commit ff15b2b2c, based on current production 960941475. Original work retained in feat/layered-production-20261005 (repair 1ca63d0ad). Lab repair a70b88aba.

24 explicit source/config/test paths reconciled using three-way application, no unresolved conflicts. Current production booking data preserved. Added bounded fresh calendar coverage and authoritative venue mapping; retained V2 finalizer lease protection and public edge identities. Spreadsheet detour, historical generated inventory and unrelated pages excluded.

171 combined production tests passed in reconciled checkout, including source/coverage/publication/cache, canonical reader, reconciliation, anchors, diagnostic projections and desktop/mobile customer renderer fixtures. Changed Python syntax passed. Lab cadence and actual/fixture browser checks: 3 passed. Negative test error messages were mocks, not denied endpoint retries.

Actual source evidence: local supported calendar exporter captured 161 Brian events at 2026-10-07T00:04:44-04:00 and yielded 1 bounded proof. Production runner artifact for run 37567101064 reports canonical reader success, 25 sessions at 2026-10-07T03:33:36.575Z. That observation is historical, not current local demand.

Public V2 activation/deployment stopped: current local canonical scheduling demand and HOT_SYNC occupancy snapshots absent; fresh actual source-to-V2-to-public-render proof unavailable. Policy remains shadow. Denied local HTTP403/BIC path not retried; secrets untouched; no bookings changed; no public deployment. Push/merge/deploy authorization remains conditional on release checks; live proof outstanding.

Next step: obtain a current source-to-V2 dry-run through the approved production runner with its configured readers; inspect public-safe decision/rejection evidence. Then activate the existing feed path and verify the deployed customer flow.

Key files: scripts/build_live_availability_snapshot.py, scripts/block_start_time_selector.py, scripts/layered_publication_adapter.py, scripts/layered_day_cache.py, scripts/apply_anchor_policy.py, scripts/build_bls_block_schedule_pilot.py, scripts/publish_scheduling_landscape.py, data/config/layered_scheduling_policy.json. Key tests: tests/test_layered_calendar_coverage.py, tests/test_layered_publication_pipeline.py, tests/test_layered_publication_adapter.py, tests/test_layered_day_cache.py.

docs/data/schedule_future.json unchanged from production: True
