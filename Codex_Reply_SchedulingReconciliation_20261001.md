# Scheduling reconciliation release handoff

Timestamp: 2026-10-01T03:32:52.018484+00:00
Branch: `codex/scheduling-reconciliation-20261001`
Implementation commit: `08d0334c83c66fc628aaf9aaf009af048edf921e`
Work-item state: IN_PROGRESS — production backend deployed; public frontend locally validated, awaiting merge/refresh approval.

## Result and exact evidence

Read the full primary audit: `data/audit/scheduling_reconciliation_20261001.md`.
Before/after canonical and workspace identities: `data/audit/scheduling_reconciliation_20261001.json`.
Protected live endpoint proof: `data/audit/scheduling_reconciliation_endpoint_proof_20261001.json`.
Publication counts, exact rejection reasons and October 2/3/7 cases: `data/audit/scheduling_reconciliation_preview_proof_20261001.json`.

One canonical operational schedule now projects into stable workspace rows; current external complete-roster evidence reconciles exact source identities, including native checkout linked to Enrollware. Source moves invalidate proof; stale/missing evidence closes new synthesis and remains unknown. Inverse availability no longer creates unrelated starts on occupied days. Course metadata supplies real occupied duration. Public selectors and Landscape consume the same final decision. Hard calendar collisions suppress booking while keeping the underlying class visible.

Production repair reconciled four source classes and six source registrations without changing Enrollware. October 2 counts are 2/1/2 at 08:45/10:45/12:45. October 3 church remains 09:00–11:30; HeartCode moved to the observed 12:30, occupied through 13:30. Original proposal/workspace identities and documents are preserved.

## Validation commands and results

```text
python -B -m unittest tests.test_anchor_state tests.test_apply_anchor_policy tests.test_canonical_scheduling_demand tests.test_fetch_canonical_scheduling_demand tests.test_demand_publication tests.test_selector_clock tests.test_enrollware_roster_reconciliation tests.test_validate_public_refresh_output tests.test_scheduling_reconciliation tests.test_publish_scheduling_landscape tests.test_zero_duration_pipeline tests.test_enrollware_ical_import
Ran 91 tests in 16.443s
OK

node --test tests/canonical_demand_endpoint.test.cjs tests/enrollware_roster_proof.test.cjs tests/resolved_selector_availability.test.mjs
49 passed, 0 failed

node --test tests/reconciliation/reconcile.test.mjs
1 PostgreSQL lifecycle integration test passed; many transaction/identity/security assertions

Syntax validation passed: 47 Python/JavaScript units
Both SQL migrations parsed successfully
git diff --cached --check: clean
```

Protected production endpoint: https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/36810335487 — 33 sessions, 7 known counts, 26 unknown; repeated content equal; OPTIONS 204; unauthenticated access 401.

Actual browser preview verified BLS Initial October 2 shows only 12:45 and retains registration ID 14501248; Landscape shows all three real classes and both October 3 commitments. October 7 source conflict is loudly marked and booking suppressed. Eight bounded selector feeds validated using fresh iCal/calendar snapshots and the deployed runtime endpoint. No full sitewide generator was run locally.

Known unrelated failures: historical generated-artifact tests depend on ignored/stale local inventory; the entire repository test suite is not claimed green. Existing Earl/Jackson case-collision files, three tracked Python cache files, and `supabase/.temp/` remain outside this commit. Original checkout was not changed. Private roster snapshots remain in the projectless task's `work/` directory and are intentionally not committed to this public repository.

## Deployment and persistent-system proof

Supabase migrations `20261001024838_canonical_scheduling_projection.sql` and `20261001032240_native_event_identity_health.sql` applied; `canonical-scheduling-demand` v7 and `canonical-session-workspace` v11 deployed with existing authentication preserved. Backend components CONNECTED and PROVEN. Frontend/publication BUILT and browser-validated locally; not yet deployed as of this receipt. GitHub Pages production source is `main:/docs`, confirmed through the GitHub Pages API.

Last bounded end-to-end proof: 2026-10-01T03:31:03.376132+00:00. Source roster observation: 2026-10-01T03:00:49.497Z; proof expires after 60 minutes. Public feed expiration: 20 minutes, checked on load and registration click; refresh every five minutes. Existing GitHub scheduling workflows are intended to refresh publication; their successful resumed cadence is not yet proven. Monitor/observer end-to-end health is not yet established, so the combined system is not MONITORED or HEALTHY.

Brian confirmed there is NO automated Enrollware export. A complete authenticated collector remains absent. The system must show stale/unknown rosters and close synthesis after freshness expires, not manufacture zero counts. Recovery uses the existing complete-roster importer with genuinely fresh source observations. An unattended collector requires an approved credentialed source and complete coverage/status semantics; Gmail/iCal are insufficient. This is a dependency toward retirement as native LanderWare enrollment becomes authoritative, not a new competing course catalog.

## Next action and owner decision

Review the audit, migrations, shared proof code, final selector policy and regressions. Finish CI, then obtain approval for merging this prepared PR and the existing production refresh. The user-provided AGENTS requires approval before a sitewide generator; merging the changed workflow paths triggers it. Expected scope: current class landers (~29), eight selector feeds/pages, course/location hubs, index/sitemap/build metadata, and admin/calendar publications; 1,075 tracked HTML pages may be inspected. Last equivalent successful refresh changed 47 files. Inspect generated scope before declaring release proven.

After approval: merge through GitHub, observe both existing refresh workflows and GitHub Pages, verify live HTML/versioned JavaScript/JSON and actual rendered October 2–3 behavior, then issue a release receipt. Do not deploy an unrelated Cloudflare worker. No approval is presumed from silence.

The October 7 17:30 Heartsaver class overlaps a Brian busy block from 02:45–21:45 and needs an operational scheduling decision. This repair suppresses the offer; it does not move/cancel the existing class.

## Exact changed files

- `.github/workflows/anchor-policy-ci.yml`
- `.github/workflows/refresh-admin-availability.yml`
- `.github/workflows/refresh-public-site.yml`
- `data/audit/scheduling_reconciliation_20261001.json`
- `data/audit/scheduling_reconciliation_20261001.md`
- `data/audit/scheduling_reconciliation_endpoint_proof_20261001.json`
- `data/audit/scheduling_reconciliation_preview_proof_20261001.json`
- `docs/ACLS.html`
- `docs/BLS.html`
- `docs/HEARTSAVER.html`
- `docs/PALS.html`
- `docs/acls.html`
- `docs/admin/scheduling-landscape-lanes.js`
- `docs/admin/scheduling-landscape.html`
- `docs/arc.html`
- `docs/assets/resolved-selector-availability.js`
- `docs/bls.html`
- `docs/corp/maxim-schedule.html`
- `docs/corp/maxim.html`
- `docs/courses/uscg-first-aid-cpr-aed.html`
- `docs/family-cpr.html`
- `docs/heartsaver.html`
- `docs/hsi.html`
- `docs/pals.html`
- `docs/uscg-elementary-first-aid-cpr.html`
- `scripts/anchor_state.py`
- `scripts/apply_anchor_policy.py`
- `scripts/block_start_time_selector.py`
- `scripts/build_bls_block_schedule_pilot.py`
- `scripts/build_schedule_future.py`
- `scripts/canonical_scheduling_demand.py`
- `scripts/publish_admin_availability.py`
- `scripts/publish_scheduling_landscape.py`
- `scripts/validate_public_refresh_output.py`
- `supabase/functions/_shared/external-roster-proof.ts`
- `supabase/functions/canonical-scheduling-demand/index.ts`
- `supabase/functions/canonical-session-workspace/index.ts`
- `supabase/migrations/20261001024838_canonical_scheduling_projection.sql`
- `supabase/migrations/20261001032240_native_event_identity_health.sql`
- `tests/canonical_demand_endpoint.test.cjs`
- `tests/enrollware_roster_proof.test.cjs`
- `tests/reconciliation/reconcile.test.mjs`
- `tests/reconciliation/schema.sql`
- `tests/resolved_selector_availability.test.mjs`
- `tests/test_apply_anchor_policy.py`
- `tests/test_demand_publication.py`
- `tests/test_scheduling_reconciliation.py`
- `tests/test_validate_public_refresh_output.py`
- `tests/test_zero_duration_pipeline.py`
- `Codex_Reply_SchedulingReconciliation_20261001.md` (this receipt)
