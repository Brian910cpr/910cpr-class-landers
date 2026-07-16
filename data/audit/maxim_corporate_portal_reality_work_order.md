# MAXIM Corporate Portal — Reality Work Order

Status: Approved direction for implementation
Owner intent: Keep the customer-facing workflow extremely simple while putting strong recovery controls underneath it.

## Goal
Turn `/corp/maxim.html` from a visual prototype into a real, data-backed corporate training portal that lets MAXIM staff quickly:

1. See who is coming due for renewal.
2. Send a personalized self-service scheduling link.
3. Schedule for the employee when needed.
4. See registrations move through completion, eCard issuance, and invoicing.
5. Correct normal human mistakes quickly without exposing a complicated admin interface.

The portal should optimize for one thing: open the page, get the employee scheduled, and close the page as quickly as possible.

---

## Primary customer-facing workflow

The visible workflow should remain simple:

**Coming Due → Scheduling Link Sent → Registered → Completed / Awaiting eCard → eCard Issued / Awaiting Invoice → Invoiced**

Use tabs across the top of the workflow panel so each stage can use the full panel height and remain browsable as the number of employees grows.

Only one person detail drawer may be open at a time. Opening a second person closes the first.

Advanced correction controls should stay behind a small detail drawer or `•••` menu.

---

## Renewal logic

Historical customer/course records are valuable from day one.

A credential should surface for renewal based on its actual prior course date and the AHA-style two-year card cycle used for this portal.

For renewal display purposes:

- A class taken on `7/2/2024` is treated as expiring on `7/31/2026`.
- Expiration is the final day of the same month, two years after the class date.
- Always display the full expiration year, e.g. `Expires 7/31/2026`.

Old records should remain in history even after they are no longer operationally current.

A person is not globally “expired.” A specific credential is expired.

---

## MAXIM identification and billing normalization

Treat a historical registration as belonging to MAXIM when either of these rules is met:

1. Promo code contains `maxim` anywhere, case-insensitive, including status suffixes and historical variants.
2. The address matches the known MAXIM Wilmington address at 5535 Currituck Drive, using tolerant address normalization.

Normalize legacy MAXIM strings into structured fields while preserving the original value:

- `corporate_customer`: `MAXIM`
- `billing_account`: one of
  - `Maxim #031`
  - `MaximBH #0852`
  - `MaximDSP #502`
- `legacy_status`: parsed when present
- `legacy_promo_code`: original historical string

Do not treat the historical promo-code string as the permanent status model.

---

## Coming Due actions

Each coming-due person should have these primary actions:

- **Schedule for them**
- **Send scheduling link**
- **Skip**

Secondary/hidden actions may include:

- View history
- Reopen renewal
- Correct billing account

`Skip` should remove that credential cycle from the active renewal queue without deleting historical records. It should be reversible.

The system does not need to know why MAXIM skipped the person.

---

## Personalized `/go/` scheduling links

A personalized `/go/` token should represent scheduling intent, not a frozen appointment.

The token should store or resolve to:

- person identity
- corporate customer
- MAXIM billing account
- credential/course family to be renewed
- renewal cycle / source credential reference
- link state

The token must be opaque and must not expose personal information in the URL.

The `/go/` link should open a simplified scheduling experience with known data prefilled.

No payment, promo code, or unnecessary checkout flow should be shown.

The employee chooses only what is still needed, primarily date/time and confirmation of contact information.

When the employee self-schedules, the MAXIM dashboard should automatically move that credential from **Scheduling Link Sent** to **Registered** and display the chosen date/time.

---

## “Schedule for them” behavior

MAXIM staff should be able to click **Schedule for them** from either:

- Coming Due
- Scheduling Link Sent
- Registered, via **Move**

The scheduling experience should be the same underlying flow used by the personalized `/go/` link.

Known person and corporate data should be prefilled.

### Move behavior

Clicking **Move** on a current registration should:

1. Open the scheduler for that same person and credential.
2. Present current live availability.
3. Preserve the existing registration until the replacement is confirmed.
4. On confirmation, mark the old registration as superseded/moved in history.
5. Show only the new registration as active in the normal Registered view.

Do not delete the old registration.

---

## Live availability freshness contract

The current hard-coded MAXIM prototype availability must be replaced with real LanderWare availability.

The page must never assume that availability seen earlier in the day is still valid.

### Required refresh points

1. **Initial page/course load**
   - Fetch current availability.

2. **Course or delivery-method change**
   - Refresh availability for the newly selected offer family.

3. **Date/calendar interaction**
   - Recheck current availability when the calendar is invoked or a date is selected.

4. **Schedule for them / Move / `/go/` entry**
   - Fetch fresh availability before presenting bookable dates and times.

5. **Time selection**
   - Recheck that date’s current valid times.

6. **Final confirmation**
   - Perform an authoritative availability check immediately before writing the registration.
   - This final check is mandatory.

### Open-tab behavior

A MAXIM user may leave the page open all day while public and corporate bookings change availability.

Therefore:

- quietly refresh visible availability periodically while the tab is open;
- refresh immediately when the calendar is actively used;
- never rely on the timer alone;
- the final confirmation check is the source of truth.

If a previously visible time has disappeared, do not allow the stale booking. Refresh the UI and present the remaining valid choices.

The intended rule is:

**Calendar display = reasonably fresh.**

**Date/time interaction = freshly checked.**

**Registration confirmation = authoritative.**

---

## Registration persistence

Corporate registrations should be native LanderWare records and should not require Enrollware checkout.

A registration record should support at minimum:

- `person_id`
- `registration_id`
- `corporate_customer`
- `billing_account`
- `course_id` / normalized course family
- `class_id` / schedule reference
- `date_time`
- `registration_status`
- `source_renewal_id` when applicable
- `ecard_number`
- `ecard_url`
- `billing_batch_id`
- `stripe_invoice_id`
- created/updated timestamps

Person and registration must remain separate concepts.

One person can have many historical registrations and multiple credential types.

---

## Data sources for historical seeding

Use the following available sources non-destructively:

### Enrollware export
Use for:

- person identity
- registration history
- course history
- class dates
- promo codes / MAXIM identification
- legacy workflow state

### Assigned eCard spreadsheets in connected Google Drive
Use for:

- actual issued credential records
- eCard numbers
- issue history
- credential matching
- historical card-consumption reconstruction

Deduplicate duplicate files and duplicate eCard records.

### Stripe
Use for:

- MAXIM invoice records
- invoice numbers
- invoice status
- hosted invoice references
- historical billing linkage where confidence is sufficient

### Gmail
Use for future operational ingestion such as:

- eCard purchase receipts
- inventory receipts
- other structured supply orders

---

## Status derivation and human-mess recovery

The visible portal should stay simple, but the system should preserve enough event history to recover from real-world mistakes.

Avoid making the visible workflow columns themselves the database.

Prefer statuses derived from durable records/events such as:

- renewal surfaced
- link sent
- registration created
- registration moved
- class completed
- eCard issued
- invoice assigned
- renewal skipped

Keep a quiet audit trail for recovery.

Advanced controls should remain hidden until needed.

Examples:

- Move registration
- Cancel registration
- Resend scheduling link
- Copy scheduling link
- Change billing account
- Reopen renewal
- Unskip
- View history

---

## Duplicate and stale-state protections

- Do not create duplicate people silently.
- Repeatedly sending a scheduling link should not create duplicate renewal cycles.
- One active renewal cycle per person + credential should be the normal case.
- Repeated link sends should reuse or rotate access to the same underlying renewal intent.
- A person who tries to book twice should be told about the active registration and offered a move/change path.
- Stale dates/times must fail safely and return fresh alternatives.
- Links should be revocable.

---

## MAXIM page UX rules

The page should feel like a simple status board with a schedule attached, not enterprise software.

### Left side

- 50% scheduling area
- curated course choices only
- current live calendar availability
- date/time selection
- simplified prefilled registration form

### Right side

- 50% workflow area
- status tabs across the top
- full-height browseable list for selected status
- one detail drawer open at a time
- normal actions obvious
- corrective actions hidden but immediately available

### Primary MAXIM objective

The successful workflow is:

**Open page → find person → send link or schedule → done.**

The portal should minimize typing, navigation, and explanation.

---

## Current prototype status

Current interface prototype exists at:

`/corp/maxim.html`

The current interface is considered strong enough to serve as the Beta+ interaction model, but these pieces remain to be made real:

- live availability reads
- authoritative final availability check
- native registration persistence
- persistent `/go/` token service
- data-backed status tabs
- historical Enrollware/eCard/Stripe reconciliation
- renewal surfacing engine
- real Move behavior
- real Send Link / Skip / Resend behavior

Do not describe these as live until they are actually wired and verified.

---

## Implementation order

1. Replace hard-coded MAXIM availability with the same authoritative LanderWare availability source used by public scheduling.
2. Add refresh-on-interaction and final authoritative confirmation checks.
3. Add a native corporate registration store/API.
4. Make Schedule for them and Move write real registrations.
5. Implement persistent opaque `/go/` renewal scheduling tokens.
6. Build MAXIM identity/history import from Enrollware.
7. Reconcile Assigned eCard spreadsheets against people and registrations.
8. Link Stripe invoice history where confidence is sufficient.
9. Populate status tabs from real records.
10. Add renewal surfacing by end-of-month two-year expiration logic.
11. Add hidden correction controls and audit events.
12. Verify the complete self-service loop:
    - Coming Due
    - Send Link
    - employee schedules
    - Registered appears immediately
    - completion
    - eCard
    - invoicing

---

## Acceptance criteria for first real release

A release candidate is not complete until all of the following are true:

- MAXIM calendar displays current real LanderWare availability.
- Open tabs cannot rely on morning-stale availability.
- Date/time interactions refresh availability.
- Final registration confirmation performs an authoritative availability check.
- A real corporate registration can be created without Enrollware checkout.
- A person can be scheduled by MAXIM staff.
- A personalized `/go/` link can be created and used by an employee.
- Employee self-scheduling immediately appears as Registered on the MAXIM dashboard.
- Move replaces the active registration while preserving the old registration in history.
- Renewal dates show the full year and use end-of-month two-year expiration logic.
- Only one person detail drawer is open at a time.
- Workflow tabs remain simple and browseable.
- Historical MAXIM records can seed current/future renewal workflow without deleting old history.
- No feature is presented as live until its real data/write path is verified.
