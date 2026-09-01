# Enrollware → LanderWare operational gap matrix

Assessment date: 2026-09-01. `Supported` means durable schema/service evidence exists; it does not imply every persona has a finished UI. Old `landerware_*` experiments are not counted as canonical authority where the production-compatible `class_sessions` / `registrations` / `people` model supersedes them.

| Concept | Operational problem | Evidence | Current LanderWare support | Proposed treatment | Persona(s) | Priority |
|---|---|---|---|---|---|---|
| Durable person ↔ session registration | Keep one authoritative participant lifecycle | Registration edit, roster, history | Supported: canonical people/customers, registrations and class_sessions; public intake | Shared Register/Add Participant capability with contextual entry points | Instructor, CS, Admin | P0 |
| Idempotent identity and aliases | Repeated intake/import must not duplicate people | Search/import/troubleshooting | Supported better: identity/provenance and Hx fingerprints | Keep fail-closed resolution and review queue | Admin, Owner | P0 · LANDERWARE ALREADY BETTER |
| Reschedule lineage | Preserve original and destination without fake attendance | Reschedule UI/log/help | Supported in schema/RPC via registration supersessions; UI partial | One Move action with policy/permission layers | CS, Admin | P0 |
| Payment-registration association | Processor payment may exist without registration | Outage guidance, payment report | Partial: orders/items/payment state exist | Reconciliation queue and explicit associate action | CS, Finance | P0 |
| Payment lifecycle | Void/refund/partial refund/chargeback differ | Help, reports, virtual terminal | Partial | Append-only payment events and role-gated workflows | CS, Finance, Owner | P0 · MISSING DATA-MODEL CONCEPT |
| Completion vs attendance vs credential | Registration is not completion; issuance is separate | Finalize, cards, Atlas help | Supported canonical tables; operational workflow partial | Session workspace stages and exception queue | Instructor, Admin | P0 |
| Roster finalization/locking | Prevent post-close silent edits | Finalize Roster, unlock help | Missing/partial | Explicit roster close, controlled reopen, audit reason | Instructor, Admin | P0 · MISSING DATA-MODEL CONCEPT |
| Requirement/evidence gates | Documents/skills prerequisites block stages | Custom upload, remediation | Supported requirements/evidence schema | Derived readiness gates in same workspace | Participant, Instructor, Admin | P0 |
| Inventory entitlement/events | Track owned prepaid pools and reversals | Keycode banks, recycle | Supported better in Hx foundation | Generalize operational issue/reverse/transfer UI | Admin, Owner | P0 · LANDERWARE ALREADY BETTER |
| Product/credential SKU versioning | Guideline versions overlap and retire | 2025 cards, ARC transition | Partial catalog/aliases | Effective dates, credential family/version, inactive products | Admin | P0 · MISSING DATA-MODEL CONCEPT |
| Waitlist and promotion | Full-class demand needs an ordered queue | Help/history | Missing | Registration intent state, seat hold and deterministic promotion | CS, Participant | P1 · MISSING DATA-MODEL CONCEPT |
| Unscheduled participant holding | Paid/known person may lack a session | Unscheduled Students | Partial lifecycle supports nullable intent concept, shared UI absent | First-class holding queue attachable later | CS, Admin | P1 |
| Capacity/seat holds | Avoid oversell during checkout and moves | Max students, linked seats | Partial | Transactional seat reservation with expiry | Participant, CS | P0 · MISSING DATA-MODEL CONCEPT |
| Linked sessions sharing capacity | Related offerings consume one seat pool | Help | Missing | Shared capacity resource, not copied max values | Admin | P2 · MISSING DATA-MODEL CONCEPT |
| Appointment availability engine | Slots respect instructor/location/class conflicts | Appointment edit | Scheduling pipeline exists; operational replacement incomplete | Derive from resources and commitments | Admin, Participant | P1 · AUTOMATE INSTEAD OF CONFIGURE |
| Instructor qualification/expiry | Do not assign unqualified/expired staff | Expiring certifications | Partial people catalog; workflow missing | Credential-based eligibility and warning/block policy | Admin | P1 · MISSING DATA-MODEL CONCEPT |
| Instructor bidding/acceptance | Staff availability is not assignment | Bidding screens | Missing | Optional offer/accept/decline workflow | Instructor, Admin | P3 |
| Communications delivery history | Know what was sent, delivered, failed, resent | Email/text logs | Partial | Message attempts separate from template/business event | CS, Owner | P1 · MISSING DATA-MODEL CONCEPT |
| Campaigns/reminders | Scheduled follow-up reduces manual work | Campaign/SMS screens | Missing/unknown | Event-driven automatic notifications with escape hatch | CS, Admin | P2 · AUTOMATE INSTEAD OF CONFIGURE |
| Credential vendor reconciliation | Vendor may issue but local app lacks code | Atlas duplicate/checkmark help | Evidence model better; UI missing | Review queue with manual canonical association | Admin, Owner | P1 · LANDERWARE ALREADY BETTER |
| Shipping fulfillment | Product purchase needs deliver/pickup/ship state | Shipping queue | Orders/items exist; fulfillment workflow missing | Fulfillment entity/events and exception queue | CS | P1 · MISSING DATA-MODEL CONCEPT |
| Digital key delivery | Code assignment/recycle must preserve inventory truth | Keycode manager/sales | Foundation supports events; delivery UI missing | Inventory issue/reverse plus delivery attempt | CS, Admin | P1 |
| Product/manual ownership | Existing manual avoids duplicate purchase | Registration product options | Partial registration items/requirements | Record owned/evidenced/waived vs newly fulfilled | Participant, CS | P1 |
| Promo eligibility/lifecycle | Discounts vary by client/course/date/domain/count | Promo screens/help | Missing/unknown | Rule object evaluated automatically; audited override | CS, Admin | P2 |
| Client/corporate context | Shared contacts, notes, docs, defaults and reporting | Client pages/activity | Partial organization portals and authority | Canonical organization relationship in shared workspaces | Corporate, CS, Admin | P1 |
| Participant history across renewals | Returning learner needs prior truth | Earlier Classes | Supported by canonical person identity and lifecycle | History panel in Participant/Session workspace | CS, Instructor | P0 |
| Class reports/exports | Operations and vendors need projections | Report/export menus | Partial projections/scripts | Saved read models; avoid export as authority | Admin, Owner | P1 |
| Settings/event audit | Configuration changes affect operations | Event Log, settings history | Provenance/evidence stronger in parts; broad audit partial | Append-only audit for privileged changes | Owner | P1 |
| Role-scoped shared workspaces | Same entity, different actions/evidence | User roles and class/registration pages | Partial admin/corporate surfaces | One Session/Participant model with permission-based panels | All | P0 |
| Read-only/inactive users | Preserve history without ongoing access | User edit/help | Partial | RBAC status and immutable actor references | Admin, Owner | P1 |
| Location archival | Stop future selection without hiding history | Archived Location | Supported better: scheduling_status/historical_only | Derive picker eligibility from status; never hide sessions | Admin | P0 · LANDERWARE ALREADY BETTER |
| Historical unknown fields | Do not fabricate instructor/end time | Legacy/history evidence | Supported better: closed historical record_scope | Keep unknown explicit and reviewable | Admin, Owner | P0 · LANDERWARE ALREADY BETTER |
| Bulk import with dry run | Operational imports need preview and idempotency | Student/class/location imports | Hx framework supports history; current bulk UI limited | Reusable staged import/reconcile/approve framework | Admin | P1 |
| Deletion/archive policy | Referenced records should not be erased | Delete help, archive options | Mixed | Prefer status/archive; hard delete only unreferenced drafts | Admin | P1 |
| Multi-day/session meeting model | One class can have several meetings | Class edit/help | Partial start/end only | Meeting occurrences under a session | Instructor, Admin | P1 · MISSING DATA-MODEL CONCEPT |
| Check-in, scores, remediation | Attendance and skill outcomes need structured facts | Registration/class controls | Completion schema partial; UI absent | Lifecycle assertions with controlled instructor actions | Instructor | P1 |
| Receipt/payer separation | Participant and payer/recipient differ | Receipt security announcement | Order/customer model partial | Explicit payer, purchaser, participant, receipt recipient | CS, Finance | P1 · MISSING DATA-MODEL CONCEPT |
| QuickBooks reconciliation | Sync can fail, be ignored or retried | QuickBooks Sync/help | Unknown/partial | External accounting link plus retry/ignore history | Finance | P2 |
| Security controls | MFA, AVS, CAPTCHA and IP evidence address different risks | Settings/help | Platform-dependent/partial | Central security policy; minimize exposed browser authority | Owner | P0 |
| Public registration privacy | Custom uploads and analytics can expose PII | Site Settings | Partial safeguards | Data-minimize, purpose-limit, signed upload and audit | Owner | P0 |

## Shared-workspace conclusion

Enrollware’s separate menus repeatedly converge on the same registration, session, person, payment, product and evidence records. LanderWare should use shared canonical entities and persona-specific surfacing—not four independent registration implementations. Instructor gets roster/attendance/completion actions; Customer Service gets intake/contact/move/payment association; Admin gets corrections/readiness/inventory; Owner gets provenance/supersession/reconciliation. Authorization must apply to actions and fields, not fork the underlying truth.

