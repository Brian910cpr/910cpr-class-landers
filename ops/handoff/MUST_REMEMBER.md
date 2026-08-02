# MUST REMEMBER — Anchor System Doctrine

## Core scheduling rule

- An unbooked public appointment possibility is a **barnacle**.
- The moment a barnacle receives its first confirmed seat, it becomes an **anchor**.
- Every future seated class is therefore an anchor, regardless of whether it began as a stand-alone appointment, an attached barnacle, or a traditionally scheduled class.
- Existing anchors must be evaluated and filled before the resolver creates another stand-alone start.
- A seated compatible class with remaining capacity should reuse its real Enrollware class registration link.
- New stand-alone starts are fallback inventory only, after compatible anchors and adjacent barnacles have been exhausted.
- The goal is not merely to avoid overlap. The goal is to consolidate the instructor's workday into tight, useful clusters instead of scattering individual students across the day.

## Visible schedule coding

- Anchors must be identified explicitly in generated data with `schedule_role: anchor` and displayed with an anchor icon.
- Unbooked attached offers are barnacles.
- A barnacle promoted by its first seat must appear as an anchor on the next authoritative schedule refresh.
- Anchor/barnacle status must come from scheduling data, not be guessed by the webpage from timestamps.

## Anchor lifecycle

When the first confirmed seat creates an anchor:

1. Create a permanent landing page for that exact session.
2. Use that session page as the canonical public URL.
3. Publish or update the anchor on LinkedIn.
4. Publish or update the anchor on Facebook.
5. Publish or queue it for AHA Atlas when a supported integration path is confirmed.
6. Make it eligible for event structured data, Google indexing, email, text, QR codes, and other promotion.
7. Generate compatible barnacles adjacent to the anchor.
8. Route later compatible students into the anchor before opening another cluster.

## Session landing page doctrine

Every anchor gets its own session-specific landing page containing the exact course, date, time, location, capacity/seats, registration action, course description, requirements, certification details, alternatives, analytics, social metadata, and event schema.

External platforms should point to the 910CPR session page, not directly to the raw Enrollware URL. The session page then hands registration to Enrollware for now and can later intercept registration, payment, CRM, student portal, eCard, reporting, and renewal workflows in-house without breaking published links.

## Publication lifecycle

- Barnacles are offered.
- Anchors are advertised.
- Time/location/capacity changes must update every published destination.
- Full anchors should stop active promotion or display as full with alternatives.
- Cancelled anchors should retain a useful landing page and direct visitors to current options rather than becoming dead links.
- Persist external platform IDs so updates do not create duplicates.

## Current known failure

The present implementation does not yet enforce this doctrine for BLS. It can recognize occupied time, but it does not reliably promote every seated BLS class into scheduling gravity, reuse existing compatible class links before creating later starts, or suppress scattered same-family starts. The August 5, 2026 pattern of 9:30 AM Renewal, 1:00 PM HeartCode, and 2:00 PM Renewal is the regression case that must pass before the anchor system can be called operational.
