# Native confirmation scheduler

The implementation is default-off. Installing its schema or deploying the route does not create a token, install an extension, schedule a job, activate customer mail, or prove delivery.

## Contract

- The fixed `/native-checkout-confirmations/scheduled` route accepts only an empty JSON object, a standard Bearer credential, and a database-generated run ID. It does not accept customer, order, recipient, URL, or message selectors.
- One queued run can start once. Each callback claims at most one canonical native message. Existing post-commit and owner callers retain their ten-message bound.
- Delivery leases, canonical rendering, provider idempotency, paid-registration gates, retry backoff, and provider receipts remain in the existing native queue.
- Unknown callback, provider, or settlement outcomes latch the scheduler for review. Repeating an exact completion receipt is allowed; repeating delivery after an unknown result is not.
- A completed database result is authoritative even if the HTTP response is lost. Queue polling, callback completion, and observer completion are separate evidence.
- The external observer is read-only. Its former retry mode is retired; it cannot compete with the database scheduler or bypass its latch.

## Activation and proof

Reviewed setup proposals are under `supabase/reviewed/native-confirmation-scheduler/`. They are not migrations and must not run automatically.

Before provisioning, verify the installed extension signatures, object ownership, effective transport/Vault privileges, gateway redirect behavior, and background-worker logging. The proposal restricts transport schema, tables, sequences, functions, and worker controls before a credential can enter the transient HTTP queue. Unexpected custom grants fail for review rather than being silently removed.

Provision jobs inactive, then prove cadence with customer delivery disabled. Require at least ten genuine consecutive callbacks at the intended one-minute cadence, zero claimed customer messages, no durable latch, and an independently running external observer. Callback and database-observer timestamps become stale after three minutes. A fresh queue poll cannot mask stale scheduler evidence. GitHub scheduled-job admission is not a minute-cadence guarantee.

Enabling customer delivery is a separate release step after canonical checkout, payment, roster attachment, confirmation, and public-path checks pass. Provider acceptance is not recipient inbox delivery.

## Local verification

- `tests/native-confirmation-scheduler-*.test.mjs`: route, role, lifecycle, security-boundary and service-budget checks.
- `tests/native-confirmation-monitor.test.mjs` and `tests/native-scheduler-observer.test.mjs`: complete health assessment and retired external retry.
- `tests/native-scheduler-concurrency.mjs`: seven deterministic two-connection PostgreSQL 17 races using synthetic transport/Vault fixtures, an empty loopback-only database, and no external calls.
- `scripts/run-local-scheduler-pg17.sh`: creates and stops a fresh local cluster from explicitly supplied PostgreSQL 17 binaries.

These tests establish local behavior only. Hosted cadence, actual transport, customer delivery, and an active external observer require separate evidence.
