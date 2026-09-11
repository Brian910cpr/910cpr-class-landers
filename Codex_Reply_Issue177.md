# Codex reply — Issue 177

- Timestamp: 2026-09-11T19:47:39-04:00 (America/New_York)
- Assignment: GitHub issue #177, Google Workspace durable record + recovery layer
- Branch: `codex/issue-177-durable-record-tranche1`
- Substantive commit: `374f0737bc4e651d9d466763af9e6392f1c92efa`
- Pull request: https://github.com/Brian910cpr/910cpr-class-landers/pull/198
- Work-item state: `PR_OPEN`
- Persistent-system evidence: `BUILT`

## Findings

Facts:

- Issue #141 is the historical reconciliation authority and is explicitly paused while issue #140's account-level credential-parity blocker remains unresolved. This tranche did not mutate that stack.
- Issue #113 remains the communications/Gmail authority. This tranche did not create a competing Gmail identity or message model.
- The repository already defines canonical `landerware_*` people, organizations, sessions, registrations, credentials, document references, and retail-order financial references.
- Repository Calendar snapshot support exists. No active repository Google Sheets durable-mirror writer, Drive recovery-snapshot writer, or reusable Google Workspace OAuth client was found.
- No production canonical row count is claimed. No authenticated production source read was performed.

Inference:

- Contract and deterministic-intermediate work can proceed safely without the blocked historical backfill or Google account authorization, but a real mirror/reconciliation/recovery proof cannot.

## Work performed

- Defined versioned `DurableRecordEnvelope v1` JSON Schema with stable identity, source/provenance, content hash, reconciliation state, and allowlisted inline payload strategy.
- Documented canonical entity-to-bootstrap-Sheet mapping, existing Google integration surfaces, one-way authority boundaries, local dry-run use, and remaining acceptance gates.
- Added a deterministic read-only exporter for Sessions, Registrations, People, Organizations, Credentials, and FinancialRefs.
- Exporter sorts by canonical ID, emits stable JSONL and a hash/count manifest, excludes unknown source fields, and performs no network or upstream write.
- Ignored PII-bearing runtime output and Python bytecode.

## Exact files changed

- `.gitignore`
- `docs/contracts/durable_record_envelope.v1.schema.json`
- `docs/google-durable-record-tranche-1.md`
- `scripts/export_google_durable_record.py`
- `tests/test_export_google_durable_record.py`
- `Codex_Reply_Issue177.md` (this receipt; separate receipt commit)

The checkout-generated `docs/Earl/index.html` working-tree difference is unrelated and was not staged or committed.

## Validation

- `python -m unittest tests.test_export_google_durable_record -v` — 4/4 passed.
- `python -m py_compile scripts/export_google_durable_record.py` — passed.
- JSON parse of `docs/contracts/durable_record_envelope.v1.schema.json` — passed.
- `git diff --check` on intended content — passed after removing one Markdown trailing-space defect.
- Determinism test proves byte-identical output for identical input and fixed `--mirrored-at`.
- Allowlist test proves an unknown synthetic source field is omitted.
- Fail-closed tests cover missing IDs and invalid table shapes.

Known unrelated failure/state: isolated checkout retains a 2-line checkout-generated difference in `docs/Earl/index.html`; it is absent from both intended commits.

## Deployment and proof status

- Locally validated: yes.
- Branch pushed: yes.
- PR open: #198; mergeable when checked, CI initially in progress.
- Merged: no.
- Deployed: no.
- Supabase source connected: no.
- Google destination connected: no.
- Real mirror run: no.
- Reconciliation/idempotency against Google: no.
- Drive recovery snapshot/drill: no.
- Last successful end-to-end proof: none; only the local deterministic exporter is proven by synthetic tests.

Expected eventual outcome: canonical LanderWare changes are mirrored once to stable-key Google rows, verified by read-after-write hash comparison, periodically snapshotted to Drive, and recoverable into a clean structure.

Failure/staleness condition and observer: not yet implemented. A future connected process must treat a late run, source/destination count or hash drift, verification exception, stale monitor heartbeat, or failed recovery snapshot as unhealthy. Brian is not to be the routine observer.

## Exact blockers and next action

Account/user action required: **yes**, before a real Google mirror run. An authorized owner/operator must provide a least-privilege Google Workspace authorization path and the private Drive/Sheet destination identifiers outside this public repository. An authorized canonical Supabase snapshot or least-privilege read credential is also required for production counts and a real dry run.

Repository-side next action after review: merge PR #198, then build the source-reader and non-production Google writer with stable-key upsert, read-after-write verification, durable exception receipts, and stale-run monitoring. Run it twice against the bootstrap mirror to prove idempotency before any authoritative or bidirectional behavior. Then create a portable Drive snapshot and perform a clean local recovery drill.

Do not call issue #177 complete: Google connection, mirror execution, zero-unexplained-drift reconciliation, repeat-run proof, recovery snapshot/drill, and monitoring remain open.
