# PR353 actual-data repair receipt R1

Branch: codex/v2-production-reconciliation. Source commit: 8a336ce97bad656c9c6e9929379c6afa6f698364. PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/353.

Actual-data probe: https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/37619823205. Current configured readers succeeded for Enrollware, HOT_SYNC occupancy, canonical registrations (25 sessions) and calendar exports (one bounded coverage proof). Published=false. No secrets or participant data exported.

Before: 205 availability windows, zero evaluated, 205 unresolved_occupied_bounds failures. Record 13880764 (ARC Adult CPR AED - Blended) had an unrecognized existing catalog alias and zero duration. Added exact alias to existing course372258 and used its existing duration rule, preserving the record and unknown counts. Actual-shaped import regression passes.

Next actual failure was offset-aware V2 starts compared with naive public-policy clock. Normalize both to the existing Eastern business-clock convention; regression confirms UTC and Eastern inputs yield the same policy decisions.

Final window defect: 27 missing travel rules were all the already-declared internal Room B alias being treated as offsite. Existing resolver now consumes explicit internal resource aliases and retains actual Room A/B/C assignment. Unknown offsite locations still remain unresolved; no automatic relocation added.

After: all 205 windows evaluated, zero failed. BLS: 88 dates, 68 barnacles,3836 open-time choices,12 existing classes. Heartsaver89 dates; USCG89; HSI88; ARC88; Family87. ACLS/PALS preserve existing classes and Brian's explicit exclusion. Unknown source counts remain unknown: 460 projected BLS-source records retain countAvailable=false and registeredCount=null.

October16 BLS skills actual rendering: 9:15AM, starred10:15AM existing class,1:00PM. Desktop1440 and mobile390 verified: exactly one star, two unstarred barnacles,88 selectable dates, no JS errors or horizontal overflow. 9:15AM Register link has appointmentDayId260787,courseId210549,matching startTime. No registration submitted.

Tests: combined production171 passed before final repairs; latest timezone/publication/cache51 passed; alias/normalizer/publication/cache61 passed; source alias/zero-duration/reconciliation30 passed; fixture-reader/clock27 passed; probe rollback test passed. Required GitHub PR checks passed at source8a336ce97. Wider legacy test_block_start_time_selector run had15 failures and18 errors (missing local current-session data and old renderer/source expectations); not represented as green. Those results remain a validation gap.

Public diagnostic privacy repaired: publish_scheduling_landscape emits whitelisted layeredLandscape rather than raw layeredDiagnostics.

Stopped actions: no merge, active public policy or public-source cutover yet. Existing persisted review says not accepted for merge or activation. This receipt supplies the requested new positive proof; that hold has not been bypassed. Historical public class13880764 returned HTTP403; stopped that read and did not retry it. Local protected HTTP403/BIC paths not retried. Non-fast-forward branch pushes were stopped, reviewer acknowledgement commits preserved via normal merges, then normal push succeeded without force.

Current policy remains shadow. No owner-only secret setup required for this runner proof. Next: resolve the release/review hold and outstanding legacy-check classification, then activate V2, update the existing customer source/rendered pages, deploy and verify live HTML/assets/calendar selection.

Changed files:
.github/workflows/refresh-admin-availability.yml
.gitignore
Codex_Read_v2_release_reconciliation.md
Codex_Read_v2_release_reconciliation_20261007T1207Z_Delta.md
Codex_Reply_v2_release_reconciliation.md
data/audit/chatgpt_handoff_v2_release_reconciliation.md
data/config/course_map.json
data/config/layered_scheduling_policy.json
scripts/apply_anchor_policy.py
scripts/block_start_time_selector.py
scripts/build_bls_block_schedule_pilot.py
scripts/build_live_availability_snapshot.py
scripts/build_sessions_current.py
scripts/fetch_canonical_scheduling_demand.py
scripts/generate_dynamic_offers.py
scripts/layered_day_cache.py
scripts/layered_publication_adapter.py
scripts/layered_resource_readiness.py
scripts/layered_scheduling_engine.py
scripts/layered_selector_adapter.py
scripts/publish_scheduling_landscape.py
scripts/run_layered_release_probe.py
tests/fixtures/layered_native_oct10.json
tests/fixtures/layered_publication_oct11_14.json
tests/test_demand_publication.py
tests/test_enrollware_ical_import.py
tests/test_fetch_canonical_scheduling_demand.py
tests/test_layered_calendar_coverage.py
tests/test_layered_day_cache.py
tests/test_layered_location_aliases.py
tests/test_layered_publication_adapter.py
tests/test_layered_publication_pipeline.py
tests/test_layered_release_probe.py
tests/test_layered_resource_readiness.py
tests/test_layered_selector_adapter.py
tests/test_selector_clock.py
