# Hx-Builder Nine-Mismatch Resolution

**Recommendation: NOT READY**

No migration was applied, no production data was mutated, and nothing was deployed.

| ID | Classification | Original evidence | Current / expected interpretation | Correction | Required | Status |
| --- | --- | --- | --- | --- | --- | --- |
| M01 | importer deficiency | 13 unique historical identities; zero exact-sample production customer matches. | Propose canonical customers and reuse identity within the batch. Expected: Match a unique canonical customer by durable alias or normalized email/phone; otherwise propose one customer per identity. | Batch identity reuse is fixed; production aliases remain the durable future match path. | code + future migration apply | resolved in dry-run contract |
| M02 | importer deficiency | 11 exact-sample and 655 large-sample Enrollware class IDs matched no production class_session. | Propose one source session per unique external class ID. Expected: Reuse external_class_id when present; otherwise reconstruct only after canonical course/location/instructor and timing are resolved. | Session proposals are deduplicated; insert/apply remains gated on required canonical FK normalization. | source normalization + manual review | review gate |
| M03 | importer deficiency | Production has zero historical registrations and none matched either sample. | Propose participant/session membership after person and session resolution. Expected: One canonical registration per person/session with external/composite source identity retained. | Registration proposals now reuse batch identities/sessions and exact replays are suppressed durably by source fingerprint. | code + future migration apply | resolved in dry-run contract |
| M04 | importer deficiency | Student report has no Enrollware registration ID or course ID. | Use SHA-256(identity|class|course date|registration date) as composite record/registration identity and retain course display evidence. Expected: Prefer native IDs; where absent, use a documented deterministic composite and treat collisions as duplicate candidates. | Composite strategy is explicit; 28 large-sample collisions are routed as duplicate candidates, not double attendance. | source normalization + manual review | resolved with review routing |
| M05 | source-data ambiguity | Complete/Incomplete status appears without independent completion or card evidence. | Status-only values are review items; eCard-backed rows alone create completion/credential assertions. Expected: Never infer passed/failed completion merely from registration status. | Removed status-only completion reconstruction and route all such rows to manual review. | code + manual review | resolved |
| M06 | importer deficiency | Production contains zero canonical completions, credentials, and reschedule events. | Create separate proposed facts only when explicit evidence exists. Expected: Registration, attendance, completion, credential, reschedule, and fulfillment remain distinct. | Exact sample reconstructs 5 eCard-backed completions/credentials and one explicit reschedule without fake origin attendance. | code + future migration apply | resolved in dry-run contract |
| M07 | schema/model gap | NHCSO is canonical organization_key=nhcso; production has no canonical AHA BLS eCard product. | Resolve owner/product/pool only by unique canonical keys or curated aliases; unresolved product stops the event. Expected: Reuse canonical organization, product, and equivalent owner/product/unit pool; never invent or fuzzy-match them. | Owner resolves uniquely; 3 exact/85 large product facts route to review. A product-master decision is required before pool creation. | manual review + canonical product data; schema only after approval | blocking |
| M08 | schema/model gap | lifecycle_import_records uniqueness was batch-local and stored no fingerprint. | Proposed migration adds source_system and SHA-256 source_fingerprint plus global exact-fingerprint uniqueness and source-identity lookup. Expected: Exact source version is durable across runs/machines/batches; changed fingerprint for the same identity routes to review and preserves both versions. | Unapplied migration and worker now implement exact-version replay/conflict semantics. | schema + code | ready for schema review, not applied |
| M09 | identity-resolution deficiency | Initial exact run proposed 15 people for 13 identities; large production match includes ambiguous duplicate canonical identities. | Reuse batch email/phone identity; conflicting or multiple canonical candidates stop for review. Expected: Never select arbitrarily; create at most one proposed person per unique identity and preserve aliases/candidates. | Batch reuse fixed; large sample matched 29 people and routed 3 ambiguous identities to review. | code + manual review | resolved with review routing |

## Exact-sample verification

- Deterministic hash: `9a7f25762864fb639cb54bbc1f860d489bc428d2962053e3242b985848ed2cc9`
- Replay: `{"actions": {"idempotent_replay": 15}, "additional_assertions": 0, "additional_operations": 0}`
- Review queue: `{"completion_status_only": 6, "inventory_product": 3}`
- Unexplained mismatches: **0**

## Blocking items

- No canonical AHA BLS eCard product/product alias exists, so prepaid pool/event resolution must stop.
- Historical session proposals still require canonical course, location, instructor, and complete timing normalization before apply mode.
- The durable fingerprint migration has not been reviewed or applied; production cannot yet enforce cross-batch replay safety.
