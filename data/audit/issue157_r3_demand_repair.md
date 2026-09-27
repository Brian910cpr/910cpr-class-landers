# Issue 157 R3: canonical demand and the September 27 split

Observed 2026-09-27 UTC. Existing assignment: #157; existing PR: #197; direct prerequisite: #297. This continues R3 and preserves every prior receipt.

## State and ownership

- Repository: Brian910cpr/910cpr-class-landers. Existing branch: `codex/issue-157-runtime-projection`.
- Isolated worktree: `C:\Users\ten77\Documents\Codex\worktrees\issue-157-r3`. Other working copies and unrelated dirty changes were preserved.
- No competing active coding owner was found in the available Codex task/process inventory. No session was interrupted.
- Observed local runtime configuration: `gpt-6-astra`, reasoning effort `xhigh`; not changed.
- Production baseline: main `616832dec7cef34b0e4928d90fe74a7d480259ab`, successful Pages run `36286584307`. Main was merged into the existing PR history at `2db7c48f273`; one Anchor-policy test conflict retained both sets of required assertions.
- Case-colliding generated Earl/Jackson paths were backed up outside the repo and excluded in this Windows worktree. They are not part of the patch.
- Stage 6 remains gated. No real booking was created, moved, canceled, or edited.

## Actual incident records

Both occurrences are **Sunday, September 27, 2026**, at Wilmington Shipyard Room B, with Brian Ennis. The authenticated Enrollware class list and individual rosters each currently show one registration.

| Course | Public external class ID | Appointment class ID | Start Eastern | Registration timestamp Eastern |
|---|---|---|---|---|
| BLS Renewal, course 359474 | 14361098 | 51485 | 1:00 PM | September 24, 7:26 PM |
| HeartCode BLS, course 210549 | 14421081 | 51495 | 6:30 PM | September 26, 3:59 PM |

The Renewal booking came first. Enrollware notices independently corroborate those times. The records do **not** establish the referral/navigation channel. A materials option labeled “MANUAL: OTHER SOURCE” is not evidence of a booking channel. Neither customer's visit is assumed to have passed through LanderWare. No participant names, contact details, payment details, or private roster files are included here.

The Enrollware class form reports zero instructional hours and identical start/end times for the Renewal appointment-created row. The public scheduling projection supplies its configured two-hour duration. This is another reason not to manufacture canonical scheduling identity/duration from a roster screenshot or notice alone.

## Publication trace and lead-time defect

`data/audit/issue157_r3_proof.json` preserves the exact public records and source revisions:

1. Before Renewal: `71a15fd71ce3656873e655fc1da71f8a244840c8`. No September 27 schedule/Anchor rows; 137 selector offers.
2. Before HeartCode: `af4befbd61699b65fc5603ff60292558665a40dd`. Renewal exists at 1 PM. Its old Anchor has `registered_count: 0`, `promotion_reason: existing_public_class`. The selector has exactly two offers: Renewal and HeartCode 6:30 PM. HeartCode already has `schedule_role: barnacle`, `attached_to_session_id: 14361098`, direction `post`, availability block `brian_do_not_schedule:inverse_gap:3`, and appointmentDayId `260768`.
3. Current baseline: both bookings are schedule rows and both were promoted by the old public-class rule despite unknown enrollment. Live BLS HTML and all seven referenced same-site CSS/JS assets returned 200; SHA-256 hashes are in the JSON audit. This is observation of the unrepaired public deployment, not live proof of the patch.

The pre-HeartCode feed was built at `2026-09-26T18:02:15.568540` on the UTC runner. `selector_reference_datetime()` used host local time and discarded the zone. Thus it treated 18:02 UTC as 18:02 Eastern instead of 14:02 Eastern. The unchanged 24-hour minimum then excluded tomorrow's 3 PM offer and admitted 6:30 PM. The focused historical-clock regression demonstrates this filter error. It explains a mechanism consistent with the recorded offer, but does not prove which page either customer visited or reconstruct every historical source constraint.

The fix normalizes aware input timestamps and the build reference clock to America/New_York. The lead-time value, duration, availability, conflict, compatibility, repeat-spacing, and ranking policies are unchanged. An AST comparison confirms `apply_daily_anchor_stack` is identical to current-main baseline; `data/config/anchor_schedule_policy.json` is unchanged. There are no weekend-specific rules.

## Canonical prerequisite, verified again

Fresh production SQL across **all record scopes** returns zero `class_sessions` rows from September 26 local midnight through September 28 local midnight. Therefore the two Sunday cases and the three September 26 cases in #297 cannot join to canonical registrations. This is not the historical #140 blocker; #140's gate was already cleared.

The current external bridge has no verified session-level complete-roster freshness contract. Existing historical import/promotion code and `scripts/import_enrollware_registration_events.py` (report-only) do not supply current cancellation/reschedule/empty-roster completeness. Merely reading old canonical rows at the present time cannot establish current Enrollware demand.

The endpoint therefore emits null/unknown for external backends, with `demand_status: external_reconciliation_required`. Native `landerware` and `manual` canonical backends count actual active relationships. Missing matches remain null with `missing_canonical_session`; duplicate claims fail closed for both rows. The per-occurrence match audit exposes the exact missing IDs and reasons. No mail-derived or historical counts were promoted to live truth.

Coordination is on the original prerequisite: https://github.com/Brian910cpr/910cpr-class-landers/issues/297#issuecomment-5852136510. Required continuation is canonical session reconciliation plus a verified complete-roster source watermark, cancellation/reschedule handling, and an agreed freshness window. This repair does not claim #297 complete.

## Implementation and publication connection

- `supabase/functions/canonical-scheduling-demand/index.ts`: real New York date boundaries (EST, EDT, 23/25-hour days), local default date, validated ranges, CORS-preserving bodyless OPTIONS, bounded backend/auth requests, stable paginated reads, preserved external course identity, PII-free known/unknown demand.
- `scripts/fetch_canonical_scheduling_demand.py`: New York query date, validated explicit unknowns, fresh schema-checked atomic runtime snapshot. The existing 15-minute source freshness limit remains enforced.
- `scripts/canonical_scheduling_demand.py`: recompute derived demand on every refresh; reject missing identity and duplicate claims; remove stale prior projection; preserve unknown.
- `scripts/anchor_state.py`: actual canonical positive demand or a separate explicit commitment/manual override; shared promotion gate; unknown count remains null.
- `scripts/block_start_time_selector.py`: canonical snapshot reaches candidate consolidation as well as final ranking; legacy seat counts no longer create candidate Anchors; Eastern clock repair.
- `scripts/apply_anchor_policy.py`: require a fresh runtime input, clear demoted Anchor metadata, preserve explicit commitments through positive-demand refreshes, rewrite the selector's actual appointment URL when reusing an Anchor, emit per-occurrence reconciliation diagnostics. Existing ranking remains unchanged.
- Both `.github/workflows/refresh-public-site.yml` and `refresh-admin-availability.yml` fetch canonical demand before candidate/Anchor publication. The public workflow uses the validated stable hash, aborts a failed PowerShell fetch, and reapplies policy on registration-only changes. The second scheduled publisher cannot overwrite with a path that omitted canonical demand.
- `.github/workflows/anchor-policy-ci.yml` runs isolated source tests. `verify-canonical-participants.yml` adds an explicitly selected, read-only demand verification job using the existing GitHub secret; no key is printed or copied locally.

No sitewide generator or production publication workflow was dispatched from this working branch. Existing public HTML/JS/CSS are unchanged. Fixture output is confined to temporary/work files; the actual public renderer consumes that output in a local browser.

## Tests and rendered proof

- `python -m unittest tests.test_anchor_state tests.test_apply_anchor_policy tests.test_canonical_scheduling_demand tests.test_fetch_canonical_scheduling_demand tests.test_demand_publication tests.test_selector_clock`: **43 tests passed**.
- `node --test tests/canonical_demand_endpoint.test.cjs`: **12 tests passed**. Tests execute the actual TypeScript handler through Node's TypeScript stripping with isolated auth/database fixtures, including 501-row pagination, CORS/auth, active statuses, unknown external demand, and DST boundaries. They do not substitute a separately implemented endpoint.
- Five changed Python modules compile; four changed workflow YAML documents parse; `git diff --check` passes.
- The broader existing selector suite was compared against baseline main in the same checkout/environment: **60 tests, 14 failures, 18 errors on both versions; no newly failing test IDs**. These tests depend on absent ignored live `data/sessions_current.json` and stale generated-output expectations. Exact names are retained in `selector_regression_comparison` in the JSON audit. They are not represented as passing CI or fixed here.
- Isolated endpoint -> HTTP fetcher -> atomic runtime -> schedule -> Anchor -> selector publication: weekday September 2, Saturday September 7, Sunday September 8, 2030; `0→1→1→0→0` in each case. Explicit commitment/manual-override and legacy explicit-commitment variants survive `1→0`. Missing/ambiguous sources clear previous demand; missing runtime stops publication.
- The actual unmodified `docs/bls.html` and repository assets were opened at `http://127.0.0.1:8157/bls.html?course=210549`. For the Sunday fixture, one registration yields Renewal 1–3 PM and HeartCode noon/3 PM Barnacles. DOM buttons have `is-barnacle`; the Register URL is `https://example.test/fixture/12:00`. Reload preserves it. Removing the registration yields no Anchor and four `is-available` HeartCode slots (8 AM/noon/3 PM/6:30 PM). No real checkout was submitted.

## Deployment, limits, next action

The protected read-only demand function was deployed as **version 1**, function ID `d4fe35dc-9ccb-4043-9593-172cf629ef9f`, bundle SHA-256 `58c3c86cb628430745016aa93176e6d2aa2eb3b2d3dca16e9a07ce1ef2bc8d6a`. Custom authentication uses the existing HOT_SYNC owner endpoint. Live checks: allowed OPTIONS **204** with required CORS and empty body; missing key **401**; deliberately invalid key **401**; untrusted origin **403**. Authenticated proof and exact workflow run are recorded in the immutable R3 receipt after pushing the substantive commit.

**BUILT locally; demand endpoint DEPLOYED; public repair not MERGED, DEPLOYED, or LIVE-VERIFIED.** Do not label the full system CONNECTED/PROVEN/HEALTHY. The isolated lifecycle is proven, but production canonical coverage is incomplete and R3 review remains required. Stage 6 stays closed.

The explicit issue instruction at https://github.com/Brian910cpr/910cpr-class-landers/issues/157#issuecomment-5760164604 says: “Do not merge or claim CONNECTED/PROVEN until the R3 receipt is reviewed and the strongest currently available live/backend verification is complete.” This is the merge gate, not an assumed permission problem.

After review and #297 reconciliation, merge the existing PR through the normal process, run the normal production publishers, verify the deployed revision against live schedule/Anchor/selector JSON and BLS HTML/assets, then repeat a later production refresh check. Complete-roster reconciliation must replace the conservative external-unknown gate before claiming external demand is connected. Native Enrollware appointment checkout, direct/bookmarked URLs, administrator adds, and other external paths remain outside LanderWare's selector enforcement. Their source state must be reconciled; this patch cannot enforce LanderWare ranking inside Enrollware.
