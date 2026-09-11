# Codex Reply: Issue 180

- Timestamp: 2026-09-11T01:27:00Z
- Branch: `codex/google-durable-recovery`
- Substantive branch SHA: `acca07f821ae7f192fc3de25808edcc3dfc91da2`
- Pull request: #181
- Work-item state: `PR_OPEN` (draft)
- Persistent-system evidence state: `CONNECTED`

## Findings

The Google durable-record bootstrap existed but contained headers only. A live read of the production LanderWare Supabase project succeeded, and the resulting control counts/timestamps were written to the Google Master Ledger. The newest observed core-table activity was September 8, so the ledger was marked `STALE_SOURCE_ACTIVITY` rather than healthy.

The repository had source-side snapshot and reconciliation patterns but no Google-bound production exporter, no Drive archive verification, and no scheduled stale-run evidence.

## Work performed

- Added a daily/manual read-only Supabase-to-Google Drive exporter.
- Added exact-count pagination and fail-closed partial-export handling.
- Added a content-addressed ZIP containing per-entity gzipped JSONL streams.
- Added SHA-256 archive and entity round-trip checks.
- Added Google Drive size and MD5 verification after upload.
- Added a separate reconciliation receipt and non-PII Actions health artifact.
- Added the persistent proof, cadence, staleness, observer, recovery, and escalation contract.

## Files changed

- `.github/workflows/google-durable-snapshot.yml`
- `scripts/export_google_durable_snapshot.py`
- `tests/test_export_google_durable_snapshot.py`
- `docs/operations/google-durable-recovery.md`

## Validation

- `python -m unittest tests.test_export_google_durable_snapshot`: 5 tests passed.
- `python -m py_compile scripts/export_google_durable_snapshot.py`: passed.
- Workflow YAML safe-load: passed.
- Live Supabase table inventory/count query: passed.
- Live Google Master Ledger Control write/readback: passed.

## Deployment and proof status

- Local validation: passed.
- Branch pushed through the GitHub connector: yes.
- Pull request: open as draft.
- Merged: no.
- Scheduled workflow deployed: no.
- Real immutable production archive in Drive: not yet.
- Last end-to-end proof: none. Current state remains `CONNECTED`, not `PROVEN`.

## Stop condition and next action

Account-level Google authority is required to provide a service-account JSON credential as GitHub Actions secret `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON` and share the Raw Snapshots and Reconciliation Reports folders with that service-account email. Do not paste the credential into GitHub issues or chat.

After the credential is configured: dispatch the draft workflow, verify the first real archive and reconciliation receipt in Drive, then promote the evidence state to `PROVEN` and continue with ledger population and recovery reconstruction testing.
