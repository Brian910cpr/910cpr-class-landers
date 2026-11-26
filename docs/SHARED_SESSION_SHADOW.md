# Issue 359: shared-session shadow contract

This is a partial Phase A backend test bed under #342. No production import,
selector, workflow, database, registration or payment path calls it.

## Objects and incumbent lesson

Existing `scripts/layered_scheduling_engine.py` preserves source commitments and
computes remaining seats from a source's capacity/headcount. That incumbent
pattern correctly makes capacity belong to the class occurrence; exact course
identity is needed for enrollment/fulfillment, not an independent seat bucket.
Its current source-course identity does not establish that different products
belong to ONE operational session. Do not merge sessions by matching clock time.
The 910CPR improvement is an explicit reusable session family with exact product
items retained. This supports native LanderWare identity rather than new
Enrollware ID dependencies. This round does not remove an Enrollware dependency.

`Session.session_id` owns identity; `capacity` is its explicit seat limit;
`items` contains exact product/count pairs representing active seats and holds;
`revision` describes the current snapshot. ARC_GENERAL_SKILLS and ARC_BLS default
to four individually. No global capacity or existing course data is modified.
Existing sessions retain explicitly supplied capacities. Capacity provenance and
historical session migration require review before a real adapter is connected.

`options` accepts only already-qualified scoped sessions and starts accepted by
the existing legality engine. It prefers compatible planted seats and otherwise
returns legal starts with the configured new-session capacity. A full session
creates no date-wide suppression. Closed/full sessions must remain occupancy
inputs to the legality engine; this helper does not remove resource blocks.
Unknown counts/mappings fail closed. Callers must include live holds exactly once
in occupancy and establish snapshot completeness; missing rows cannot mean zero.

## Booking gate and remaining acceptance work

`revalidate` is a pure precondition, NOT an atomic reservation. Its test models a
revision change after the fourth seat; it does not prove concurrent database
bookings safe. A transactional backend must lock the canonical session, reread
seats and unexpired holds, re-evaluate current resource/qualification/time rules,
check revision/capacity, persist the requested product item and advance revision
before committing. Idempotent retries, hold expiry, failed payments, cancellation
and reschedule histories must preserve counts and provenance.

Before integration: establish authoritative product-to-family mappings (do not
infer $11/$16 products from prices or guess external IDs), canonical session IDs,
complete active seat/hold projections, lifecycle rules and session-capacity
provenance. Then compose this helper with #342 real-input/shadow regression
fixtures including legal later same-day starts; run actual concurrent transaction
proof of the last-seat race. This round's legal-start list is synthetic and does
not prove the real day or customer selector. Issue acceptance #9 and production
acceptance remain outstanding. No production mutation is authorized by this code.

## Proof contract

Evidence level: BUILT, locally tested only. Expected eventual outcome: mixed
compatible products fill one session without overselling and later legal sessions
remain bookable. Success evidence must be durable transaction records plus the
customer selection/registration outcome. Cadence is every booking; no real
end-to-end proof or production observer exists for this helper. An eventual
observer must detect oversold sessions, stale/unknown seat snapshots and missing
booking proof, and have its own heartbeat. Recovery is fail-closed affected
session booking and reconcile authoritative holds/registrations. Escalate missing
business mappings/identity decisions to owner review; do not require Brian to
routinely monitor bookings. No monitoring health is claimed here.
