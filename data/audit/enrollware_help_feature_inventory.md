# Enrollware help feature inventory

Reviewed through the visible Help Center UI on 2026-09-01.

## Coverage

| Category | Articles inventoried |
|---|---:|
| Affiliate Site setup | 1 |
| Billing | 5 |
| Contact Enrollware | 1 |
| EnrollwarePay | 14 |
| Getting Started | 46 |
| Advanced Topics | 108 |
| How-to Videos | 15 |
| AHA Training Centers | 10 |
| **Total** | **200** |

Sixty-eight high-value articles were opened and reviewed in full. Selection emphasized lifecycle, exceptions, troubleshooting, permissions, payments, fulfillment and integrations rather than introductory marketing.

## Operational clusters found

- Registration intake: bulk/private registration, custom questions, participant file upload, multiple-class registration, labels, portal, holding area and copy-to-class.
- Rescheduling: cross-course moves, self-reschedule insurance and fees, blackout windows, calendar/location filtering, prior-class history and a dedicated audit report.
- Session operations: multi-day/multi-session classes, linked classes sharing seats, appointments, class repetition, waitlist/automatic promotion and “will call to schedule.”
- Completion and credentials: roster finalization/locking, remediation, scores, certificate email, AHA/HSI/ARC integrations, duplicate-assignment recovery and manual credential reconciliation.
- Products and inventory: books, shipping queues, keycode banks, multiple banks per course, add-ons, recycling/unassignment, training-center product sales and asset tracking.
- Payments: payment requests, pay-at-door/check, virtual terminal, recharge, partial/full refund, void, funding reconciliation, QuickBooks sync, ignored transaction recovery and chargeback evidence.
- Communications: registration/class templates, course-specific CCs and sidebars, campaigns, scheduled SMS, resend, per-participant delivery logs and service-outage fallback.
- People and permissions: active/inactive/read-only users, instructor-only scope, multiple sites, training-center/site roles, bidding, certification expiration and class-change notifications.
- Locations and organizations: advanced location records, archived locations, client tracking/activity, shared/internal notes, documents and direct links.
- Forensics: event log, registration status webhook, email/text logs, IP capture, reschedule log, payment notes/adjustments, roster locks and settings audit trail.

## Troubleshooting-derived requirements

- Credential APIs may accept a request but fail to send mail, reject duplicates, or become unavailable. Issuance state, vendor state and notification state must be separate.
- A card may exist in Atlas while Enrollware lacks the credential code/checkmark. Manual association and provenance-preserving reconciliation are necessary.
- Payments can succeed without a matching registration during outages. Payment identity and participant/session identity require a reviewable association workflow.
- Keycodes can be assigned incorrectly and later recycled. Inventory needs immutable issue/reversal events, not a mutable remaining-count field alone.
- Refunds can be partial and may occur in the processor rather than the registration screen. Refund, registration and accounting states cannot be one status.
- Shipping must exclude canceled registrations while retaining historical fulfillment evidence.
- Finalized rosters may require controlled unlock authority; current truth and audit history must both survive correction.
- Class moves can cross course types. Reschedule lineage cannot be represented solely by changing a session foreign key without history.
- Location/course/user deletion is constrained by references; archive/inactive states are the normal operational answer.
- Multi-session classes remain operationally upcoming until their last meeting is complete.

## Current-status caution

Help evidence was cross-checked against the present Admin UI when possible. Articles can describe optional edition-specific integrations or older terminology. Those are marked as operational evidence, not proof that every feature is enabled for 910CPR today.

Raw, non-committed research inventories are retained locally at `work/enrollware_help_article_inventory.json` and `work/enrollware_help_articles_reviewed.json`.
