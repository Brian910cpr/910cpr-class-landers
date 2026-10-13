# Active V2 demand and availability correction — local receipt

Date: 2026-10-11. Local implementation and validation only; no release authorization.

Branch: `fix/v2-demand-availability-20261011`

Implementation commit: `573305904f38842ff8118b9b199cb00e64cb42a1`

Base, refreshed from origin/main: `e663209d1e3db7d582079008250da622a2a01856`

Worktree: `C:\Users\ten77\Documents\Codex\2026-10-11\task\v2-demand-fix`

## Result

The active `layered-publication.v2` path separates direct bookability, committed capacity, and demand Anchors. Confirmed-zero inventory no longer creates occupied blocks or demand Anchors. Empty direct classes beyond 24 hours remain offered; inside 24 hours they are rejected. Speculative open-day offers and barnacles keep the 24-hour cutoff. Positive/seated direct offers do not inherit that empty cutoff, and lifecycle/capacity filtering remains upstream. Independent room/instructor commitments still veto conflicting direct and dynamic choices. Follow-up diff review also added directional instructor travel buffers to the direct-offer veto: touching after the evidenced travel interval is allowed, overlap and unknown travel are rejected conservatively.

Unknown counts remain unknown and conservatively reserve their bounded capacity; they no longer automatically manufacture a demand Anchor or daywide unknown-full-course rejection. Exact previously verified positive commitments retain their Anchor and occupancy through an unknown refresh. A compact identity ledger in `data/state_public/layered_verified_commitments.json` is supplied by the active selector and included in the existing refresh workflow's approved output. Its records contain only identity, timing, instructor/resource and verified counts. It never substitutes a historical count into the current roster count. Tests verify continuity with an empty calculation cache, zero clearing, cancellation, and moves. Independent manual/calendar commitments survive zero.

Canonical lifecycle and count evidence wins over mirrored published inventory for the same identity. A canceled or moved occurrence clears its own prior interval, without clearing another seated identity, including another seat at the same time. Input source records are not mutated.

The public feed reports inventory separately from Anchor/blocking geometry. `bookableUntil` carries the empty direct cutoff through finalization and browser refresh. The renderer uses the new asset version `20261011-empty-demand-1`.

## Before/after reproduction with bookable windows

Inputs: fixture-only confirmed-zero HeartCode BLS class at 12:00–13:00 on October 11; declared, completely covered room/instructor window 10:00–15:00; reference October 5 noon Eastern; no independent commitment. Real course IDs are reused; URLs point to `fixture.test`, and no booking endpoint is called.

| Decision | Unchanged base | Corrected V2 |
|---|---|---|
| Existing empty direct class at 12:00 | Rejected unconditionally | Bookable |
| Full Heartsaver choices | None | 10:00, 11:00, 12:00 |
| Occupied blocks | One, from zero inventory | None |
| Total alternative choices | 4 | 17 |

The same renderer and assets are used to isolate scheduling behavior. Desktop (1440px) and mobile (390px) Chrome both verified these starts through the actual course-choice UI and verified the 12:00 Heartsaver booking link. Alternatives do not reserve capacity against one another.

Durable evidence:

- `data/audit/v2_empty_window_before_after.json` — offers, feeds, occupied blocks, rejection reasons.
- `data/audit/v2_empty_window_before.html` and `data/audit/v2_empty_window_after.html` — rendered local fixture pages.
- `data/audit/v2_empty_window_reproduce.py` — reproduces from the pinned baseline and current code.
- `data/audit/v2_demand_validation.json` — aggregate failing test names/details and final check statuses.

Reproduce from the repository with `python -B -m data.audit.v2_empty_window_reproduce`. This writes only the two fixture HTML files and one fixture JSON receipt under `data/audit/`.

## Validation: passed, failed, and unrun

Passed:

- Python syntax compilation of all six changed scheduling modules.
- `git diff --check` and Node syntax check of `docs/assets/resolved-selector-availability.js`.
- Focused unittest suite: 101 executions, 71 unique tests, all passed. The existing day-cache test module imports the publication test class, causing repeated executions.
- `tests.test_v2_empty_window_rendered` plus `tests.test_layered_publication_pipeline`: 5 tests passed, including actual offline Chrome at desktop/mobile widths. All browser requests were intercepted; no live requests were made.
- Node aggregate: 51 passed, 0 failed, for canonical endpoint fixtures, external roster proof, and resolved selector availability.

Failed aggregate:

- The broader Python aggregate ran 155 tests: 122 passed, 15 failures, 18 errors, no skipped tests.
- The unchanged baseline ran the same 155 tests and had the same 15 failing and 18 erroring test identities. No newly failing test identities were introduced. This is not a green aggregate and does not prove release readiness.
- Missing `data/sessions_current.json` and other real runtime inputs prevent several real-input selector tests. Existing static/legacy expectations also fail on baseline. Details are preserved in the validation JSON.
- Initial sandbox runs additionally failed on temp-directory permissions and localhost sockets. Temp files were redirected to `.test-tmp`; the final aggregate ran with local fixture servers permitted, removing five environment-induced failures. These initial attempts are superseded by the final recorded result.

Unrun/blocked:

- Fresh authenticated canonical demand refresh and actual live-source before/after generation: `HOT_SYNC_ADMIN_KEY` is not configured and no fresh canonical snapshot exists in this isolated checkout. No credentials were invented or printed.
- Isolated PostgreSQL reconciliation suite; no database or migration was changed by this fix.
- Production build, push, PR, merge, deployment, live booking changes, and customer messaging were not performed.

Commands used for focused checks:

```powershell
$env:TEMP = Join-Path (Get-Location) '.test-tmp'
$env:TMP = $env:TEMP
python -B -m unittest tests.test_layered_day_cache tests.test_layered_publication_adapter tests.test_layered_selector_adapter tests.test_layered_calendar_coverage tests.test_layered_location_aliases tests.test_layered_resource_readiness tests.test_layered_release_probe
python -B -m unittest -v tests.test_v2_empty_window_rendered tests.test_layered_publication_pipeline
node --test tests/canonical_demand_endpoint.test.cjs tests/enrollware_roster_proof.test.cjs tests/resolved_selector_availability.test.mjs
```

## Bounded October 17 investigation and uncertainty

The checked-in BLS feed is generated at `2026-10-11T18:04:18.264015-04:00`. It contains unknown-count source identity `14377157` and canonical identity `3b2731a3-19bb-4d10-9757-08a8e81e336f`, both for the 10:00–12:00 Renewal occurrence (`359474`), and retains its direct 10:00 booking link. At noon it offers Provider and HeartCode, but not Renewal. These are checked-in diagnostics, not a new live observation.

A bounded fixture proves that a current unknown Renewal interval can remain occupied at 10:00–12:00 and directly bookable at 10:00 while Renewal at noon is no longer rejected solely for `full_course_count_unknown`. If authoritative exact historical commitment exists, normal Anchor/consolidation rules still apply. No claim is made that this live occurrence is empty or that all current holes arise from this defect.

The parent diagnosis reported zero confirmed-zero sources, 43 unknown class-source entries, and two positive entries for the same native Heartsaver occurrence. Those counts were not refreshed here. Cold-start history cannot invent prior demand for those unknown rows; they remain conservatively occupied until authoritative evidence is available. The new persisted ledger accumulates actual verified positives from fresh canonical input rather than treating displayed inventory as truth. Issue 334 lease expiry remains separate.

## Files for review and preserved work

Primary code: `scripts/layered_scheduling_engine.py`, `scripts/layered_publication_adapter.py`, `scripts/layered_selector_adapter.py`, `scripts/layered_day_cache.py`, `scripts/block_start_time_selector.py`, `scripts/build_bls_block_schedule_pilot.py`, `docs/assets/resolved-selector-availability.js`, `.github/workflows/refresh-public-site.yml`.

Tests: `tests/test_layered_publication_adapter.py`, `tests/test_layered_selector_adapter.py`, `tests/test_layered_day_cache.py`, `tests/test_layered_publication_pipeline.py`, `tests/test_v2_empty_window_rendered.py`, `tests/resolved_selector_availability.test.mjs`.

The original checkout remains on its unrelated intake branch; existing worktrees were inspected and not edited. No new competing recent V2 fix was found in the fetched source history. CRM issue 371 / PR 372 and CTA/link fixes 376–378 were not changed. This Windows checkout has case-collision modifications to `docs/Earl/index.html` and `docs/Jackson/index.html`; they are intentionally unstaged and absent from the implementation commit. `.test-tmp/` remains untracked with local test logs and temp files. No cleanup/reset of user work was performed.

## Release steps — require separate authorization

1. Review this local branch, the shared identity ledger, lifecycle matching, and aggregate failures.
2. Obtain the approved existing credentials/environment and refresh canonical demand and complete resource/instructor coverage. Do not infer emptiness for unknown rows; reconcile exact historical/manual commitments as needed. Seed history only from authoritative verified evidence.
3. Run the relevant real-input checks and a bounded current-source before/after comparison. Confirm real occupied intervals and seats are preserved, and inspect the October 17 example with its actual commitment evidence. The identical historical/template baseline failures are not new defects or blanket blockers for this correction; triage them separately rather than requiring unrelated repairs before a release decision.
4. Review the expected selector/feed generation scope before rebuilding public output. Verify rendered pages and booking URLs, the new asset version, empty cutoffs, and the ledger's persistence across fresh runners. Coverage leases/issue 334 must be assessed independently.
5. Only after explicit release authorization: push/create the reviewed PR, merge, allow the existing production workflow, and verify production output. This receipt grants no such authorization.

## Exact blocker clarification and follow-up review (22:46 UTC)

Actual missing inputs checked: `data/sessions_current.json` and `data/runtime/canonical_scheduling_demand.json`. Credential presence check only: `HOT_SYNC_ADMIN_KEY` is absent. The existing `data/audit/live_availability_snapshot_preview.json` is present, generated at 22:04:17 UTC; its one complete-coverage proof was observed at 22:04:17 UTC and expired at 22:19:17 UTC. At the 22:46 UTC check that proof cannot open V2 availability. The existing envelope freshness helper accepts the snapshot, but V2's scoped lease enforcement still rejects its expired proof. This is input freshness, not a newly fixed issue 334.

Present inputs checked: `docs/data/schedule_future.json`, location/resource map, course catalog, people catalog, appointment containers, and course consumption rules. The absence of `data/state_public/layered_verified_commitments.json` is expected before an authoritative first run; it is not a credential or required preexisting input. Cold-start unknown rows keep conservative occupied intervals without invented positive history.

All 18 aggregate errors stop at missing `data/sessions_current.json`. The 15 failures are one obsolete August 29–31 inventory assertion and 14 template/UI/asset-version assertions, including subtests; all fail on unchanged main too. None is newly caused by this scheduling correction. The relevant real-input integration checks remain unverified until valid inputs exist; unrelated historical/template failures should be triaged separately.

The browser before/after is synthetic fixture data. It uses a zero-count 12:00–13:00 HeartCode BLS occurrence, a covered 10:00–15:00 resource/instructor window, and a frozen October 5 clock. Both views use the same renderer/assets and only fixture.test links; all network requests are intercepted. It proves the decision and rendered bookability change, not current live demand or production readiness.

Booking-safety review: current zero does not reserve capacity, unknown is never silently zero, exact historical positive commitments survive unknown, independent commitments survive zero, lifecycle changes clear only their identity, dynamic alternatives remain constrained by room/instructor availability, and direct offers now respect collisions and directional travel. No additional reproducible defect was identified in the authorized scope after this follow-up fix. Open uncertainty is actual current roster/commitment evidence, including October 17; production inventory and history-ledger persistence through an actual refresh job are unrun.

Next owner action is access to the existing approved refresh environment or current validated snapshots, followed by review of the bounded real-source comparison. A separate explicit release decision is required before push/PR/merge/deploy. No unrelated baseline repair is automatically required by this patch.

## Runtime-input discovery follow-up (October 11, 22:51–22:56 UTC)

Before requesting owner inputs, all 14 registered repository worktrees were checked at explicit ordinary runtime paths, including the primary D: checkout and the existing source-refresh/reconciliation worktrees. No `data/sessions_current.json` or `data/runtime/canonical_scheduling_demand.json` was found. Existing calendar snapshots were stale; none was re-dated or accepted as current authority. No credential store was searched or secret value displayed.

The documented supported read-only source flow resolved two missing inputs locally:

- `scripts.build_sessions_current.build_sessions_from_enrollware_ical`: succeeded against its existing configured feed; produced 232 sessions at `2026-10-11T18:51:16.707133-04:00`. Validated build schema/shape, unique session identities, start timing, fresh timestamp, and `enrollware_ical_authoritative` source provenance. The producer explicitly leaves participant truth to canonical registrations.
- `scripts.export_calendar_snapshots.export_calendar_snapshots`: succeeded for all three active configured calendars via the documented public ICS resolver. Amy/Nick exported zero events; Brian inverse calendar exported 157 events. Private credential-file reads were disabled, and no credentials were copied or configured.
- `scripts.build_live_availability_snapshot`: produced 368 blocks at 22:52 UTC, with one complete coverage proof valid until `2026-10-11T23:07:18.049004+00:00`. Schema, fresh source provenance and scoped lease were validated. This lease is time-limited and must be renewed if consumed later.

Every new raw snapshot/output is confined to `.test-tmp/source-validation/`, which remains untracked. The ordinary primary checkout and production outputs were not changed. Sanitized producer receipts are recorded in `data/audit/v2_runtime_input_discovery.json`.

This supersedes the earlier claim that session timing and fresh calendar coverage require owner-supplied inputs. Those can be generated through the already-supported public read flow. The remaining blocker is authoritative canonical demand: no existing canonical snapshot was found, and the current process has no `HOT_SYNC_ADMIN_KEY`. No unauthenticated attempt was made against that reader and no credential boundary was bypassed. iCal counts must not be substituted for canonical attendee demand.

Exact supported commands for the ordinary environment are `python -B -m scripts.build_sessions_current --source enrollware_ical --output <validation-directory>/sessions_current.json --audit-dir <validation-directory>/sessions_audit`, `python -B -m scripts.export_calendar_snapshots`, `python -B -m scripts.build_live_availability_snapshot`, and `python -B -m scripts.fetch_canonical_scheduling_demand`. The no-CLI-output-override readers were invoked through their existing module APIs with output-path constants redirected solely to the isolated validation directory. The calendar reader's private-file lookup was disabled; its ordinary public source resolver was retained.

For canonical demand, use the existing approved runtime/CI environment where `HOT_SYNC_ADMIN_KEY` is already injected, as documented in `.github/workflows/refresh-public-site.yml`; execute only the read-only fetch module with its `OUTPUT` and `STATUS_OUTPUT` redirected to the validation directory. Do not dispatch the production workflow, copy/rotate/configure credentials, or ask Brian to provide secret values. Once that fresh validated snapshot exists, the remaining real-input comparison can proceed. No production workflow was dispatched here.
