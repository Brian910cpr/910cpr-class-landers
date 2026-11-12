# Native full Heartsaver publication

This is an additive, default-off extension of the existing native publisher and layered scheduler. It is not an activation or a deployment receipt.

## Exact scope

- Full classroom 209809: canonical course 23dfcfa7-4224-46ed-8d45-64d43d5425db, policy heartsaver-full:209809.v1, 120 minutes teaching plus 30 minutes cleanup.
- Full classroom 344085: canonical course 306bc81a-0e09-49e1-8910-e05501222eb4, policy heartsaver-full:344085.v1, 90 minutes teaching plus 15 minutes cleanup.
- Only the existing Brian/Shipyard B scope is admitted. Blended 209808/329495, pediatric and other families are not admitted by this extension.
- The separate 509474 skills gate and its canonical contexts remain independent. Full-course choices never route through a skills context.
- Both real Heartsaver public capacities remain NULL in the predecessor migration. Historical catalog defaults, group-order limits and test capacities cannot establish public seats.

## Gates and original proof

The existing publication configuration gains boolean heartsaverFullEnabled, default false. The global enabled gate is still required. With skills off, Heartsaver adds exactly four paths to the six BLS paths: heartsaver.html, HEARTSAVER.html, heartsaver-schedule.html and the Heartsaver selector JSON. With skills on, the allowlist remains fifteen paths.

Only when heartsaverFullEnabled is true does the demand fetch request native_heartsaver=1. The ordinary demand request does not call the new policy RPC, allowing source and endpoint deployment while the new schema is absent. Missing/disabled policy cannot fall back to an external URL or a local guessed capacity.

The service-only STABLE native_heartsaver_publication_policy() RPC supplies exact course policies, the original database observation, a fifteen-minute lease and the earliest applicable qualification expiry. This proof remains private input. The layered scheduler still owns intervals, uncertainty, closures, travel, canonical occupancy and consolidation. Accepted full-course offers must match both the first-party calendar and exact course policy. Their expiry is the minimum original lease; generating a later page does not extend either proof. Qualification must cover the consumed end of the class.

Public dynamic rows carry coursePolicyKey and separate calendar/policy observation stamps. Dynamic alternatives carry no separate capacity pools. They use the existing /register/skills-session/?course=...&selectionId=... route, whose server reads the matching Heartsaver feed, checks current policy, and revalidates the option before materialization/reservation.

## Existing seats

The additive SQL extends the existing native_scheduling_seat_snapshot STABLE reader, guarded against predecessor-definition drift. It retains registered/held/inherited occupancy and unresolved-payment liability behavior. A separate heartsaverBooking DTO is emitted only with exact course/profile/canonical identity, enabled publication policy, through-class qualification, geometry, location, verified capacity and no conflicting alias or unresolved liability. BLS and skills booking DTOs remain unchanged.

The publisher discards every prior public booking decision, then re-admits existing seats from the fresh canonical DTO and fresh course proof. The occurrence remains an occupancy blocker if admission is unavailable. A held/materialized Heartsaver class is published once, using the existing /register/?session=... route with its remaining seats. It is not recreated as another dynamic capacity pool.

## Safe integration order

1. Review source, exact migration predecessor hashes and isolated synthetic tests. Keep all new gates false.
2. Deploy source/endpoint with the optional request still off. Verify the unchanged BLS-only path against the currently installed schema.
3. Apply the reviewed full-course scope migration, then this publication migration, with capacities NULL and gates off. Verify service-only privileges, predecessor guards and read-only snapshot contracts.
4. Establish the two real public seat caps, capacity evidence, exact BLS qualification provenance and expiry, bound active profiles, canonical prices and active catalog. Verify public display prices agree with backend prices. Enable only explicitly reviewed course scope(s).
5. Complete the independent confirmation-transport closure below before treating customer registration as an end-to-end operational replacement.
6. Enable hosted publication for an approved course and the source Heartsaver gate, fetch fresh original proof, run the bounded existing publisher, and validate exact output manifests before any authorized publication.
7. Verify the exact deployed selector, dynamic checkout, materialization, held/registered continuation, payment result, participant attachment, confirmation and stale-proof recovery. Observe repeated cycles before assigning operational health.

No step above is performed by this source change. Activation, credentials, payment and email operations require their normal authorization.

## Separate confirmation closure

This change does not expand transport. landerware_checkout_delivery_config.course_ids currently defaults to the existing BLS/skills IDs and excludes 209809/344085. Do not update that default or overwrite an installed scope as a publication side effect.

A separate reviewed closure must:

- Approve the exact additional course IDs, existing provider, recipient scope and not_before boundary; inspect pending messages to avoid a historical backlog replay.
- Verify the profile confirmation template binding, paid-order/student/canonical-registration joins, exact classroom course/date/time/location, and absence of online-course/keycode promises for these full classroom profiles.
- Exercise native_checkout_claim_confirmation and native_checkout_settle_confirmation with existing idempotency, rejected retry limits and ambiguous-send handling. Prove a queued paid registration, provider receipt and actual receipt at the authorized owner test address before customer-scope activation.
- Verify the scheduled sender and health observer remain fresh, and that course-scoped pending/failed/ambiguous counts include the newly approved IDs. Existing customer sends must not be enabled merely by setting a publication gate.

## Proof and recovery contract

Expected outcome: fresh scoped calendar policy produces correct native choices, one canonical registration/session lifecycle and correct remaining capacity. Required durable evidence is the bounded publication manifest, exact deployed asset/feed hashes, canonical order/session/registration relationship and confirmed delivery outcome.

The original proof expires after at most fifteen minutes; the existing runner reserves five minutes for publishing and one minute for observation. Expired, incomplete or changed proof suppresses selection and prevents publishing. The existing publication observer/maintenance and confirmation scheduler observer remain the health boundary; this extension does not create an unrelated scheduler.

Recovery is a fresh canonical/calendar read and bounded rebuild, never copying an old lease, guessing empty occupancy, removing an unresolved liability, re-sending an uncertain message or using a retired external booking fallback. Capacity decisions, qualification evidence, authorization and provider/account failures are escalation boundaries. Browser/CI or local test success is BUILT evidence, not a production end-to-end proof or a HEALTHY claim.

## Local and CI checks

- Python: python -m unittest tests.test_native_heartsaver_publication
- Endpoint and database: node --experimental-strip-types --test --test-concurrency=2 tests/native_heartsaver_demand_endpoint.test.cjs tests/native-heartsaver-publication.test.mjs
- PostgreSQL17: tests/native-heartsaver-publication-concurrency.mjs, using a fresh explicitly isolated skills_claim_test_223000 database and the existing local-postgres address guards.
- Browser: python -B -m unittest tests.test_native_heartsaver_publication_browser -v. The native verification workflow installs Playwright 1.56.0 plus Chromium in a separate browser-contracts job. Every request is intercepted; unknown destinations abort. Missing browser capabilities fail instead of skipping tests.
