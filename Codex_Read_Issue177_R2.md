# Codex reply — Issue 177, round 2

- Timestamp: 2026-09-11T20:07:49-04:00 (America/New_York)
- Assignment: GitHub issue #177, Google Workspace durable record + recovery layer
- Branch: `codex/issue-177-local-mirror-r2`
- Substantive commit: `14c62b974163d691582df6d4e4ad41525a25938f`
- Pull request: https://github.com/Brian910cpr/910cpr-class-landers/pull/199
- Base/dependency PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/198
- Work-item state: `PR_OPEN`; overall issue remains externally `BLOCKED`
- Persistent-system evidence: `BUILT`

## Findings and dependency state

Facts:

- Issue #141 remains explicitly blocked by issue #140's account-level `HOT_SYNC_ADMIN_KEY` parity gate. This round did not alter #141's reviewed stack, schema, migrations, historical data, or production state.
- Issue #113 remains the communications/Gmail authority. No communications behavior was added here.
- A real Google mirror remains blocked by authorized least-privilege Google Workspace access, private Sheet/Drive destination IDs, and an authorized canonical Supabase snapshot/read path. None were available or used.
- PR #198 is open and green and supplies the `DurableRecordEnvelope v1` contract and deterministic exporter on which this round is stacked.
- The assigned primary checkout and the prior #177 worktree contained unrelated dirty `docs/Earl/index.html` state. The new worktree also reflected that generated-file difference after checkout. It was not staged, changed intentionally, committed, or pushed by this round.

Inference:

- The authenticated connection and real mirror/recovery proof cannot safely proceed without account authorization, but the adapter safety semantics can be built and tested locally without mutating any persistent external system.

## Work performed

- Added a local-only destination adapter that upserts by `(entity_type, canonical_id)` rather than row position.
- Added read-after-write content-hash verification for every record.
- Added deterministic reconciliation counts for matched, missing, extra, mismatched, and ambiguous states. Ambiguous is reserved and never silently repaired.
- Added append-only run audit and exception logs plus a latest `control.json` health receipt.
- Added stale-source classification using a configurable maximum snapshot age.
- Added fail-closed validation for export schema version, manifest hash, per-file hashes, entity counts, total count, record shape, and duplicate stable keys.
- Documented the local two-run command and the adapter boundary required for a future authenticated Sheets implementation.

## Exact files changed

- `scripts/apply_google_durable_mirror.py`
- `tests/test_apply_google_durable_mirror.py`
- `docs/google-durable-record-tranche-1.md`
- `Codex_Reply_Issue177_R2.md` (this receipt; communication-only follow-up commit)

## Tests and checks

- `python -m py_compile scripts/apply_google_durable_mirror.py scripts/export_google_durable_record.py` — passed.
- `python -m unittest tests.test_export_google_durable_record tests.test_apply_google_durable_mirror -v` — 11/11 passed.
- Repeat application proof: first synthetic run inserted 4 records; second run reported 4 unchanged, 0 inserted, 0 updated, 4 matched, and 0 exceptions.
- Behavioral coverage includes update without duplication, extra-record drift, read-after-write failure, stale source, tampered file, and tampered manifest.
- `git diff --check` on intended files — passed.
- No repository generator was run; generated public output count is zero.

Known unrelated failure/state: `docs/Earl/index.html` remains modified in the worktree and is intentionally excluded.

## Deployment and proof status

- Persisted locally: yes, in the separate named worktree.
- Changed in repo: yes, four intended files across the substantive and receipt commits.
- Validated locally: yes, using synthetic non-private records.
- Pushed: substantive branch/commit and this receipt branch tip.
- Merged: no.
- Deployed: no.
- Google/Supabase connected: no.
- Production data written: no.
- Outbound messages sent: no.

Persistent-system status remains **BUILT**, not CONNECTED, PROVEN, MONITORED, or HEALTHY. The last successful proof is the local synthetic 11-test run at this round's timestamp. The implemented stale condition is source age greater than the configured window or any verification/reconciliation exception. There is no scheduled observer yet; `control.json` and append-only logs are local evidence only, so observer health is not claimed.

## Remaining risks and next action

The local JSON adapter proves repository logic but not Google Sheets API behavior, quotas, concurrency, permissions, or Drive snapshot recovery. No real source counts or zero-drift claim is made.

Exact recommended next action after PR #198 and PR #199 review: provide an authorized least-privilege Google Workspace execution path and private Sheet/Drive IDs through runtime secrets, plus an authorized canonical Supabase snapshot/read path. Then implement the Sheets adapter behind the tested boundary, run it twice against a non-production mirror, require read-after-write verification and zero unexplained drift, and only then perform the portable Drive snapshot and clean recovery drill.

User/account-level action required: **yes** — authorize the Google Workspace and canonical source access without placing credentials, IDs, or private data in the public repository or issue. Issue #140's unrelated credential parity remains a separate owner/pause gate for #141 and must not be bypassed.
