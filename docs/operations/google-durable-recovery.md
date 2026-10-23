# Google Durable Recovery

## Purpose

Google Workspace is the independent business-record and recovery layer. LanderWare/Supabase remains the operational source. This process copies production records out of Supabase without changing them, packages them into a content-addressed archive, uploads that archive to Google Drive, and writes a separate reconciliation receipt.

Private snapshot archives must never be committed to GitHub or uploaded as GitHub Actions artifacts.

## Proof contract

- **Expected outcome:** one complete, verified production archive appears in `LanderWare Durable Record/01 Raw Snapshots`, with a corresponding JSON receipt in `02 Reconciliation Reports`.
- **Cadence:** daily at 06:17 UTC, plus manual dispatch when required.
- **Success evidence:** Drive upload returns a matching byte count and MD5 checksum; the archive passes SHA-256, gzip, row-count, and internal round-trip verification; the reconciliation receipt records the Drive file ID and per-entity counts/hashes.
- **Stale condition:** no successful reconciliation receipt within 26 hours.
- **Observer:** the scheduled GitHub Actions workflow and its non-PII health artifact.
- **Observer health:** a workflow run exists for the expected daily window, including explicit failure output when extraction or upload fails.
- **Recovery path:** rerun `Google durable snapshot`; if it fails, use its health artifact to distinguish Supabase extraction, partial-count, archive-integrity, Google authentication, and Drive upload failures.
- **Escalation boundary:** Codex can repair repository code and retry runs. A Google administrator is required only to create/rotate the service-account credential, share the two target folders with that service account, or restore revoked Google access.

## Required GitHub Actions secrets

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON`

The Google value is the full service-account JSON credential. Do not paste it into an issue, commit, workflow file, or chat transcript.

The service-account email must have Editor access to both target folders:

- Raw snapshots: `1qdy514zfz53Ch-yQ1KIBHDhqD801ezNE`
- Reconciliation reports: `1r11x64lvNiUDLsdM766Q4tlYrQtHsGRB`

## Current entity scope

- `class_sessions`
- `registrations`
- `customers`
- `organizations`
- `participant_credentials`
- `class_session_audit`

Each table is fetched in deterministic `id` order and paginated at 1,000 rows. The PostgREST exact total must match the rows retrieved or the export fails closed before upload.

## Evidence states

- `BUILT`: exporter and workflow exist and tests pass.
- `CONNECTED`: a live Supabase read and a Google ledger write have both succeeded.
- `PROVEN`: the first complete archive and reconciliation receipt are verified in Drive.
- `MONITORED`: the scheduled run and stale-run observer have completed at least one expected cycle.
- `HEALTHY`: a successful end-to-end archive is newer than 26 hours and the observer's expected run is present.

Do not advance the status based only on a merge or deployment.
