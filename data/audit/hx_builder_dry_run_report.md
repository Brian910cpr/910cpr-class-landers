# Hx-Builder contract validation and dry-run report

Date: 2026-09-01
Branch: `codex/stabilization-integration`
Mode: **DRY RUN ONLY**
Production mutation: **none**
Schema deployment: **none**

## Authority

Hx-Builder targets the canonical LanderWare authority already in production:

`customers -> registrations -> class_sessions`

It proposes calls to the shared `register_participant` and `move_registration` contracts. It does not create a parallel person, session, registration, roster, completion, credential, or history database.

## Finalized contracts

### 1. Identity and idempotency

- Every input has `source`, `source_record_id`, and an import batch.
- Existing import records suppress replay across batches.
- Duplicate source records inside one batch are reported and skipped.
- External aliases resolve before exact normalized email/phone evidence.
- Conflicting email/phone matches enter review; names alone never merge people.
- Proposed registration idempotency keys are `hx:<source>:<source_record_id>`.
- Session identities preserve source-specific IDs while resolving to canonical `class_sessions`.

### 2. Reschedule lineage

- Hx-Builder reconstructs a move only from explicit origin-session evidence and a reason.
- The proposed operation retains customer, origin session, destination session, timestamp, reason, source, source record, and import batch.
- The canonical move contract retains the original registration and creates/links the target registration through `registration_supersessions`.
- A move does not imply attendance or completion.

### 3. Completion and credential handling

The worker emits separate evidence types for:

- registration;
- attendance;
- completion;
- credential/card;
- payment;
- product/accessory fulfillment;
- requirements;
- inventory entitlements.

A completion is proposed only when evidence explicitly says `passed`, `failed`, or `incomplete`. Registration status—even “Completed” from an Enrollware row—is not converted into participant completion. A credential requires a number or issuance timestamp. Product fulfillment and prepaid inventory consumption remain independent facts.

### 4. Provenance, ambiguity, and import batches

The undeployed migration adds append-only:

- `lifecycle_evidence_assertions`;
- `inventory_entitlement_pools`;
- `inventory_entitlement_events`.

Every assertion retains source, source record, import batch, original source value, asserted value, confidence state/score, source timestamps, effective time, reconciliation state, and optional supersession. Higher-quality evidence creates a new assertion linked by `supersedes_assertion_id`; it cannot overwrite the earlier evidence.

All proposed tables are service-only, RLS-protected, and append-only. The migration was parsed against the production schema inside a transaction and rolled back. It was not deployed.

## Generic prepaid inventory model

A pool has a product, owner type, owner identity, unit type, source record, batch, and provenance. Its balance is reconstructed from append-only acquired, allocated, consumed, released, expired, corrected, and reconciled events.

The fixture demonstrates a customer-owned prepaid eCard pool consumed by a participant registration. Nothing in the schema or worker is NHCSO-specific.

## Representative dry run

Input: `tests/fixtures/hx_builder_sample.json`
Reference: `tests/fixtures/hx_builder_reference.json`
Machine-readable output: `data/audit/hx_builder_dry_run_report.json`

| Measure | Count |
|---|---:|
| Source records examined | 9 |
| People matched | 1 |
| People proposed for creation | 1 |
| Sessions matched | 2 |
| Sessions proposed for creation | 1 |
| Registrations matched | 2 |
| Registrations proposed for creation | 1 |
| Reschedules reconstructed | 1 |
| Completions reconstructed | 1 |
| Credentials/cards reconstructed | 1 |
| Unresolved identities | 1 |
| Ambiguous/conflicting facts | 1 |
| Duplicate candidates | 1 |
| Records intentionally excluded | 1 |

The single unresolved identity deliberately combines one customer's email with another customer's phone. Hx-Builder stops that record for review. The duplicate is a repeated Enrollware source record. The excluded row is explicitly marked as a test/staff record.

## Reconciliation by course, date, and source

| Course | Date | Source | Examined | Reconciled | Duplicate | Unresolved | Excluded |
|---|---|---|---:|---:|---:|---:|---:|
| BLS | 2024-01-01 | Enrollware | 2 | 1 | 1 | 0 | 0 |
| BLS | 2024-02-01 | Atlas | 1 | 1 | 0 | 0 | 0 |
| BLS | 2024-02-01 | Class document | 2 | 2 | 0 | 0 | 0 |
| BLS | 2024-02-01 | Stripe | 1 | 1 | 0 | 0 | 0 |
| BLS | 2024-03-01 | Gmail | 1 | 0 | 0 | 1 | 0 |
| Heartsaver | 2023-05-10 | Legacy CSV | 1 | 1 | 0 | 0 | 0 |
| Unknown | Unknown | Legacy CSV | 1 | 0 | 0 | 0 | 1 |

The report contains 13 proposed canonical operations and 7 append-only evidence assertions. No operation was executed.

## Validation

- 9 Hx-Builder contract tests passed.
- Existing Enrollware normalization is used through an adapter rather than copied.
- Enrollware adapter test proves registration status does not infer completion.
- Evidence/inventory migration passed a production-schema transaction and was rolled back.
- Python syntax compilation passed.
- Dry-run output is deterministic for the supplied sample/reference pair.

## Approval boundary

Do not deploy the evidence/inventory migration and do not execute proposed operations until a dry run against an approved real historical sample is reviewed. The current report proves the contracts and worker behavior using synthetic representative evidence; it is not approval to import production history.
