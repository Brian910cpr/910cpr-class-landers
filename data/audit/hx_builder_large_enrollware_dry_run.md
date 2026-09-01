# Hx-Builder Large Real Enrollware Dry Run

- Production mutation: **none**
- Migration applied: **no**
- Deployment: **none**
- Source population: 8,199
- Deterministic sample: 1,000
- Deterministic hash: `89bb622b765b616ea14b851ebad52e15b08befe3508ec41a0aef6abc7be2e530`
- Replay: `{"actions": {"idempotent_replay": 972}, "additional_assertions": 0, "additional_operations": 0}`

## Summary

```json
{
  "ambiguous_conflicting_facts": 669,
  "completions_reconstructed": 317,
  "credentials_cards_reconstructed": 317,
  "duplicate_candidates": 28,
  "people_created": 750,
  "people_matched": 29,
  "records_intentionally_excluded": 0,
  "registrations_created": 939,
  "registrations_matched": 0,
  "reschedules_reconstructed": 1,
  "sessions_created": 655,
  "sessions_matched": 0,
  "source_records_examined": 1000,
  "unresolved_identities": 3
}
```

## Explicit review queue

`{"completion_status_only": 581, "identity": 3, "inventory_product": 85}`

All remaining ambiguities are classified and routed to review. Unexplained mismatches: **0**.
