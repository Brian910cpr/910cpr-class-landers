# 910CPR / Lander Scheduler Scope Lock

Generated: 2026-06-18

This checkpoint freezes the scheduler redesign around four critical objects only:

1. People
2. Courses
3. Availability
4. Occupancy

Everything else is real and valuable, but it is future-adjacent for this phase. The first solver should stay narrow enough to prove it can make honest schedule decisions before downstream systems consume those decisions.

## Current Project Purpose

The scheduler's first proof is:

> Given an open availability window, the system can identify which classes can honestly be offered.

This means the first useful solver does not need to understand products, payments, inventory, reminders, add-ons, or payroll. It needs to understand who can teach, what can be taught, when space/instructors are available, and what is already occupying that time.

## In-Scope Objects

### People

In scope:

- instructors
- students/customers only as future registration/occupancy context
- instructor qualifications
- instructor availability ownership

The scheduler needs people data only when it affects whether a class can honestly be offered. For this phase, the critical people question is: which qualified instructor owns or can consume an availability window?

### Courses

In scope:

- course ID
- title
- provider
- family
- duration
- capacity
- instructor requirement
- appointment eligibility

The scheduler needs course data only when it affects whether a class fits a time window, can be taught by the available instructor, and can be safely offered to customers.

### Availability

In scope:

- explicit open windows
- DNS / Do Not Schedule blocks
- ADR/employment blocks
- personal blocks
- room/location availability if locally represented

The scheduler should treat availability as the supply side of the problem. It should not invent availability from absence of data unless the policy explicitly says that is allowed.

### Occupancy

In scope:

- existing scheduled Enrollware classes
- booked/generated appointments once confirmed
- occupied instructor/location time
- conflicting class windows

The scheduler should treat occupancy as committed or reserved time that reduces what can honestly be offered.

## Out Of Scope For This Scheduler Phase

The following are future systems, not current scheduler inputs:

- Enrollware product add-ons
- keycode banks
- manuals/eBooks
- eCards
- HeartCode inventory
- Stripe payments
- inventory replenishment
- student reminders
- renewal reminders
- review requests
- emails/SMS
- invoice/payroll logic

## Why These Items Are Deferred

These systems matter, but they should consume scheduler output later instead of complicating the first solver.

Example:

- Scheduler says: "6 BLS students are booked next Tuesday."
- Inventory system later asks: "What does 6 BLS students consume?"

That separation keeps the scheduler responsible for sellable time and class feasibility. Product catalogs, keycodes, eCards, consumables, reminders, payment flows, and payroll can attach after a class exists or after a booking is confirmed.

If the first solver tries to model every downstream operational detail, it becomes harder to audit the basic question: can this class honestly be offered at this time?

## Current Built Artifacts

Planning and scope:

- `docs/910cpr_lander_scheduler_punchlist.md`

Read-only solver audit:

- `scripts/solver_audit.py`
- `tests/test_solver_audit.py`
- `data/audit/solver_audit_summary.json`
- `data/audit/solver_audit_candidates.json`
- `data/audit/solver_audit_rejections.json`
- `data/audit/solver_audit_report.md`

Canonical course model:

- `data/config/course_catalog.json`
- `data/audit/course_catalog_validation.md`

Course rules review draft:

- `data/audit/course_catalog_rules_patch_draft.json`
- `data/audit/course_catalog_rules_patch_review.md`

## Recommended Next Action

Complete the scheduler-critical course review only:

- duration
- capacity
- appointment_allowed
- required_instructor_certifications

Do not expand product/resource modeling yet.

The next useful checkpoint is a clean, reviewed course catalog where every scheduler-critical course has explicit duration, capacity, appointment eligibility, and instructor requirement values. Once that is complete, the solver can use better course facts without adding scheduling complexity.

## Future-System Parking Lot

### Product Catalog

Future concern for Enrollware product add-ons, manuals, eBooks, eCards, keycodes, HeartCode inventory, and course material bundles. This should consume confirmed class/course output after scheduling.

### Inventory / Replenishment

Future concern for manikins, AED trainers, lungs, masks, books, cards, keycodes, and other consumables. This should answer what a confirmed class consumes, not whether the class can initially be offered.

### Payments / Stripe

Future concern for checkout, deposits, invoices, balance payments, refunds, and payment reconciliation. This should attach after a class or registration path exists.

### Notification Engine

Future concern for student reminders, instructor reminders, SMS/email workflows, review requests, and operational follow-up messages.

### Renewal Engine

Future concern for certification expiration tracking and renewal reminders. This is customer lifecycle logic, not first-pass scheduling logic.

### Instructor Payroll / Invoicing

Future concern for instructor pay, contractor invoices, revenue splits, and internal cost accounting.

### Customer History / People CRM

Future concern for customer profiles, organization history, prior certifications, renewal timing, repeat bookings, and account-level relationship management.

## Codex Safety Checklist

Before future scheduler work, Codex should verify:

- no public pages changed
- no Enrollware behavior changed
- no generated HTML changed
- no Worker creation enabled
- no appointment URLs changed
- all new outputs are `docs/`, `data/audit/`, or explicit config only

If a requested change crosses those boundaries, stop and call it out before implementation.
