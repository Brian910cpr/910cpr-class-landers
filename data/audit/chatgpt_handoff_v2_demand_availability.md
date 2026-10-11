# Active V2 demand and availability correction — local receipt

Date: 2026-10-11. Local implementation and validation only; no release authorization.

Branch: `fix/v2-demand-availability-20261011`

Implementation commit: `573305904f38842ff8118b9b199cb00e64cb42a1`

Base, refreshed from origin/main: `e663209d1e3db7d582079008250da622a2a01856`

Worktree: `C:\Users\ten77\Documents\Codex\2026-10-11\task\v2-demand-fix`

## Result

The active `layered-publication.v2` path separates direct bookability, committed capacity, and demand Anchors. Confirmed-zero inventory no longer creates occupied blocks or demand Anchors. Empty direct classes beyond 24 hours remain offered; inside 24 hours they are rejected. Speculative open-day offers and barnacles keep the 24-hour cutoff. Positive/seated direct offers do not inherit that empty cutoff, and lifecycle/capacity filtering remains upstream. Independent room/instructor commitments still veto conflicting direct and dynamic choices.

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
- Focused unittest suite: 99 executions, 70 unique tests, all passed. The existing day-cache test module imports the publication test class, causing repeated executions.
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
3. Run real-input aggregate checks and a bounded current-source before/after comparison. Confirm real occupied intervals and seats are preserved, and inspect the October 17 example with its actual commitment evidence. Resolve baseline validation blockers before treating the release as ready.
4. Review the expected selector/feed generation scope before rebuilding public output. Verify rendered pages and booking URLs, the new asset version, empty cutoffs, and the ledger's persistence across fresh runners. Coverage leases/issue 334 must be assessed independently.
5. Only after explicit release authorization: push/create the reviewed PR, merge, allow the existing production workflow, and verify production output. This receipt grants no such authorization.
