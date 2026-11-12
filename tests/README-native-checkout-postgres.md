# Existing native checkout PostgreSQL gate

The real race tests are `skills-native-concurrency.mjs`,
`skills-checkout-concurrency.mjs`, and `generic-checkout-concurrency.mjs`.
The existing `verify-skills-native-claim.yml` workflow supplies an isolated
PostgreSQL17 service and fixture setup. No separate replacement harness or
new database service is needed. The major version matches the coordinator-observed
hosted PostgreSQL17.6.1.147; the community CI image is not proof of Supabase
extension/schema equivalence. Older PostgreSQL16 passes are historical only.

Locally, run only with an already-authorized, dedicated PostgreSQL17 test
runtime. `psql` must already be installed. These scripts do not install software,
start a server, create a database, drop existing data, or contact Supabase.
`generic-checkout-concurrency.mjs` requires a new empty loopback database named
`native_checkout_test`; it rejects another version, a replica, and a populated
public schema before loading fixtures. All three scripts validate target major17,
matching test database identity and non-recovery mode before any fixture writes. An SSH tunnel to production is not a
test runtime. The legacy pair use `skills_claim_test` and the setup in the
workflow, in that order.

For the existing empty generic test database, PowerShell invocation:

```powershell
$env:NATIVE_CHECKOUT_TEST_DATABASE = 'native_checkout_test'
# Optional: SKILLS_TEST_PSQL points to an already-installed psql executable.
# Optional: SKILLS_TEST_PORT is the approved local test port (default 5432).
node tests/generic-checkout-concurrency.mjs
```

All three clients reuse `helpers/local-postgres.mjs`: fixed loopback host and
host address, restricted test database names, no inherited PG service/password
files or options, noninteractive startup, and bounded connect/statement/lock
timeouts. The isolated server must support the dedicated test connection;
production credentials are never imported to make it work.

The generic race gate loads the shared `native-checkout-migration-plan.mjs`,
including all eight new checkout migrations in order. Synthetic course-key
normalization occurs before the final profile mapping. It then exercises mixed
$55/$95 seat claims, duplicate keys, final-code inventory competition, exact
cleanup boundaries and duplicate paid finalization. Assignment is not delivery.

The same migration plan is exercised by `native-checkout-profile-sql.test.mjs`
in PGlite. `local-postgres-harness.test.mjs` checks connection isolation and the
plan without opening a database connection. Those local checks establish
fixture migration loading and harness guards, not real PostgreSQL concurrency,
target schema equivalence, production migration state or operational delivery.
If the approved runtime is absent, report the race gate **not run** rather than
substituting a mock, installing a service or pointing it at a hosted project.

Full-course materialization is separately fail-closed: the edge flag
BLS_NATIVE_FULL_MATERIALIZATION_ENABLED and service-only native_full_course_policy
must both be explicitly verified/enabled; fixtures enable only their local row.
The full-course suite exercises actual SQL in PGlite, not independent-backend
concurrency. Canonical BLS duration/cleanup must match the evidenced 120+30 policy;
missing capacity/qualification or other same-course daily positions reject creation.

The seventh migration adds a disabled per-product learner-code policy and private
lease/prepare/settle transport. Local fixture tests cover actual SQL behavior;
independent sender races and provider delivery remain unproven externally.

The eighth migration reuses the existing Cloudflare Email Service envelope and
private-token recorder, then adds recipient-and-provider-ID-bound native code
history. Fixture events are synthetic; no provider/account/queue configuration
or actual delivery is verified by them. Event arrival before settlement,
replay and out-of-order/deferred evidence are tested without inventory writes.

## Non-install proof route for the current patch

Use the existing `Verify native skills reservation` GitHub Actions workflow
(`.github/workflows/verify-skills-native-claim.yml`) on a reviewed test ref
containing the complete current patch. Its `postgres:17` service and independent
`psql` clients provide the intended isolated runtime; this is not a PostgreSQL
installation on CyberPC or a new Supabase branch. Confirm repository Actions
billing/authorization before creating new paid compute; no hosted service is
provisioned by these local scripts. A run on an older commit does not prove the
current working tree.

The generic race now includes the deployed additive profile-column prerequisite
and both exact in-person Heartsaver draft identities (209809 and351632), with
TEST-ONLY native sessions and a two-seat override. Three independent claims must
produce two successes and one insufficient_seats rejection; duplicate-key replay
must retain the original order. These fixture overrides do not change production
course capacities or existing session bounds. The329495 online bundle remains
inactive and outside these plain-course races.
