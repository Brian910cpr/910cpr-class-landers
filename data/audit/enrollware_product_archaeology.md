# Enrollware product archaeology

## Executive finding

Enrollware’s mature advantage is not its menu count. It is its accumulated handling of lifecycle exceptions: money arriving without a registration, cards existing in Atlas without local confirmation, moved students, partial refunds, recycled codes, reopened rosters, archived entities, failed communications, capacity shared across listings, and user access that changes without erasing history.

LanderWare already has the better foundation in several places: canonical participant/session identity, provenance-preserving historical evidence, durable import fingerprints, explicit historical unknowns, location scheduling status, supersession lineage, and entitlement inventory events. Its main risk is **operational incompleteness around those records**. A schema that can tell the truth is not yet a complete replacement unless Customer Service, instructors and administrators can safely perform the common and exceptional actions.

The correct product shape is one set of authoritative entities—Person, Registration, Session, Order/Payment, Requirement/Evidence, Product/Fulfillment, Completion and Credential—with persona-specific actions in shared workspaces. Separate Retail, Corporate, Instructor and Admin registration implementations would recreate synchronization problems Enrollware’s own pages reveal.

## Evidence and method

- Authenticated Admin UI explored visibly and strictly read-only: approximately 45 distinct list/detail/settings/report screens.
- Complete Help Center tree inventoried: 200 articles; 68 lifecycle, exception, troubleshooting, security and integration articles reviewed in full.
- 30 tenant notifications reviewed and 345 dated What's New entries inventoried.
- Approximately 214 meaningful controls/actions harvested and deduplicated into 40 operational concepts.
- Current LanderWare status assessed from canonical migrations, functions, tests and audit artifacts in this repository. Old parallel `landerware_*` tables were not treated as current production authority.

No setting was saved, record changed, message sent, card issued, payment touched, import triggered, or bulk action entered. No credentials or participant PII were committed.

## What years of product development discovered

1. **Registration is a relationship, not a form.** Intake, payer, participant, session, requirements, products and history must remain linked through rescheduling and renewal.
2. **Operational truth is multi-state.** Paid, registered, attended, completed, issued, emailed and fulfilled are distinct facts.
3. **Recovery paths are core product.** Manual payment association, card reconciliation, roster reopen and inventory reversal are not administrative curiosities.
4. **Archive beats delete.** Locations, courses and users stop participating in future selection while historical sessions and actor references survive.
5. **External systems diverge.** Processor, accounting, eCard vendor and local projections need explicit linkage and reconciliation.
6. **Capacity is a resource problem.** Seats, equipment ratios, linked offerings, waitlists, late reschedules and appointment conflicts interact.
7. **Permissions follow actions.** Instructor, Customer Service, Admin and Owner often view the same record but require different mutations and evidence depth.
8. **Communications need history.** A business event and an email/SMS delivery attempt are not the same state.

## Persona-based shared workspace

| Persona | Same Session/Participant truth | Surfaced capabilities |
|---|---|---|
| Instructor | Roster, session, requirements, lifecycle | Check-in, attendance, scores/remediation, completion readiness, issue-request/export, documents |
| Customer Service | Person, registration, order, session, products | Register/add, attach paid participant, move/reschedule, contact, payment association, fulfillment follow-up |
| Admin | All above plus policies and reconciliation | Corrections, reopen roster, resolve identity/reference, product/inventory issue/reverse, external reconciliation |
| Owner / Forensic | Same records plus immutable evidence | Provenance, import batches, supersession, actor history, financial/inventory reconciliation |

Enrollware supports this conclusion: class and registration pages expose overlapping records, while roles primarily change scope and actions. Its separate menu organization is navigation, not evidence for separate authoritative models.

## Top 20 replacement-critical ideas

1. Durable Person ↔ Registration ↔ Session authority.
2. Idempotent identity resolution with aliases and review.
3. Reschedule supersession preserving source and destination.
4. Transactional capacity and expiring seat holds.
5. Payment-to-registration reconciliation.
6. Refund, void, partial-refund and chargeback lifecycle.
7. Separate attendance, completion, credential issuance and notification.
8. Roster finalization, lock and controlled reopen.
9. Requirement/evidence gates at registration, attendance and completion.
10. Entitlement inventory issue/reversal/transfer ledger.
11. Credential product/SKU/version lifecycle.
12. Participant history that survives rescheduling and powers renewal.
13. Shared persona-scoped Session and Participant workspaces.
14. Unscheduled paid/known participant holding queue.
15. Waitlist and deterministic promotion.
16. Instructor qualification and expiration enforcement.
17. Communication templates plus delivery-attempt history.
18. Physical/digital fulfillment lifecycle.
19. Multi-meeting sessions and shared-capacity resources.
20. Append-only audit and external-system reconciliation queues.

## LanderWare status summary

| Classification | Count | Interpretation |
|---|---:|---|
| Already supported | 11 | Canonical durable machinery exists; some still need UI/projection work |
| Already supported better | 5 | Identity/provenance, Hx evidence, inventory events, location archival and historical unknowns |
| Partial | 15 | Schema/service or one persona path exists, but operational lifecycle is incomplete |
| Missing | 9 | No convincing canonical implementation found |
| Meaningful replacement gaps | 24 | Partial + missing capabilities that matter before Enrollware exit |
| Likely missing data-model concepts | 10 | Payment events, roster lock, SKU versions, waitlist/seat holds, shared capacity, qualification, delivery history, fulfillment, meetings, payer roles |

The count is a research classification, not a release gate. The detailed rationale is in `enrollware_landerware_gap_matrix.md`.

## Direct option vs automation

- **Automate/derive:** location picker eligibility, appointment conflict detection, close-registration instant, qualification checks, readiness gates, reminder triggers, historical visibility and capacity calculations.
- **Role-specific direct actions:** add/register participant, move, associate payment, issue/reverse inventory, finalize/reopen roster, record attendance/completion and reconcile credential.
- **Advanced escape hatches:** manual external association, correction with reason, staged imports, accounting ignore/retry and historical ambiguity review.
- **Potentially unsupported:** instructor bidding and several legacy presentation knobs unless owner evidence shows real use.

## Highest-risk replacement gaps

The top P0/P1 gap is not public page presentation. It is a coherent operational Session workspace capable of intake and recovery: add an existing/new person, preserve idempotency, attach a payment/order, attach/waive material requirements, move without losing lineage, distinguish attendance/completion/credential, finalize the roster, and expose the same durable history later. Payments/refunds, capacity/seat holds, fulfillment, communications and instructor qualification are the next critical layers.

## Evidence artifacts

- `data/audit/enrollware_menu_tree.md`
- `data/audit/enrollware_help_feature_inventory.md`
- `data/audit/enrollware_feature_announcement_history.md`
- `data/audit/enrollware_landerware_gap_matrix.md`
- `data/audit/enrollware_weird_options_owner_review.md`
- `data/audit/enrollware_crawl_progress.md`
- `data/audit/enrollware_crawl_gaps.md`
- `data/audit/evidence/enrollware_help_ip_chargeback.png`
- `data/audit/evidence/enrollware_help_reschedule_lineage.png`

## Safety/status

Persisted locally in the repository as audit-only artifacts. Research was remote/read-only. No Enrollware mutations, LanderWare changes, migrations, imports, or deployments were performed.
