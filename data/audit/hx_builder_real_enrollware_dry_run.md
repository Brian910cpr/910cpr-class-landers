# Hx-Builder Real Enrollware Historical Sample — Dry Run

**Result:** deterministic replay passed; production import remains blocked.

- Production mutation: **none**
- Migration applied: **no**
- Real source rows: 8,199; deterministic sample: 15
- First pass proposed operations/assertions: 71 / 49
- Exact replay additional operations/assertions: 0 / 0
- Replay decisions: `{"idempotent_replay": 15}`

## First-pass summary

```json
{
  "ambiguous_conflicting_facts": 4,
  "completions_reconstructed": 7,
  "credentials_cards_reconstructed": 5,
  "duplicate_candidates": 0,
  "people_created": 13,
  "people_matched": 0,
  "records_intentionally_excluded": 0,
  "registrations_created": 15,
  "registrations_matched": 0,
  "reschedules_reconstructed": 1,
  "sessions_created": 11,
  "sessions_matched": 0,
  "source_records_examined": 15,
  "unresolved_identities": 0
}
```

## Production/reference comparison

| Area | Sample proposal/evidence | Existing production |
| --- | ---: | ---: |
| People | 13 unique proposed | 0 matched sample identities |
| Sessions | 11 proposed | 0 matched sample class IDs |
| Registrations | 15 proposed | 0 historical registrations total |
| Completions | 7 | 0 |
| Credentials/cards | 5 | 0 |
| Reschedules | 1 | 0 |

## Classified mismatches

| ID | Classification | Area | Finding |
| --- | --- | --- | --- |
| M01 | importer deficiency | people | 13 unique historical identities in the sample matched zero production customers; batch-local duplicate identity reuse is now correct. |
| M02 | importer deficiency | sessions | 11 Enrollware class IDs in the sample matched zero production class_sessions; production has 352 historical sessions, but none cover these sampled IDs. |
| M03 | importer deficiency | registrations | 15 sampled participant/session memberships matched zero production registrations; production has zero registrations with historical_import_key. |
| M04 | importer deficiency | source identity | The student export contains no Enrollware registration ID or course ID, so the adapter uses a documented composite registration key and course-name evidence. |
| M05 | source-data ambiguity | completion | Four rows have Complete/Incomplete status without an eCard; Hx refuses to translate those status-only values into passed/failed completion facts. |
| M06 | importer deficiency | lifecycle | The sample supports 7 explicit completions, 5 credentials, and 1 reschedule, while production currently contains zero canonical completions, credentials, or reschedule lifecycle events. |
| M07 | schema/model gap | prepaid inventory | Three NHCSO rows carry the AHA-BLS-ECARD option and the trusted checkpoint says the cards use a customer-owned prepaid pool, but production lacks the proposed entitlement pool/event tables and canonical owner/product IDs remain unresolved. |
| M08 | schema/model gap | idempotency provenance | Exact replay is deterministic with a source fingerprint in the dry-run overlay, but lifecycle_import_records has no dedicated source_fingerprint column; persistence must store and query an equivalent immutable fingerprint before apply mode is approved. |
| M09 | identity-resolution deficiency | batch identity | The initial real run proposed one person per row (15 instead of 13); Hx was corrected to reuse email/phone identity within the batch and regression-tested. |

## Gate

BLOCKED until every mismatch is reviewed and fingerprint persistence plus canonical course/owner/product resolution are approved.

The detailed JSON contains PII-redacted decisions, operations, evidence assertions, and course/date/source reconciliation totals.
