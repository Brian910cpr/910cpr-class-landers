# Native Checkout completion checkpoint

Assignment: Native LanderWare Checkout / owner issue #270
Timestamp: 2026-10-12 America/New_York
Branch: codex/native-registration-bls-renewal
Commit: implementation commit containing this receipt (see git log -1)
State: IN_PROGRESS — production activation gated
Evidence: PROVEN isolated test, not production deployed or monitored

# Native Renewal checkout — implementation and isolated proof

2026-10-12 00:38 America/New_York. Branch: `codex/native-registration-bls-renewal`. Starting checkpoint: `a02eb2c5185575d25c93ecd7a024168d76216915`.

## Confirmed failures repaired

Public Checkout writes `landerware_public_orders`; the deployed webhook routed order metadata to the retail finalizer. The public finalizer inserted `active`, while Session Workspace accepts `registered`, `confirmed`, and `completed`. The eight-argument create-order overload bypassed the later seven-argument seat-count correction. Implicit materialization could convert external classes without fresh reconciled occupancy. Zero-price corporate invoice orders could be represented as paid without a verified payment.

The new migration replaces both creation overloads, requires an already eligible canonical operational session and matching Course Master ID, locks the class during hold/finalization, counts live holds and occupied seats, and requires fresh complete external occupancy when applicable. A hold lasts exactly 1,800 seconds. Finalization verifies Checkout/order/amount/currency/PaymentIntent evidence and atomically inserts operational customers/registrations, student associations, and durable confirmation messages. Late paid events recheck capacity; unsafe reconciliation records an explicit review reason. Duplicate events have no duplicate effects. Corporate invoicing is blocked pending an approved invoice workflow, rather than represented as paid.

The webhook verifies signatures, timestamp, payment status, expected live/test mode and order binding, routes public and retail orders separately, and retains the retail RPC contract. Missing orders are retryable. Failure/expiration events cannot downgrade paid orders. Browser recovery independently retrieves Stripe payment evidence before calling the same transaction. The public page retains its retry key across redirects, clears expired retry keys, shows instructor/seats, and preserves Enrollware fallback.

## Real Stripe test evidence

`data/audit/native_checkout_stripe_test_proof_20261012.json` contains isolated SQL state, actual Stripe IDs, webhook responses and the actual `summarizeSession` projection. No production DB writes occurred. Stripe account `acct_1LmpKHC9bZe0CGm2`, **livemode false**. Two distinct synthetic guest checkouts each paid $75; neither created a saved Stripe Customer (`customer: null`). No email worker or eCard process ran.

1. Order `7731dba2-6342-41af-81f6-15a5a8fd616f`; Checkout `cs_test_a1Bq0RlCKYOLxHN93wzmykBRpawOnzus5rEu50gooNzaWoTHPkjbOu6Llq`; PaymentIntent `pi_3UPas5C9bZe0CGm21rm2dKhl`. Server Stripe API recovery confirmed one seat. Initial test tunnel inherited an unrelated ingress config and returned 404; an isolated config corrected it. A locally re-signed replay of the real event returned idempotent success.
2. Order `1915f6a8-ecf0-4974-84b0-072d25a4629a`; Checkout `cs_test_a1P5SgMnbT9j9C9QiwScaH5XN0xrsPwkHB636G4WNnq6kGZalRJyDYvtKd`; PaymentIntent `pi_3UPawxC9bZe0CGm21o1wLNoG`. **Actual Stripe-delivered** event `evt_1UPawzC9bZe0CGm2vDGU6YIp` finalized at `2026-10-12T04:35:02.825Z`, HTTP 200, Stripe `pending_webhooks: 0`, before browser recovery. A locally re-signed replay returned `idempotentReplay: true`.

Final isolated state: two paid orders, two unique operational registrations/people, two Session Workspace roster entries, two occupied seats, ten remaining, no holds, exactly two pending paid confirmations. Both registrations have `registration_source=landerware_native_checkout`, status `registered`, and no Enrollware registration ID. This status is the actual canonical operational confirmed-seat contract.

The isolated session cloned a genuine validated Renewal offer: October 14, 2026, 7:30–9:30 PM Eastern, consumption through 10 PM, Brian Ennis, Shipyard B; course 359474, $75. Feed `bls.json`, appointment day 260785, right-edge anchor 14589762, source session IDs 14589762 and 4952c8b3-ee5f-4e08-8291-4e0fef061252. This snapshot was fresh when selected but must be revalidated before release. No existing external class was converted. Production external classes 14377157/14601690 had 2/1 registered seats and stale October 10 reconciliation; they are not approved native inventory.

## Validation

- Node: 26 passed, zero failed across native SQL lifecycle (8), existing reconciliation lifecycle (1), webhook (10), existing workspace baseline/authorization (7).
- Python public-registration suite: 11 passed. Stale renderer assertion corrected to exercise selector offer behavior and preserve external/native URLs.
- Edge TypeScript stripping/VM parsing and inline HTML JavaScript syntax passed; `git diff --check` passed.
- Local browser displayed “Registration confirmed” after actual test payment. Visual evidence saved in the chat outputs folder.
- Failure cases: duplicate submissions/events; multi-student count; competing final-seat requests; abandoned/expired holds; late payment with/without remaining capacity; unpaid/canceled/failed event behavior; bad amount/course/currency/Checkout binding; invoice bypass rejection; message enqueue rollback/retry; failed delivery preserving paid registration; stale external occupancy rejection.

Limitations: PGlite is real PostgreSQL execution with a reduced existing fixture, not a deployed Supabase staging project. Concurrent application calls share one engine; distributed multi-connection contention and actual production constraints/triggers require a staging canary. Stripe API calls were transported through the authorized connector into the actual Edge handlers; their HTTP/DB adapters were local. Confirmation **queue** is proven; sending was intentionally disabled. The initial fixture lacked `channel`, so optional recovery-email enqueue failed without blocking either checkout; the reusable fixture now includes it. Actual Session Workspace projection was executed against resulting records; the authenticated production workspace was not mutated. Corporate billing and other families are not claimed proven.

## Narrow release — pending explicit owner approval

Database: apply only `supabase/migrations/20261012060000_public_checkout_integrity.sql`. It adds three public-order audit columns, adds service-only seat-state RPC, replaces both creation overloads and both public-finalizer overloads. No parallel registration tables or new dependencies. Capture current function definitions and affected schema before applying; inspect all constraints/triggers in staging first.

Functions: deploy only `public-registration` and `stripe-registration-webhook`, preserving existing secrets, JWT/public access settings and bindings. Production expects live mode (default true). Preserve existing live endpoint and signing secret; verify its subscribed completed/async events. No webhook configuration change should be needed if current subscriptions match. The temporary **test-only** endpoint `we_1UPanDC9bZe0CGm2bBUbdzCh` is disabled after proof.

Page: publish only `docs/register/index.html`; no sitewide generator, selector rebuild or family replacement. Inline JS travels with the page; existing external assets are unchanged. Existing Enrollware links remain fallback.

Inventory activation: separately approve one native-open Renewal session only after a fresh authoritative offer/conflict check, reviewed Course Master capacity, and current occupancy/commitments. Do not convert an Enrollware-managed session. The proof-session UUID is isolated and must never be copied into production. Check updated public API seats and the actual owner roster after activation.

Known timing boundary: Stripe requires Checkout expiration at least 30 minutes after creation. Checkout uses the fixed hold expiry plus 60 seconds, while the database hold remains exactly 30 minutes. A payment after hold expiry cannot bypass the fresh capacity check and may require review/refund if sold out. Delayed async payments have the same review boundary. Recreating an uncreated Checkout more than a minute into an old hold can fail Stripe's minimum; the safe recovery is a new availability check, not extending occupancy.

Rollback: close only newly enabled native sessions, keep Enrollware fallback, preserve paid orders/registrations and Stripe evidence. Drain/reconcile any paid webhook deliveries before reverting Edge functions. Do not restore the old finalizer/status bug over already paid orders. Audit columns may remain; restoring previous RPC definitions is a separately reviewed operation. Never delete payments or registrations to roll back.

## Proof and monitoring contract

Evidence level: **PROVEN in isolated test; BUILT, not deployed in production**. Last real webhook proof: 2026-10-12T04:35:02.825Z. Expected purchase outcome: matching paid Stripe Checkout, canonical registration/student count, roster and occupied seats, durable confirmation, no duplicates.

Production gate must include the existing operational observer checking: paid orders without complete registration associations; `reconciliation_error`; Checkout-open orders whose Stripe payment succeeded; failed/pending confirmation delivery beyond five minutes; count disagreement. Compare Stripe API evidence during reconciliation, never browser redirects. Check observer last-success heartbeat and escalate if older than two cycles. Recovery: retry verified finalization/queue delivery; capacity or identity review requires owner resolution/refund decision. **Automatic production observation is not activated or claimed monitored by this change.** Its canary and observer-health evidence remain release requirements.

Unrelated unstaged files preserved: `docs/Earl/index.html`, `docs/Jackson/index.html`; Python test execution changed three already-tracked `scripts/__pycache__/*.pyc` files, intentionally excluded from commits. No cleanup/reset performed.


## Exact changed files
- supabase/migrations/20261012060000_public_checkout_integrity.sql
- supabase/functions/public-registration/index.ts
- supabase/functions/stripe-registration-webhook/index.ts
- docs/register/index.html
- tests/test_public_registration.py
- tests/stripe_registration_webhook.test.cjs
- tests/reconciliation/native-checkout-harness.mjs
- tests/reconciliation/native-checkout-server.mjs
- tests/reconciliation/native-checkout.test.mjs
- data/audit/native_checkout_release_20261012.md
- data/audit/native_checkout_stripe_test_proof_20261012.json
- Codex_Reply_NativeCheckoutProof_20261012.md

Owner decision: approve a staging canary and then a separately gated narrow production migration/two-function/page release and one freshly validated native Renewal session. No broad generated-output publication authorized or performed. Recommended next step: stage the exact migration against a production-equivalent schema and run multi-connection seat contention, confirm queue-worker delivery with an approved test recipient, wire the existing observer, then request final activation approval.
