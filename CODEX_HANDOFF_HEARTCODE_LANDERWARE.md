# Codex Handoff — LanderWare HeartCode BLS Checkout

## Objective

Move BLS HeartCode customer checkout toward LanderWare while preserving Enrollware course/session identity where it is still needed.

This is a vertical slice intended to become the reusable model for ACLS, PALS, ARC blended, HSI online, and other eProduct-backed classes.

## Non-negotiable domain rules

1. **Enrollware course ID 210549 remains the BLS HeartCode scheduling identity.**
   - Do not rename, repurpose, or replace it with a synthetic course ID.
   - Enrollware uses 210549 to schedule its appointment/event path.

2. **Do not create a fake LanderWare-only course number for BLS skills-only.**
   - The same physical skills session may contain both Enrollware-origin and LanderWare-origin registrations.

3. **Two customer purchase configurations share the same physical session/time/capacity pool.**
   - HeartCode BLS Provider: skills session $55 + AHA HeartCode BLS eProduct $41 = **$96 total**.
   - Skills Session Only: **$55 total**.
   - They are not competing sessions and may occupy the exact same start time.

4. **Session occupancy and seat occupancy are different concepts.**
   - One physical session blocks instructor/location time once.
   - Enrollware registrations + LanderWare paid registrations + active LanderWare holds consume seats in the same capacity pool.

5. **LanderWare-owned registrations must not be pushed into Enrollware just to preserve course identity.**
   - LanderWare owns student/order/payment/seat/fulfillment records for the LanderWare checkout path.
   - Enrollware does not need to know that a LanderWare-only registration exists.

6. **eProduct fulfillment is manual-approval-first.**
   - No automatic AHA eProduct release in this phase.
   - After payment for the $41 HeartCode item, create a high-priority owner fulfillment task/notification.
   - Prepare the student delivery email but do not send it automatically.
   - If no code exists, leave a clear placeholder for the owner to paste a purchased AHA code/link, then approve/send.

## Current repository seams

### Selector configuration
- `data/config/block_schedule_pages.json`
- BLS page currently defines:
  - 209806 — BLS Provider Initial
  - 359474 — BLS Provider Renewal
  - 210549 — AHA HeartCode BLS, currently presented as skills-only at $55

### Selector rendering
- `scripts/build_bls_block_schedule_pilot.py`
- Generates `docs/bls.html`
- Current model assumes one customer-visible course option per scheduling course ID.

### Scheduling / appointment URL generation
- `scripts/block_start_time_selector.py`
- Uses Enrollware course IDs and appointment containers.
- Existing `210549` appointment URLs must remain valid for the Enrollware-backed path.

### Native LanderWare checkout
- `docs/register/index.html`
- `supabase/functions/public-registration/index.ts`
- `landerware_registration_catalog`
- Existing native public-order flow already supports:
  - seat holds
  - Stripe checkout
  - per-student items/add-ons
  - paid confirmation
  - LanderWare registrations

### Existing BLS catalog data
- `supabase/migrations/20260909220000_native_public_checkout.sql`
- `210549` currently exists in catalog at $55.
- Do not treat that historical catalog row as proof that $55 and $96 are separate scheduling courses. They are purchase configurations on one session identity.

## Target public UX

Section title:

**HeartCode BLS Provider**

Choice 1 — default/recommended:

**HeartCode BLS Provider — $96**
- Online portion + in-person skills
- Includes AHA HeartCode BLS eProduct

Choice 2:

**In-person BLS Provider Skills Session Only — $55**
- For students who already purchased/completed the AHA HeartCode BLS online portion

Both choices must surface the same legal dates/start times for course/session identity `210549`.

## Preferred checkout model

Use one LanderWare checkout surface with product composition instead of two unrelated checkout systems.

Base line item:
- key: `bls_skills_session`
- display: `BLS Provider Skills Session`
- amount: 5500

Optional/default eProduct line item:
- key: `aha_heartcode_bls`
- display: `AHA HeartCode BLS Online`
- amount: 4100
- product_type: eproduct
- fulfillment_mode: manual_approval
- requires_manual_approval: true

Default selected total: 9600.
Skills-only total: 5500.

Customer-facing language should say **Online course**, not “add-on”.

## Order / product separation

Do not overload course IDs with product identity.

Model three separate concepts:

1. **Session/course identity**
   - What physical training is happening, when, where.
   - For this slice: Enrollware scheduling course ID `210549`.

2. **Order items**
   - What the customer paid for.
   - Skills session and optional HeartCode eProduct.

3. **Fulfillment**
   - What 910CPR still has to deliver after payment.
   - HeartCode access/code/link requires owner action.

## Capacity and coexistence

A valid example:

```
Physical session: 210549
Start: 2026-10-13 10:00 America/New_York
Capacity: 6

Enrollware registrations: 2
LanderWare paid registrations: 2
LanderWare active holds: 1

Seats consumed/held: 5
Seats remaining: 1
Instructor/location block count: 1
```

Do not block the $55 and $96 variants against each other as separate sessions.

When the first LanderWare registration selects an available dynamic 210549 start, materialize or attach to a canonical LanderWare representation of that physical session. Subsequent LanderWare registrations at the same start/location/session family must join that same physical session rather than create duplicates.

## Dynamic-slot behavior

For a LanderWare checkout selected from a 210549 candidate time:

1. Revalidate the selected start against current authoritative availability.
2. Resolve an existing equivalent physical session if one exists.
3. Otherwise materialize a LanderWare session representation for that 210549 start.
4. Create a seat hold.
5. Create LanderWare order and order items.
6. Redirect to Stripe.
7. On payment, activate the registration.
8. Refresh availability immediately.
9. Capacity must reconcile Enrollware seats + LanderWare seats + active holds.

Do not create a second instructor/location blocker for the same physical session.

## Stripe

Where supported, send separate Stripe line items:
- BLS Provider Skills Session — $55
- AHA HeartCode BLS Online — $41

Stripe confirms money. LanderWare remains the authority for:
- session
- registration
- order
- order items
- fulfillment state
- audit trail

## Manual eProduct fulfillment

After a paid order contains `aha_heartcode_bls`:

Create a high-priority fulfillment record/task with:
- student name
- student email
- provider: AHA
- product: HeartCode BLS
- quantity
- amount collected: $41
- skills session date/time/location
- order ID
- eProduct code/link field
- status: `needs_action`

Recommended state machine:
- `not_required`
- `needs_action`
- `inventory_reserved`
- `code_assigned`
- `draft_ready`
- `approved`
- `sent`
- `failed`
- `cancelled`
- `refunded`

For this phase, typical path:
`paid -> needs_action -> code_assigned -> draft_ready -> approved -> sent`

## Owner priority notification

Prepare/send an owner alert such as:

**Subject:** ACTION REQUIRED — Issue HeartCode BLS for {{student_name}}

Include:
- student
- email
- AHA HeartCode BLS
- quantity
- $41 collected
- selected skills session
- order ID
- `EProduct code: [ NOT ASSIGNED ]`
- instruction to acquire/assign product and approve the prepared student draft

Use the project's current owner/fulfillment notification mechanism. Do not silently auto-issue.

## Prepared student draft

Create but do not send:

**Subject:** Your AHA HeartCode BLS online course

Body should include:
- student greeting
- product name
- clear placeholder: `[ EPRODUCT CODE / LINK GOES HERE ]`
- selected skills date/time/location
- instruction to complete HeartCode before skills
- 910CPR contact info

Owner should be able to paste the code/link and approve/send.

## Reusable product catalog direction

Prefer a provider-neutral product/fulfillment model suitable for later:
- AHA HeartCode ACLS
- AHA HeartCode PALS
- AHA Heartsaver online products
- ARC blended online products
- HSI online products

Candidate product fields:
- product_key
- provider
- display_name
- product_type
- sale_price
- cost
- fulfillment_mode
- requires_manual_approval
- active
- metadata

Candidate eProduct inventory fields:
- id
- provider
- product_key
- provider_product_id
- code
- status
- purchased_at
- cost
- assigned_order_id
- assigned_student_id
- assigned_at
- notes

Do not over-generalize before the BLS vertical slice works.

## Acceptance criteria

1. BLS selector section reads **HeartCode BLS Provider**.
2. Public choices are **$96 complete HeartCode BLS Provider** and **$55 Skills Session Only**.
3. Both use the same legal 210549 skills times.
4. Complete package defaults to selected HeartCode eProduct.
5. Unselecting online course yields $55 total.
6. LanderWare can accept payment for both configurations.
7. A LanderWare $55 student and a $96 student may register into the exact same physical session.
8. Enrollware-origin and LanderWare-origin registrations may coexist in that same physical session.
9. Combined seat accounting is correct.
10. A physical session creates one instructor/location occupancy block regardless of registration source or purchase configuration.
11. Paid $41 HeartCode item creates high-priority manual fulfillment work.
12. Prepared student email is created but not automatically sent.
13. Missing inventory/code produces a visible placeholder, not a failed or silently completed fulfillment.
14. Availability is refreshed after hold/payment actions.
15. Existing BLS Initial and Renewal flows remain unchanged.
16. Existing 210549 Enrollware appointment URLs remain valid.
17. No synthetic scheduling course ID is introduced for skills-only.
18. Tests cover coexistence, capacity, duplicate-session prevention, payment totals, and fulfillment creation.

## Tests to add

At minimum:
- $96 checkout = 5500 + 4100
- $55 checkout = 5500
- same 210549 time accepts one $96 and one $55 LanderWare registration when capacity allows
- same physical session accepts Enrollware seat count plus LanderWare seats
- session occupancy is not duplicated by multiple registrations
- capacity rejects only when combined seats + active holds exceed max
- repeat checkout joins existing canonical physical session
- payment containing HeartCode creates `needs_action` fulfillment
- payment without HeartCode creates no eProduct fulfillment
- student draft remains unsent until explicit approval
- existing 209806 / 359474 behavior does not regress

## Implementation guardrails

- Do not hand-edit generated `docs/bls.html` as the source of truth.
- Change generator/config/source files and rebuild.
- Do not weaken fail-closed availability behavior.
- Do not make Enrollware aware of LanderWare-only registrations.
- Do not let Stripe become the authoritative product catalog.
- Do not auto-send AHA eProducts in this release.
- Preserve auditability: order -> student -> session -> items -> fulfillment must be traceable.

## Suggested implementation order

1. Add product/order-item/fulfillment model needed for this slice.
2. Extend native public checkout to support 210549 dynamic materialization/joining, not only BLS Initial.
3. Implement shared physical-session resolution and seat accounting.
4. Add HeartCode BLS $41 product with manual fulfillment.
5. Update checkout UI to default HeartCode selected and permit skills-only.
6. Update BLS selector presentation/config.
7. Add owner priority notification + prepared student draft.
8. Add tests.
9. Rebuild selector artifacts.
10. Verify live links and no regressions before merge.
