# ChatGPT handoff: issue #136 data boundaries

## Primary finding

Operational session truth is split across external/durable records and generated projections. The September 19 regression in `tests/test_canonical_schedule_hot_sync.py` proves that scheduled durable LanderWare sessions must reserve Brian/location availability even before Class Report absorption, while cancelled records must remain explainable without blocking inventory. `docs/data/schedule_future.json` remains the authoritative **public inventory contract**, but is not the complete operational or historical session ledger.

The complete inventory wording is in `data/audit/data_inventory_issue_136.md`; the authoritative ownership and reference rules are in `data/audit/canonical_silo_map_issue_136.md`.

## Contract and fixture

- Schema: `data/contracts/session_bundle.schema.json`
- Generator: `scripts/build_session_bundle.py`
- Adversarial source evidence: `data/fixtures/september_19_source_records.json`
- Generated export: `data/fixtures/session_bundle_2026-09-19.json`
- Tests: `tests/test_session_bundle.py`

Stable IDs are deterministic SHA-256-derived, type-prefixed IDs based on object kind, source system and immutable source ID. Cross-silo relationships use IDs; every imported session/registration retains source references.

## September 19 exact behavior

- 09:00–11:00 Hendersonville Family Dental: scheduled; reserves Brian and location.
- 11:00–14:00 Little Leaps: scheduled; reserves Brian and location.
- 14:00–16:00 Accelerated Academy / Hendersonville Family Dental: cancelled; retained in the bundle; does not reserve resources.
- Registration rows are absent from the regression evidence. The bundle records `registrations_not_present`; an empty exported array must not be interpreted as confirmed zero participants.
- Canonical Course Master IDs and the original source-observation timestamp are also explicitly missing.

## Validation performed

```text
python scripts/build_session_bundle.py --generated-at 2026-09-04T00:00:00Z
Wrote 3 sessions to .../data/fixtures/session_bundle_2026-09-19.json

python -m py_compile scripts/build_session_bundle.py tests/test_session_bundle.py

python -m unittest tests.test_session_bundle tests.test_canonical_schedule_hot_sync
........
Ran 8 tests in 0.612s
OK

python -m json.tool <each new JSON file>
JSON syntax: OK
```

Full Draft 2020-12 schema execution was not run because the local environment does not provide the optional `jsonschema` or Ajv package. JSON syntax, generator behavior, stable identifiers, references and September 19 occupancy semantics were validated locally without adding a dependency.

## Changed files

- `data/audit/data_inventory_issue_136.md`
- `data/audit/canonical_silo_map_issue_136.md`
- `data/audit/chatgpt_handoff_issue_136.md`
- `data/contracts/session_bundle.schema.json`
- `data/fixtures/september_19_source_records.json`
- `data/fixtures/session_bundle_2026-09-19.json`
- `scripts/build_session_bundle.py`
- `tests/test_session_bundle.py`

## Open questions and next slice

1. Confirm the actual Supabase `class_sessions` schema/migrations in the LanderWare repository or connected project; this repository only exposes its snapshot integration and related D1 portal schema.
2. Promote durable registration/participant links into the Session Bundle once source rows are available; never infer participants from schedule counts.
3. Decide and persist canonical organization/location identifiers before importing historical bundles.
4. Add a reconciliation importer as a separate slice. It should dry-run conflicts first and must never write production data merely to make an export clean.

## Worktree caveat

On case-insensitive Windows storage, current `main` checks out five case-colliding generated HTML pairs (`docs/ACLS.html`/`docs/acls.html`, etc.) as unrelated working-tree modifications. They are intentionally excluded from this change and must not be staged.
