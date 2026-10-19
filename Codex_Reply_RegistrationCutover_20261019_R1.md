# Codex Reply — Registration cutover audit and delivery repair, October19 R1

Timestamp: 2026-10-19, America/New_York.
Assignment: audit existing class registration, finish gaps using existing systems, keep Enrollware until replacement proven. Customer Interaction Studio stopped/denied; no CRM work or provisioning resumed.
Branch: codex/registration-exit-audit-20261019; existing PR416, not a new PR.
Substantive commit: 8bbb04e6c70396996349c7d19972e9286ccc692c.
Receipt commit: pushed branch tip reported in PR416 checkpoint.
State: PR_OPEN; BLOCKED for account-connected release. Production Enrollware exit NO-GO.

Read AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Used Stripe/Supabase/Workers/Wrangler/email guidance and existing PR387/416 code/tests. No new registration table/model, checkout, catalog, outbox, monitor, scheduler or paid environment. Mature operational behavior is retained: explicit person/registration/session identity, seat holds, verified payment before fulfillment, immutable retry receipts, manual material fulfillment, observed delivery and legacy booking during cutover.

## Findings and bounded repair

Full primary report: data/audit/registration_cutover_20261019.md. Exact sanitized evidence/metrics: data/audit/registration_cutover_20261019.json. Read the full report rather than relying on this summary; it contains the stage-by-stage dependency matrix and concrete release sequence.

Live schedule publishes26 future sessions,25 Enrollware booking URLs and1 native URL. Live BLS HTML lacks the draft inline-registration asset/native-register route. Supabase public-registration v19 lacks nativeReady/payment-evidence safeguards; stripe-registration-webhook v10 lacks the public finalizer route and five-minute signature guard. Production verified-seat function, payment_evidence column, confirmation delivery config/health/provider-event table are absent. These source repairs already exist in PR387/416; they have not been released. No new competing implementation.

One native candidate is Renewal Nov3 noon–2PM Eastern, configured capacity20 and instructor/location present. GET/session returns200/$75 with no verified seat evidence. Capacity20 is observed configuration, not a validated operational cap or release approval. External/mixed classes must keep completeness/freshness reconciliation and existing booking fallback. Legacy course IDs and imported snapshots are provenance; not all such names imply a remaining live dependency.

New defect reproduced: current draft health returned healthy=true after provider acceptance despite a later bounce or overdue missing delivery evidence. Two tests failed true!=false before fix. Existing UNAPPLIED migration20261017210000_email_delivery_events.sql now extends the same authenticated health RPC with deliveryFailures and deliveryUnconfirmed, uses existing recipient-bound message history and configured scope, and marks bounced/failed/rejected/complained or >10min missing/deferred evidence unhealthy. No auto-resend. No new notification channel. Production does not have this migration; another already-applied environment would need a corrective migration rather than rewritten history.

## Exact intentional files

- supabase/migrations/20261017210000_email_delivery_events.sql
- tests/reconciliation/email-delivery-events.test.mjs
- data/audit/registration_cutover_20261019.md
- data/audit/registration_cutover_20261019.json
- Codex_Reply_RegistrationCutover_20261019_R1.md

Review existing integration sources: supabase/functions/public-registration/index.ts; supabase/functions/stripe-registration-webhook/index.ts; supabase/migrations/20261012060000_public_checkout_integrity.sql; worker/checkout-confirmation.mjs; worker/wrangler.checkout-confirmation.jsonc; docs/register/index.html; docs/assets/inline-registration.js; scripts/build_schedule_future.py. Existing class/roster/identity records remain authoritative.

## Validation

Baseline78passed,0failed. New health regressions2failed before correction. Provider-event suite after correction5passed,0failed. Final full existing checkout/mail suite80passed,0failed; exit0:
node --test --test-reporter=dot --test-concurrency=1 tests/inline_registration.test.cjs tests/embedded_registration_payment.test.cjs tests/public_registration_option_errors.test.cjs tests/stripe_registration_webhook.test.cjs tests/checkout_confirmation_worker.test.mjs tests/checkout_email_template.test.mjs tests/crm_messages.test.cjs tests/reconciliation/native-checkout.test.mjs tests/reconciliation/bls-options.test.mjs tests/reconciliation/checkout-confirmation.test.mjs tests/reconciliation/message-operational-links.test.mjs tests/reconciliation/checkout-reminders.test.mjs tests/reconciliation/email-delivery-events.test.mjs

Node --check Worker and changed test:PASS. JSON ConvertFrom-Json:PASS. git diff --check:PASS. Wrangler4.151.1 deploy --dry-run --config worker/wrangler.checkout-confirmation.jsonc --outdir(projectless work/registration-audit-worker-20261019):PASS,13.45KiB compiled,no upload. SQL exercised with real migration text in local PGlite; not independent remote backend sessions, provider delivery or a production transaction. No public source/output changed by this repair; fetched live HTML verifies current state only.

## Exact blockers / owner actions

- Stripe connected list_available_accounts_or_orgs returned UNAUTHORIZED: reconnect app. No Stripe account/mode or webhook destination was independently verified through this connector; no fallback credential retrieval/real charge.
- Cloudflare wrangler whoami returned9109: saved access token cannot be used from current network location. Correct that existing token's authorized network restriction or supply an appropriately scoped existing deployment credential privately. No repeated failing auth path or broadened permissions.
- PR416 draft currently mergeable=false. Main compare reports363 later commits touching scheduling/public projections; do not overwrite those pages. Main fetch with gh credentials and bounded low-speed timeout failed curl28; cached main not used as current. Preserve this pushed review branch and unrelated dirt before integration; no merge/rebase/reset/force push attempted.
- Real production-equivalent schema/default-ACL/concurrency, confirmed capacity, approved sender/consumer and outcome observer, usable backup/rollback and explicit bounded rollout/canary remain gates. Existing message_operational_links is already applied under version20261018004708; match content and avoid blanket replay.
- Reschedule/cancel/refund and actual material/credential fulfillment require staff-usable lifecycle proof. Cancellation reminder-suppression tests do not prove refund or seat-release operations. Enrollware class/report/iCal/roster dependencies still exist. Keep current bookings and source archives.

Only immediate Brian actions: reconnect Stripe and correct Cloudflare's existing token/network authorization. No paid resource approval requested. Once access and operational gates are satisfied, present the exact bounded production migration/function/Worker/page/canary set for existing rollout approval; do not call this test package a production fix.

GitHub issue CLI reports repository issues disabled; report on existing PR416 without changing repository settings. No new PR. Unrelated dirty docs/BLS.html (case-collision projection) preserved/excluded; no generated outputs/cache/runtime artifacts staged. Original CRM checkout's unfinished audit and dirt untouched. No source generator or sitewide build, production SQL mutation, deploy, real payment, customer email, live credential, resource provisioning or automation change occurred. Codex_Read files untouched.

Persistent proof: foundation BUILT; this defect locally PROVEN in synthetic SQL evidence. Production registration-to-delivered-confirmation remains NOT PROVEN/MONITORED/HEALTHY. On-demand useful outcome is one verified payment -> canonical student registration/seat/roster -> delivered confirmation -> traceable fulfillment/completion. Missing/review payment or roster, stuck lease>5min, queue/provider evidence>10min, poll>3min and stale observer are failure conditions. Existing delivery RPC/Worker is intended observer surface, but no connected production outcome observer is established here. Recovery preserves receipts and intent, investigates unknown sends without resend, reconciles current state and retains legacy booking for unmigrated classes. Brian must not become the routine checker.

ChatGPT next: review the full primary report and exact source/test change; restore account access, reconcile existing PR416 against fresh main without clobbering scheduling, complete controlled release/fulfillment/cancellation proof, then expand native class families before any Enrollware termination.
