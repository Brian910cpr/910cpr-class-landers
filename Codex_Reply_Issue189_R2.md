# Codex Reply — Issue #189 Round 2

- Assignment: GitHub issue #189, supervisor Round 2
- Timestamp: 2026-09-11T14:34:55-04:00 (America/New_York)
- Branch: `codex/issue-189-timezone-r2`
- Substantive commit: `1a23750a05da149db8dff5e00ec83859bdc53be3`
- Pull request: #191, https://github.com/Brian910cpr/910cpr-class-landers/pull/191
- Merge commit: `e1dc87fd4bf13254b12f2bc5b39d8bba2e836e44`
- Work-item state: `VERIFIED`

## Root cause

`docs/admin/all-classes.js` appended `-04:00` to every owner-entered class start and end. That encoded summer EDT correctly but shifted winter EST entries by one hour relative to the canonical `America/New_York` wall-clock contract. It also had no safe handling for local times in the spring DST gap or fall DST overlap.

## Work performed

- Added a browser-machine-timezone-independent `America/New_York` serializer.
- Resolves the offsets applicable near the selected date, round-trips candidate instants through `Intl.DateTimeFormat`, and accepts exactly one candidate.
- Fails closed with an owner-visible error when a wall time is nonexistent or ambiguous.
- Routed the exact record serialized into the existing HOT_SYNC `fetch()` body through the tested record builder.
- Versioned the public JavaScript reference from `v=20260911-1` to `v=20260911-2`.
- Added deterministic Node tests for winter EST, summer EDT, both DST boundary failure modes, and HOT_SYNC JSON payload preservation.

## Exact files changed

- `docs/admin/all-classes.js`
- `docs/admin/all-classes.html`
- `tests/all_classes_timezone.test.cjs`
- `Codex_Reply_Issue189_R2.md` (this communication-only receipt)

No generator or broad rebuild was run.

## Tests and checks

- `node --check docs/admin/all-classes.js` — passed.
- `node --test tests/all_classes_timezone.test.cjs` — 3 tests passed.
- `python -m unittest tests.test_all_classes_workspace` — 3 tests passed.
- Repeated `node --test tests/all_classes_timezone.test.cjs` with process `TZ=Pacific/Honolulu` — 3 tests passed; results remained Eastern and unchanged.
- `git diff --cached --check` before the substantive commit — passed.
- PR #191 Source integrity `truncation-guard` checks — passed.
- PR #191 Cloudflare Pages preflight checks — passed.
- PR #191 Cloudflare Pages preview — passed. This was treated separately from production GitHub Pages.

The HOT_SYNC payload test constructs the same record passed to `JSON.stringify(record)` in `saveClass()`, round-trips that JSON, and proves a winter owner entry of `08:15`/`11:45` reaches the request body as `2026-12-10T08:15:00-05:00` and `2026-12-10T11:45:00-05:00`. No authenticated production POST was made because that would create a real operational class.

## Deployment and production evidence

- Local validation: passed.
- Branch push: completed.
- PR merge: completed at 2026-09-11T18:33:16Z.
- GitHub Pages run: `34633917452`, successful for merge SHA `e1dc87fd4bf13254b12f2bc5b39d8bba2e836e44`.
- GitHub Pages deployment: `6399411243`, state `success` at 2026-09-11T18:34:10Z, environment URL `https://www.910cpr.com/`.
- Production HTML verification: `https://www.910cpr.com/admin/all-classes.html` referenced `/admin/all-classes.js?v=20260911-2`.
- Production asset verification: `https://www.910cpr.com/admin/all-classes.js?v=20260911-2` returned HTTP 200, `Last-Modified: Fri, 11 Sep 2026 18:34:04 GMT`, contained `America/New_York`, `easternWallTimeIso`, and the DST overlap rejection, and no longer contained the hard-coded HOT_SYNC `:00-04:00` write expression.

## Persistent-system evidence state

`PROVEN` for the repaired serializer being present in the production owner workspace: deterministic behavioral tests passed and the deployed, versioned asset was inspected after a successful production deployment. The broader authenticated owner-entry-to-database lifecycle was not mutated for this verification, so no new claim beyond the existing HOT_SYNC path is made.

Expected outcome: an accepted owner-entered wall time is posted with the correct Eastern offset for its date; DST gap/overlap entries are rejected before POST.

Success evidence: deterministic payload tests plus the production deployment and served-asset evidence above.

Failure condition: production HTML references another asset version, the served serializer is absent, or the deterministic timezone/payload tests fail. Existing GitHub Pages deployment status observes deployment failure; the focused repository test is the regression detector for serialization behavior.

Recovery path: rerun `node --test tests/all_classes_timezone.test.cjs`, inspect the versioned production asset, and redeploy the smallest corrected source change.

## Known unrelated state

The original checkout was dirty and was not modified. The isolated worktree showed an unrelated pre-existing/checkout artifact in `docs/Earl/index.html`, and the Python test created `tests/__pycache__/test_all_classes_workspace.cpython-312.pyc`. Neither was staged or committed.

## Remaining risk and next action

- Ambiguous fall-back times are deliberately rejected rather than asking the owner to select the first or second occurrence, matching the issue's fail-closed allowance.
- A live authenticated HOT_SYNC write was intentionally not performed because it would create a real class. The production request-body path is the same tested builder and serializer.
- Recommended next action for ChatGPT: inspect and acknowledge this receipt, then close issue #189 if the fail-closed overlap policy is accepted.
- User/account-level action required: none for this repair. A deliberate owner test class would be required only if an additional real database-write proof is desired.
