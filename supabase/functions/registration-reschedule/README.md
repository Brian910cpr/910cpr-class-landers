# Registration rescheduling

`POST /context` reads the registration identified by the `x-reschedule-token` capability. `POST /confirm` rechecks the current published course calendar and atomically moves that registration. Tokens are random 256-bit capabilities, stored only as SHA-256 hashes; the student page keeps them in the URL fragment and memory. Tokens expire, can be revoked, and become idempotent receipts after confirmation.

Owner-authenticated endpoints: `lookup`, `issue`, `block`, `revoke`, `health`, `retry-confirmations`. The owner page is `/admin/reschedule.html`. Issuing a link does not send mail or move a student. Before issuing links for multiple disrupted sessions, block all those session IDs so one affected cohort is not offered another unavailable class. `deadlineAt` optionally limits the selected class start; `expiresAt` controls link validity, independently.

Same-course transfers preserve the canonical supersession history, requirements, payment order, material choice, and public-order student references. Exact duplicate imports for the same customer, course, and original start are retired in the transaction; conflicting duplicate financial/completion records require review. No new checkout is created.

The server uses the current published family calendar, then checks canonical session state, date closures, blocked sessions, capacity and active checkout holds. It matches both external session identity and Eastern start time. The first release offers published sessions that already exist in the canonical registry. It does not materialize unpublished or synthetic availability. An empty calendar has a private help-request path.

Confirmation messages are inserted in the transfer transaction and delivered through the existing `RESEND_API_KEY`. Optional `RESEND_FROM_EMAIL` overrides the established notification sender. Provider idempotency uses the durable message ID. Failed sends never roll back a successful seat move. The page accurately distinguishes saved changes from sent confirmation email. Delivery leases prevent parallel sends; ambiguous attempts beyond the provider deduplication window require review.

The confirmation workflow retries every ten minutes using the existing owner automation credential. Its HTTP failure is a failed Actions run. Health levels must be reported separately: database tests and deployment do not prove recipient delivery or an observed scheduled recovery. Verify the workflow runs, its notification/observer path, and a real recipient confirmation before calling the process monitored or healthy.

Validation: `node --test tests/reschedule.test.mjs`; `tests/reschedule-transaction.sql` inside `BEGIN`/`ROLLBACK` as `service_role`; `node tests/reschedule-browser.mjs` requires Playwright and Chromium. Never run the SQL fixture outside a rollback transaction. Rollback: revoke issued links, remove the public page, disable the confirmation workflow; retain all supersession/audit/financial history.
