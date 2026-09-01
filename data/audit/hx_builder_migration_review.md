# Hx-Builder Migration Review

**READY FOR MIGRATION REVIEW**

No migration was applied, no production history was imported, and nothing was deployed.

## Fixed 1,000-record dry run

```json
{
  "canonicalization": {
    "course_resolved": 915,
    "end_at_resolved": 921,
    "instructor_resolved": 612,
    "location_resolved": 300,
    "sessions_ready": 186,
    "sessions_review_required": 741,
    "start_at_resolved": 927
  },
  "deterministic_hash": "dbd53d21d13de745164b4021b5dd33a15586d6ad5961dccab9350aaaedd0b0d5",
  "duplicate_candidates": 28,
  "identity_ambiguities": 3,
  "independent_output_identical": true,
  "replay": {
    "additional_assertions": 0,
    "additional_operations": 0
  },
  "review_required": {
    "completion_status_only": 581,
    "identity": 3,
    "session_course": 12,
    "session_end_at": 6,
    "session_instructor": 315,
    "session_location": 627
  },
  "summary": {
    "ambiguous_conflicting_facts": 1544,
    "completions_reconstructed": 15,
    "credentials_cards_reconstructed": 15,
    "duplicate_candidates": 28,
    "people_created": 750,
    "people_matched": 29,
    "records_intentionally_excluded": 0,
    "registrations_created": 228,
    "registrations_matched": 0,
    "reschedules_reconstructed": 1,
    "sessions_created": 186,
    "sessions_matched": 0,
    "source_records_examined": 1000,
    "unresolved_identities": 3
  },
  "unexplained_mismatches": 0
}
```

The review queue is intentional and fail-closed: unresolved course, location, instructor, or timing facts do not create an insert-ready session.

## Inventory product resolution

- Observed prepaid product evidence: `{"AHA-BLS-ECARD": 85}`
- Inventory events reaching proposal after session gates: **14**
- AHA-BLS-ECARD resolves to the proposed canonical AHA BLS Provider eCard product (25-3001; legacy alias 20-3001).
- AHA-HS-FACPRAED-ECARD resolves to the proposed canonical Heartsaver First Aid CPR AED eCard product (25-3002; legacy alias 20-3002).
- Products still blocked in this sample: **none**. Unencountered AHA eCards remain reference-only until product-master pricing approval.

## Fingerprint migration review

- **uniqueness:** (source_system, source_record_id, entity_type, source_fingerprint_algorithm, source_fingerprint)
- **indexes:** global exact-version unique index; source identity lookup index; predecessor lookup index
- **source version behavior:** algorithm is part of identity; algorithm changes do not silently collide
- **changed record behavior:** new fingerprint is a new record, linked to predecessor and review-required
- **supersession:** predecessor_import_record_id preserves the version chain; accepted evidence uses supersedes_assertion_id
- **batch relationship:** every import record remains attached to one lifecycle_import_batch
- **rollback:** batch/derived facts are reversed with append-only correction/reversal records; fingerprints are retained
- **existing records:** legacy rows are backfilled with sha256-jsonb-text-legacy-v1 and remain distinguishable from canonical-json-v1
- **rolled back production schema test:** passed; all proposed objects/columns/products were absent after ROLLBACK
