# Skills reservation, payment, and optional completion certificate

These routes preserve previously saved skills receipts. New registrations use
the shared course-driven form and `reserve_native_checkout_order`, which calls
canonical atomic public-order creation. See `../public-registration/README.md`.
The skills rules still enforce two shared seats, instructor eligibility,
occupied intervals, cleanup, closures, and identity idempotency. Payment and
document steps never create another attendee or session.

All routes are POST with the existing public Supabase authorization headers.
`choices` and `reserve` retain their existing contracts. The following routes
require `context` plus the original UUID in the `idempotency-key` header:

- `payment-status`: checks the saved receipt and its bound Stripe session. It
  never creates a Checkout Session. Only verified paid evidence records payment.
- `checkout`: reuses or creates one hosted Stripe Checkout Session for the
  durable order. Server price, currency, registration, order metadata, and session
  binding are checked. No browser-supplied price or return URL is accepted.
- `certificate`: accepts an optional `{certificate:{type,base64}}` object for a
  PDF, JPEG, or PNG up to 2 MiB. MIME signatures and actual byte size are checked.
  There is no requirement to call this route before reserving or paying.

The random receipt key is a bearer capability. The browser keeps it in
sessionStorage and sends it only in a header, never a URL. Contact details are
not persisted in browser storage. Losing a response or returning from Stripe
resumes the original receipt before querying calendar availability.

Uploads reuse the existing private `class-session-docs` bucket and
`class_session_documents` records, with a server-derived class/registration/hash
path. No original client filename, storage URL, or registration UUID is trusted.
Instructors use the existing authenticated workbench and short-lived document
links. Upload is evidence for instructor review, not an automatic completion or
eligibility decision. Bringing the certificate to class remains an alternative.

`STRIPE_SECRET_KEY` must belong to the account delivering events to the existing
`stripe-registration-webhook`. The webhook routes by canonical skills receipt
before generic payment mutations. Signed completed/async-success events must be
paid and match the bound session, $55 amount, and USD currency. Failed/expired
events cannot downgrade an already-paid order. Return query parameters never
prove payment. An expired or uncertain checkout older than the provider's safe
idempotency window requires reconciliation; it cannot silently create a second
charge attempt. Leaving Stripe does not cancel the existing date reservation.

Release order: apply the new service-only migration; deploy the webhook and
skills endpoint with existing JWT settings; then publish the form and versioned
client asset. No new public database/table/storage policy is required. Recheck
the private bucket and existing instructor document access before activation.
Hosted checkout, real webhook delivery, and staff document viewing require
separate operational verification; local mocks are not live proof.

Focused checks: `tests/skills-checkout*.test.mjs`, the existing native skills
handler/adapter/SQL tests, and selector/refresh tests in
`.github/workflows/verify-skills-native-claim.yml`. SQL tests use a disposable
PGlite database. Real multi-client PostgreSQL reservation concurrency is a
separate existing CI gate and must not be inferred from PGlite.
