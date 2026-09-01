# Enrollware feature announcement history

Read-only evidence captured 2026-09-01 from the authenticated Notifications page and the Help Center **What's New** history.

## Coverage

- 30 tenant-visible notifications reviewed, dated 2024-12-19 through 2026-08-31.
- 345 dated What's New entries inventoried, extending back before 2018.
- 375 entries reviewed or inventoried in total. The raw captured text remains local and uncommitted because it is research evidence, not application data.

## Product-history themes

| Period/evidence | Change | Operational problem surfaced | Persona/workflow | Current-UI evidence |
|---|---|---|---|---|
| 2026-08 | Multiple online-keycode banks per course | A single inventory pool cannot express multiple SKUs, vintages, or owners | Admin; product inventory | Present in Course Edit and Online Keycodes |
| 2026-08 | ARC r21 to r25 transition guidance | Credential products and course versions have overlapping retirement windows | Admin; catalog/compliance | Course archive and keycode-bank controls present |
| 2026-07 | Receipt-link security change and separate receipt delivery | A reusable receipt URL can leak payment data; payer and participant may differ | Customer service; payment | Payment/report surfaces present |
| 2026-03 | Mass deletion with zero-student class guard | Cleanup is useful but must not erase participant history | Admin; class maintenance | Bulk controls present; mutation not entered |
| 2026 | HSI blended certificates and expanded certification APIs | Completion, issuance, vendor acceptance and notification are distinct states | Instructor/Admin; credentials | Credential settings/exports present |
| 2025-09 | Reschedule calendar/location UI optimization | Large schedules make naïve destination lists slow and error-prone | Customer service; reschedule | `Reschedule to` and self-reschedule log present |
| 2025 | 2025 AHA guideline/card versions | Course/card versions change while prior credentials remain historically valid | Admin; catalog/credential inventory | Course/card/keycode configuration present |
| 2025 | Outage reconciliation guidance | Processor payment can exist without registration; card can exist in Atlas without local code | Admin/Owner; reconciliation | Manual registration/card association paths documented |
| Multi-year | Waitlist and automatic promotion | Full classes require queued demand and deterministic seat release | Customer service; registration | Documented; not observed as enabled tenant UI |
| Multi-year | Self-reschedule, fees, insurance and blackout window | Moving a participant has policy, money, capacity and audit consequences | Customer service/participant | Course settings and audit report present |
| Multi-year | Cross-course rescheduling | A legitimate move may change course identity, not just session ID | Admin; lifecycle | Registration edit supports destination selection |
| Multi-year | Finalize/lock/unlock roster | Completion evidence needs a controlled close and exceptional correction path | Instructor/Admin | Finalize Roster present |
| Multi-year | Email/SMS logs and resend | Delivery attempts and business state cannot be conflated | Customer service; communications | Per-registration logs present |
| Multi-year | Partial refunds, voids, chargebacks and adjustment notes | Payment lifecycle is not a Boolean paid flag | Finance/Admin | Reports/help evidence present |
| Multi-year | Product shipping and canceled-registration exclusion | Purchase, fulfillment and attendance have different lifecycles | Customer service; fulfillment | Shipping queue present |
| Multi-year | Keycode assignment, unassignment and recycling | Digital inventory requires immutable consumption/reversal history | Admin; inventory | Bank/sales screens present |
| Multi-year | Instructor bidding and change notifications | Staffing has offers, acceptance and downstream notification states | Instructor/Admin | Bidding menus and user preferences present |
| Multi-year | Appointment availability and existing-class conflict checks | Flexible slots must respect resources already committed elsewhere | Scheduler/Admin | Appointment edit controls present |
| Multi-year | Settings audit trail, MFA, strict AVS and IP evidence | Configuration and payment disputes require forensic evidence | Owner/Security | Site settings and event log present |
| Multi-year | QuickBooks ignored/full-history recovery | Accounting sync needs retry, ignore and reconciliation states | Finance/Admin | QuickBooks Sync controls present |

## Interpretation

The history is consistent with a mature operational product: most additions are exception-handling, recovery, auditability, permissions, and cross-system reconciliation—not novel page types. Current UI observation was used where possible. Older or edition-specific announcements are evidence that the problem exists, not proof that every feature is enabled for 910CPR.

Safe screenshots:

- `data/audit/evidence/enrollware_help_ip_chargeback.png`
- `data/audit/evidence/enrollware_help_reschedule_lineage.png`
