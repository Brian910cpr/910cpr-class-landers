# P0 Codex handoff — October 26 Voice rules for LanderWare

**Execute, don't merely plan.** Inspect existing implementation and Supabase schema first; reuse working infrastructure.

## Ownership
- Enrollware registration emails are intake evidence for student, course, session, payment and booking. Verify source details and reconcile into existing canonical LanderWare records.
- Once entered and reconciled, **LanderWare owns the operational registration**, including enrollment, schedule, roster, occupancy, changes and communications. Do not require recurring Enrollware roster confirmation to trust a LanderWare-enrolled student.
- Preserve original external IDs, provenance, payment, materials and audit history. Make ingestion idempotent. Do not let late Enrollware messages undo a later LanderWare change.
- Preserve UNKNOWN when current occupancy cannot be verified; missing roster does not mean zero students.

## Reschedule
- Enrollware-origin students use the **same LanderWare calendar and reschedule flow** as native LanderWare students.
- For a straight course-date change, retain existing registration, payment and materials; **no additional charge**.
- Show real eligible slots; update canonical session linkage, FROM/TO occupancy, change log and confirmation atomically. Track who used personalized reschedule links and FROM→TO movements.
- Renewals/new enrollments are **new paid transactions**, not free reschedules; use the Stripe payment process.

## Email lifecycle
- Day-before class reminders offer a personalized reschedule link.
- Approximately 23-month renewal outreach offers the calendar preselected to the student's last course type and the appropriate paid enrollment flow. Avoid already renewed students and duplicate messages.
- LanderWare manages subsequent confirmations, reminders and status; Enrollware is intake, not ongoing operational authority.

## Work
1. Inspect repo, Supabase canonical tables, ingestion/sync, sessions, reschedule handlers, payments, email jobs and tests.
2. Repair existing ingestion/reconciliation, including historical registrations, without parallel databases or invented records.
3. Implement explicit intake pending/confirmed/failed/conflicted states, deduplication, and safe transition to LanderWare ownership.
4. Test import, payment retention, native-equivalent reschedule, occupancy, late emails, cancellations, renewal paid checkout, reminders and tracking.
5. Report commits, tests, migrations, backfill results, blockers and deployment verification. Do not claim deployment without proof.

**Acceptance:** imported students appear in correct LanderWare rosters and capacity; can reschedule like native students without paying again; no later Enrollware intake overwrites LanderWare; reminders and paid renewals use their distinct flows.

This is a permanent implementation directive, not a request to manually copy text into Codex.
