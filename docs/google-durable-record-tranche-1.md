# Google durable record and recovery layer — tranche 1 contract

Issue: #177
Status: backend contract and local dry-run exporter only; no Google write or production cutover

## Authority and direction

LanderWare/Supabase remains the operational source. Google Workspace is the one-way durable mirror and recovery layer. Sheet row positions are never identities. A later writer must upsert on `(entity_type, canonical_id)`, verify the resulting destination hash, and record any exception instead of silently resolving ambiguity.

Issue #141 remains the historical reconciliation/backfill authority. This tranche consumes canonical records; it does not invent another historical importer or alter the paused #141 stack. Issue #113 remains the communications authority; Gmail message/thread provenance is not duplicated here.

## Repository source and integration inventory

The inventory below is based on repository code/schema, not a claim about current production row counts.

| Surface | Existing authority | Current integration state |
|---|---|---|
| Canonical people and organizations | `landerware_people`, `landerware_organizations`; identity helper and `landerware_person_identities` | Checked-in Supabase migrations; exact production counts require authenticated read access |
| Sessions and registrations | `landerware_sessions`, `landerware_registrations`; historical bridge remains governed by #141 | Checked-in Supabase migrations; exporter uses stable UUIDs |
| Credentials | `landerware_credentials` | Checked-in Supabase migration |
| Financial references | `landerware_retail_orders` | Only stable references, amounts, currency, lifecycle status, and timestamps are exported; no checkout URL, idempotency secret, or payment payload |
| Google Calendar | `scripts/export_calendar_snapshots.py`, `data/config/calendar_sources.json`, `.github/workflows/refresh-admin-availability.yml` | Read-only public/private ICS snapshot path exists; it is scheduling input, not the historical record destination |
| Gmail | `landerware_messages` schema and provider fields; issue #113 | Durable provider boundary exists; repository has no active Gmail ingestion worker in this inventory |
| Google Drive | `landerware_documents.storage_provider/storage_reference` can retain references | No authenticated Drive snapshot writer found |
| Google Sheets | Bootstrap workbook described by issue #177 | No repository Sheet writer found; folder and Sheet IDs must remain outside this public repo |
| Apps Script | `scripts/pay_balance_lookup_apps_script.js` | Narrow balance-lookup script; not a durable-record mirror |
| OAuth/config | Calendar source configuration plus runtime secrets outside git | No reusable Google Workspace OAuth client for Drive/Sheets was found in tracked code |

Concrete source row counts are intentionally not guessed. The dry-run manifest reports exact input/output counts when run against an authorized canonical snapshot. No production credentials or private payloads were available or used in this tranche.

## Envelope and Google mapping

The versioned schema is `docs/contracts/durable_record_envelope.v1.schema.json`. `content_hash` is SHA-256 over canonical JSON containing `entity_type`, `canonical_id`, `source_system`, `source_id`, `schema_version`, `payload_strategy`, `payload`, and `provenance`. It excludes `mirrored_at` and `reconciliation_status`, so retries and reconciliation state changes do not create false content drift.

| Entity | Canonical table | Bootstrap Sheet tab | Stable key |
|---|---|---|---|
| session | `landerware_sessions` | Sessions | `session:<id>` |
| registration | `landerware_registrations` | Registrations | `registration:<id>` |
| person | `landerware_people` | People | `person:<id>` |
| organization | `landerware_organizations` | Organizations | `organization:<id>` |
| credential | `landerware_credentials` | Credentials | `credential:<id>` |
| financial_ref | `landerware_retail_orders` | FinancialRefs | `financial_ref:<id>` |

The Google Control tab should hold contract version, last attempted/successful run IDs, counts, and snapshot hash. AuditLog should append verification/reconciliation events. Neither tab is implemented by the read-only exporter.

## Local dry-run

The exporter accepts a JSON object keyed by the six canonical table names. Input and output can contain customer data and must stay outside git; `data/runtime/google_durable_record/` is ignored.

```powershell
python -m scripts.export_google_durable_record --input-json <private-canonical-snapshot.json> --output-dir data/runtime/google_durable_record/run-001 --mirrored-at 2026-09-11T22:00:00Z
```

It writes sorted JSONL files plus `manifest.json`, never contacts Google, and never mutates Supabase. Repeating with identical input and `--mirrored-at` produces byte-identical output. Fields are allowlisted; unknown source fields are omitted.

## Local stable-key mirror harness

`scripts/apply_google_durable_mirror.py` applies an exported run to a local JSON destination. This is a non-production adapter harness, not a Google Sheets writer. It upserts by `(entity_type, canonical_id)`, reads every record back, compares content hashes, writes an append-only audit log and durable exception log, reconciles missing/extra/mismatched records, and marks a source snapshot stale when its age exceeds the configured window.

```powershell
python -m scripts.apply_google_durable_mirror --export-dir data/runtime/google_durable_record/run-001 --mirror-dir data/runtime/google_durable_record/local-mirror --run-at 2026-09-11T23:00:00Z
```

Run the command twice with the same export. The second receipt must report all records as `unchanged`, zero exceptions, and all source records `matched`. `control.json` is the latest health receipt; `audit_log.jsonl` preserves every run; `exceptions.jsonl` is created when verification or reconciliation fails. All of these files may contain identifiers or PII and must stay in the ignored runtime directory.

The future authenticated Sheets adapter should implement the same `upsert`, `read`, and `read_all` boundary. A successful API response alone is insufficient: read-after-write verification and reconciliation remain mandatory.

## Portable recovery snapshot and local drill

Package a validated dry-run export into a deterministic portable ZIP, then restore it into a new empty local structure:

```powershell
python -m scripts.durable_record_recovery create --export-dir data/runtime/google_durable_record/run-001 --archive data/runtime/google_durable_record/recovery.zip
python -m scripts.durable_record_recovery restore --archive data/runtime/google_durable_record/recovery.zip --recovery-dir data/runtime/google_durable_record/recovery-drill
```

The archive carries a hash manifest for the exporter manifest and all six JSONL entity files. Restore rejects missing, extra, duplicate, unsafe, or hash-mismatched members; refuses to overwrite a nonempty destination; validates the original exporter contract; rebuilds a clean stable-key local store; and writes `recovery_receipt.json` only after zero-exception reconciliation.

Real archives may contain PII. Keep them in ignored private runtime storage and upload them only to an authorized private Drive destination. The repository implementation and synthetic drill do not prove Drive upload, retention, access control, or restoration from Drive.

## Reconciliation and recovery gates still open

- Build an authenticated, least-privilege source reader or produce an authorized canonical snapshot.
- Obtain Google OAuth/service-account authorization and private destination identifiers.
- Implement the authenticated stable-key Sheets adapter using the locally tested verification/reconciliation boundary.
- Run twice against a non-production mirror and prove no duplicate rows.
- Upload a validated portable snapshot to an authorized private Drive destination and repeat the clean recovery drill from the downloaded artifact.
- Reconcile Calendar representation without projecting thousands of historical sessions.
- Add CI around the local contract/exporter; authenticated integration validation must not expose PII or secrets.

Until those gates pass, the persistent-system evidence state is **BUILT**, not CONNECTED or PROVEN.
