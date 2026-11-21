# Operational evidence capture contract

`capture_operational_evidence` reuses `lifecycle_import_records`,
`lifecycle_evidence_assertions`, `ingest_jobs`, and `ingest_review_queue`.
It is callable only by server-side service credentials or privileged database
operators. It does not promote staged evidence into operational entities.

## Adapter input

Pass an account-scoped source system, immutable upstream identifier, source
timestamp, original JSON object, one or more categories, an extracted-facts
object, and an optional secure source reference. Preserve original bytes in
the JSON payload when exact byte recovery matters. A MIME tree is not a raw
RFC 2822 byte archive. Do not include mutable mailbox labels in source payloads.

Categories: people, classes, registrations, financial, credentials,
communications, operations, engineering. Several categories may apply.

The content fingerprint covers the original payload, timestamp, and reference.
Algorithm `sha256:postgres-jsonb-v1` hashes PostgreSQL's JSONB representation in
UTC; it is not a checksum of the original external file bytes. Store a separate
byte checksum in the payload when importing files.

## Behavior

- Identical source and interpretation return the original record/assertion IDs.
- A changed source version retains both originals and creates a predecessor link
  and conflict review. A source version change is a review signal, not proof of
  a semantic contradiction.
- A changed interpretation appends an assertion while preserving the original.
- Every new assertion enters the existing review queue with `needs_review`.
  The existing queued/retry AI worker does not claim these jobs.
- Capture does not match people, merge registrations, consume seats, write
  payments, send messages, issue credentials, or update public availability.
- Cross-source semantic reconciliation and entity linking are subsequent steps.

## Verification

Run `tests/operational_evidence_capture.sql` using a privileged SQL connection
against a database with the migration applied. The test rolls back its
synthetic evidence. Repeat with `SET LOCAL ROLE service_role` after `BEGIN`
to test the intended runtime role. Use separate database requests to verify
committed evidence survives request/session boundaries.

The SQL test checks replay, timezone equivalence, changed source and
interpretation handling, predecessor linkage, conflict queue, immutable content,
permissions, production entity counts, and complete dashboard status accounting.
It does not prove an application restart, source webhook delivery, continuous
worker operation, or notification delivery.

## Recovery and rollout

If capture misbehaves, revoke service execution first:

```sql
revoke execute on function public.capture_operational_evidence(
 text,text,timestamptz,jsonb,text[],jsonb,text) from service_role;
```

Preserve captured evidence and review items. Correct interpretations by
appending evidence; do not delete history or rerun operational imports.
Restore execution only after the regression tests pass.

The dashboard accounts for both `complete` and `completed`, reports review and
unknown states, and exposes processing older than 15 minutes and queued/retry
work overdue by one hour. These are diagnostic thresholds. The view itself is
not a scheduled observer, alert delivery mechanism, or proof of source coverage.
