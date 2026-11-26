# Native offer claim: admission policy draft

This change is deliberately inert: no function route, deployment, database
migration, published JSON, checkout link, or email is added. Run
`node --test tests/native-offer-admission.test.mjs` to exercise the reference
policy. It only admits synthetic test mode. An admission is not a hold.

## Why this path

The incumbent appointment container governs where a prospective student can
land, while its scheduled occurrence owns enrollment. Preserve that separation,
but let a qualified instructor's LanderWare availability own candidate discovery
without cloning the incumbent's container. Keep the canonical course, room,
instructor qualification, occurrence, registration and payment relationships
separate. Existing concrete-session checkout and hard-coded skills checkout
remain untouched. Actual authoritative prices and course assignments are not
inferred from the test fixtures.

## Server boundary

1. The scheduler supplies approved private offer identity, exact UTC start and
   end, and the normalized occupied interval. The opaque public selector is
   only a locator, not authorization, a session ID, or a secret. The claim
   endpoint must resolve it to a current authoritative candidate, including all
   anchor, bookend, cleanup and blocking constraints; possession of the selector
   is never enough. Never send the admission object to clients.
2. Under a transaction, lock/check both instructor and room across competing
   intervals, checking the canonical facts, fresh covered calendar/occupancy
   revision, qualification and course policy. Run admission against that
   authoritative state. Evidence completeness and validity must be established
   by the authoritative adapter, not accepted from a client. If the coverage
   revision changes during claim, fail closed and recalculate.
3. Atomically select or create the canonical occurrence and attach an expiring
   hold, preserving provenance. Separate locking for overlapping resources
   and capacity for the same occurrence is required, with a stable lock order.
   A second customer can join the same proven occurrence if seats remain; an
   equal timestamp is not proof of sameness. An authenticated retry must replay
   the same hold for the same intent and reject changed intent. Expired unpaid
   holds restore capacity and trigger recalculation, not a saved availability
   snapshot. No runtime store or concurrency guarantee is implemented here.
4. Create Stripe Checkout only against a committed hold, using an idempotent
   provider request. Reconcile Stripe's payment/expiry timing with the shorter
   internal hold, including late paid events, so a second checkout does not
   sell the same seat. If timing cannot guarantee capacity, quarantine/reconcile
   without promising an oversold seat. Validate the verified provider event's
   hold, payment, amount and currency. Persist confirmation and deduplicated
   customer/instructor outbox records in the same transaction only for a
   verified registration. Notify the canonical assigned instructor without
   routing back through the incumbent.
5. In a protected test environment, prove competing claims, duplicate/reordered
   events, failed and delayed payment, cancellation/expiry, no duplicate emails,
   and no private record disclosure. Then verify the actual customer entry and
   notification with test transactions before enabling production. Until that
   proof and separate release, maintain existing request-only behavior wherever
   no owned checkout exists.
