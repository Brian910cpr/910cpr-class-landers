# Native BLS Renewal: first implementation checkpoint

Status: assessment completed; webhook hardening BUILT and locally validated. Native purchase NOT PROVEN. Production unchanged. No charges, Checkout sessions, customers, registrations, or database writes created during this assessment.

## Production evidence

Read-only Supabase project: LanderWare `wktwgcnwdvbebcobgyey`. Read-only Stripe account: 910CPR LLC. Stripe reauthentication succeeded after owner reconnection.

- Course `359474`, canonical course key `aha-bls-provider-renewal`, existing catalog price 7500 USD cents, active. Do not invent prices or IDs.
- Live `GET /functions/v1/public-registration/session/14377157` returned HTTP 200, Renewal, October 17 2026 10:00–12:00 America/New_York, Shipyard B, $75, with existing Enrollware fallback.
- Database session `3b2731a3-19bb-4d10-9757-08a8e81e336f` for that offer is scheduled, capacity 20, backend Enrollware, registration_status `external`; public order RPC requires `open`. October 24 class `14601690` has the same mismatch. No future operational public native-open Renewal sessions and no matching public-session inventory rows for the four public Renewal offers checked. Do not simply open these sessions without verified external occupancy and instructor/location checks.
- Deployed webhook version 10 reads metadata.landerware_order_id and invokes `confirm_retail_payment`. Production definition reads `landerware_retail_orders`; public Checkout creates `landerware_public_orders`. This is a confirmed table/RPC routing mismatch, not evidence of a stranded paid customer.
- Production public finalizer creates `registrations.status='active'`. Canonical Session Workspace and external roster proof accept registered/confirmed/completed. Existing paid public students currently have registered status, so this inspection did not prove an invisible current paid customer.
- Production public hold-count RPC counts only active registrations; that excludes registered/confirmed/completed seats. Existing source uses greatest(native registered, external registered), requiring careful overlap-aware reconciliation rather than blindly summing or taking a maximum.
- Public finalizer has no hold-expiry, amount/currency, Checkout-session binding, or paid-event validation inside its service-only database function. Edge verification checks payment_status but not full order amount/currency/metadata binding.
- Canonical retail hold is 31 minutes; requested contract is 30. Public orders already use 30 minutes. Reuse one existing path deliberately rather than adding a third order model.
- Four public orders: two checkout_open ($95 and $75), two paid with total zero and no_payment_required evidence. Zero-total orders are not proof of a Stripe purchase. Retail orders: zero.
- Stripe endpoint `we_1U7vPFC9bZe0CGm21enewKW7` is enabled for completed/async-success/async-failure, pointing to the existing Supabase webhook. Listing available completed/async-success events returned eight, all pending_webhooks=0, none with a LanderWare order metadata ID. This proves neither successful native purchase reconciliation nor endpoint-specific delivery history. Do not close #287 from this evidence.

## Existing implementation to reuse

- `docs/register/index.html`: student form, multiple students, idempotency key, recovery/success UI, add-ons/billing inputs.
- `supabase/functions/public-registration/index.ts`: trusted schedule/catalog lookup, hold RPC, Checkout creation, server Stripe retrieval, recovery and queued emails.
- `supabase/functions/stripe-registration-webhook/index.ts`: existing payment webhook and legacy event handling.
- `supabase/migrations/20260909220000_native_public_checkout.sql`: public order/student/inventory tables and finalization.
- `supabase/migrations/20260910100000_first_party_retail_checkout.sql`: canonical retail orders, begin/confirm RPCs, profiles, roster and transactional message enqueue.
- `supabase/migrations/20260930050000_per_student_public_billing_codes.sql`: per-student billing/add-ons and invoice lines.
- `supabase/migrations/20260930210146_assign_bls_offer_instructor.sql`: existing initial-only materialization; never hard-code Brian or six seats for unvalidated Renewal offers.
- `supabase/functions/canonical-session-workspace/index.ts`, `supabase/functions/_shared/external-roster-proof.ts`: current operational roster/count truth and external reconciliation gates.
- Existing PR #127 inspected: older front-door work also changes builders/importer; preserve it rather than merging blindly over the newer public checkout. This checkpoint isolates changes on `codex/native-registration-bls-renewal` based on production commit e2304a1decff1a925878faf69fdc3027e63c8522.

## Changed now

`supabase/functions/stripe-registration-webhook/index.ts` rejects signatures outside a five-minute absolute tolerance, malformed/ambiguous timestamps and invalid signatures; accepts any matching v1 signature during rotation; requires payment_status paid for both supported success events. Existing reconciliation behavior is preserved pending the complete transaction repair.

`tests/stripe_registration_webhook.test.cjs` runs actual TypeScript handler/verifier in Node with local crypto and a fake database. These are local behavioral tests, not a Stripe transaction or database atomicity proof.

## Validation

- `node --test tests/stripe_registration_webhook.test.cjs tests/enrollware_roster_proof.test.cjs`: 16 passed, zero failed (7 new webhook tests, 9 existing roster tests).
- `node --check --experimental-strip-types supabase/functions/stripe-registration-webhook/index.ts`: passed.
- `git diff --check`: passed for intentional changes.
- Existing `tests.test_public_registration`: 11 run, 1 pre-existing failure: test_only_real_bls_initial_sessions_route_to_native_registration. It asserts an older inline renderer guard absent from current main. Do not relabel that string assertion as end-to-end proof or erase it to obtain a green report.

## Smallest remaining vertical slice

1. Reuse public multi-student holds and operational class_sessions/registrations, with explicit canonical bridge compatibility. Do not switch to the single-student retail path solely because its names look canonical: current Session Workspace actually consumes class_sessions/registrations.
2. Bind server-verified payment to the persisted Checkout ID, order, currency and amount; route public and retail orders explicitly without guessing. Atomic finalization must enforce paid transition, expiry/seat policy, idempotency and durable confirmation enqueue. Browser interruption must not prevent fulfillment.
3. Align finalization and seat-count statuses with existing roster truth. Protect legacy external seats with fresh complete reconciliation, including mixed native/external registrations.
4. Admit one real Renewal offer only after instructor/location/course/capacity/external-seat validation. Keep Enrollware fallback. The live GET endpoint currently overstates native readiness.
5. Keep approved corporate invoicing separate from paid status, enforce billing authorization, and preserve receipt/confirmation semantics. A zero total is not necessarily a paid invoice.
6. Local transaction tests: duplicate submits/events, last-seat concurrency, expired hold with late payment, failed/canceled/abandoned checkout, multi-student atomicity, corporate unpaid invoice, recovery, email enqueue/delivery failure.
7. Owner approval for the reviewed narrow migration/function/public route release, followed by an approved sandbox or no-unauthorized-charge end-to-end proof. This checkpoint requests no broad build or production activation.

Acceptance proof must join persisted order, server Stripe payment evidence, operational/canonical session and registration IDs, instructor/admin roster, durable confirmation and delivery receipt, and updated remaining seats. Repeat event and reload must leave exactly one seat per student. No such complete proof exists yet.

## Operational health and rollback

BUILT only for the local webhook patch. No last successful native Renewal purchase. No proven monitor for payment-to-registration-to-roster agreement. Required observer should alert on verified paid Checkout lacking confirmed registration/roster/confirmation within its defined fulfillment window; retain webhook diagnostics and separately observe the monitor. Production source remains unchanged, so rollback is not needed for this checkpoint. Before deployment, preserve version 10 and existing SQL definitions, and prepare forward-compatible rollback without dropping registrations or external seats.

Unrelated Windows-collision dirty files `docs/Earl/index.html` and `docs/Jackson/index.html` remain unstaged. No generated output was rebuilt.

Related durable work: #270 native registration; #287 webhook integrity; #367 bundles. Native registration is primary P1; CRM expansion waits, genuine active P0 incidents may interrupt.

Reference behavior: https://docs.stripe.com/webhooks/signature and https://docs.stripe.com/payments/checkout/fulfill-orders ; database security: https://supabase.com/docs/guides/database/functions .
