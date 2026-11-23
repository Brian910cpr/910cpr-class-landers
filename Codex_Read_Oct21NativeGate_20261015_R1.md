# October21 native registration protection deployed

Branch `fix/oct21-native-gate-20261015`, based on merged public closure main8f0692d3ce7. Owner explicitly authorized all new October21 registrations closed while preserving existing booked records and payments. No new policy approval is needed. PR409 public closure remains live; this is its native follow-up, not a change to PR408.

## Effective protection

- Database migration `20261015195848_enforce_owner_oct21_registration_closure` deployed successfully via the supported migration API. It compiles the existing `docs/data/public-registration-closures.json` verbatim into a service-only policy function and a SECURITY INVOKER pre-write assertion. No business rows, registrations, classes, holds or payments were changed by this migration.
- The assertion is inserted at the first executable statement of six existing PL/pgSQL entrypoints: both `landerware_create_public_order` overloads, `landerware_register`, `queue_public_registration_intent`, `start_public_registration_intent`, and `maxim_replace_registration`. Each current deployed body, security mode, owner and grants is otherwise preserved dynamically. Both known dates and actual canonical/workspace dates are checked, including workspace-only Jessica by ID, without inventing a workspace registration_status field. Queue writes, new holds, person/registration writes, BLS materialization and replacement releases are blocked before their first work when the selected interval is closed.
- `public-registration` Edge Function version19 deployed; verify_jwt=false is preserved from verified deployed version18. New lookup/start checks run the same SQL assertion before catalog/hold/payment work. Unpaid recovery no longer returns a checkout path for a closed class. Existing paid orders and completion/finalization remain outside the new-registration gate. Existing asynchronous route promises are now awaited so closure exceptions reach the handler and return409 rather than escape as an unhandled error.
- Live read-only GET `/functions/v1/public-registration/session/14721759` returned **409 registration_date_closed** at20:00:17UTC. Other-day session14377157 returned200. No registration POST, real student, payment, charge or email was submitted.

## Tests and evidence

`node --test tests/native_registration_closure.test.cjs`: **8 passed**, using the actual TypeScript endpoint in a network-free VM. Tests reject closed GET and POST before any simulated mutation, cover Jessica's workspace fixture, overnight overlap, unaffected other-day lookup, unpaid recovery and existing paid-order completion.

`python -m unittest tests.test_native_registration_closure_sql tests.test_public_registration_closures`: **9 passed**. Generated SQL uses the exact existing public policy, targets six guards and has no business INSERT/UPDATE/DELETE statements. The compiler is deterministic; the saved migration filename uses the actual server-generated version because a local Supabase CLI is unavailable.

Live pure SQL probes: three closed boundary/interior timestamps rejected; preceding interval touching the closure and following boundary accepted; Jessica workspace UUID rejected without a row write. All six deployed entrypoints independently read back with the guard marker. Service-only policy/grants retained; security-advisor read returned no finding mentioning either new helper. This is scoped evidence, not a claim that unrelated baseline advisories are resolved.

The broader existing `tests.test_public_registration` suite has10 passes and one unchanged generated-BLS routing assertion failure: it expects `String(course.courseId) === '209806'` in an unchanged BLS page. The current page and baseline text are identical and that assertion is absent in both. No unrelated page/routing repair was attempted. Total combined Python run:19 passed,1 baseline failure. Initial Node tests found the real missing-await error handling; after the targeted fix all8 pass.

Bounded live evidence and exact remaining provider URLs: `data/audit/oct21_native_gate_live_20261015.json`. No secrets or participant PII committed.

## Remaining external paths and limits

Owner must close online registration at Enrollware for these observed October21 class IDs while preserving roster/class records: `13895152`, `13895154`, `13895155`, `14721759`. URLs are `https://coastalcprtraining.enrollware.com/enroll?id=<ID>`. October21's owned appointment day is260792; the evidence JSON lists21 previously published exact course/start appointment URLs requiring provider-side closure. These are blocked from our selectors but native guards cannot control direct Enrollware URLs or a provider browser already open there. Verified-certifi access returnedHTTP403 and CyberPC CUA failedHRESULT0x80070003. No bypass attempted.

Existing already-issued Stripe-hosted checkout URLs were not expired or mutated, and paid-order reconciliation/webhooks remain available. This task prevents new native order/hold creation and unpaid recovery from exposing a checkout path; it does not claim revocation of an already-issued external payment URL. No already-paid booking/payment is reversed or suppressed. The fixed October4-only public-event endpoint cannot select October21; existing-payment webhook updates were intentionally not treated as new registration requests.

Rollback/reopening: remove the explicit closure from the same JSON and compile/redeploy its policy function through the reviewed migration procedure; guards then pass unchanged. Independently closed canonical rows are not reopened implicitly. Roll back Edge v19 to the saved matching v18 source only through normal review if required. No destructive data rollback is needed.

## Delivery

Native protection is already deployed under direct owner authorization; the follow-up PR commits exact source, compiler/template, actual migration, tests and receipt for review/recovery. No broad generator, public site rebuild, Enrollware mutation, customer message or duplicated native row closure. Local generated `native-closure-reviewed.sql` is an unstaged review artifact, excluded from the PR. Original builder state was preserved reversibly in a stash after automatic approval review rejected restoration; no rejected restoration or direct-main action was retried.
