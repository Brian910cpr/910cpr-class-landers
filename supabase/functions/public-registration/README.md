# Shared native checkout

One `/register/` form renders the canonical course's versioned registration
profile. `/register/skills-session/` preserves the original query and opens that
same form. New registrations use canonical public orders; prior skills receipts
resume their original saved payment adapter rather than creating another seat.

`courses.registration_profile_key` maps the canonical course key to
`landerware_registration_profiles`. The `native_public_checkout` profile's
`form_schema` declares fields, conditional acknowledgements, option groups,
catalog add-on keys, authorized public aliases, and inventory kind. It contains
no executable expressions. The server reads current catalog sellability and
validates fields/choices, then calculates the expected total. SQL independently
prices the saved order and reserves seats and code inventory in one transaction.
The immutable profile/selection snapshot preserves retries and later review.
Material configuration edits require an incremented profile version.

The initial mappings are the shared skills course and BLS initial/renewal.
The HeartCode-inclusive choice adds the verified $40 online component to the
$55 skills seat once; it never adds a second $95 charge. The two classroom BLS
choices stay $75. Bundle readiness, public availability and two-seat capacity
remain fail-closed behind verified canonical data/configuration. No instructor
renewal course, price, date policy or eligibility has been invented.

Two seats and 45 minutes apply to skills, not every course. Scheduled classes
load their actual start/end times and canonical seat state, including stricter
session/inventory capacity overrides. The form displays those values. A profile's
`max_students` is an order-size limit, not the class capacity. The server also
limits the form to currently remaining seats and rechecks at the atomic claim.
Two- and four-hour classes do not inherit the skills duration or capacity.

`/generic/form`, `/reserve`, `/status`, `/upload`, and `/checkout` share the
same controller. The opaque receipt UUID travels in `idempotency-key`; browser
storage contains capabilities only, not contact fields or document bytes.
Existing recovery links use the established private recovery token. Responses
exclude private catalog billing codes, contact fields and storage paths.
The form contains no analytics code and sets a no-referrer policy.

Uploads default disabled when no enabled requirement exists. A course can set
an enabled optional requirement (`upload_now: true`, `upload.enabled: true`),
with document type, MIME allowlist and bounded maximum bytes. Only an explicit
`required_before_registration: true` makes receipt a payment prerequisite.
Optional completion certificates may be brought to class instead. Instructor
renewal forms can use the same configured mechanism after their actual course
profile is mapped. Upload intents scope each file to one owned participant and
canonical class. A hash-derived private path plus pending-storage/received
states makes a failed Storage/SQL boundary retryable. Received evidence remains
unapproved; staff approval provenance is preserved. No public bucket policy or
client-supplied filename/path is used. Existing staff document access is reused.

Stripe Checkout receives the saved order amount, stable idempotency key and
order metadata. Returned and reused sessions must match environment, payment
mode, amount, currency and order binding. Paid state comes only from verified
Stripe evidence and the canonical finalizer. Query parameters cannot mark paid.
Every payment entry/recovery path checks required evidence. Configured courses
cannot bypass profile validation through the older `/start` API.

Verified provider payment is recorded in a separate service-only transaction
before roster/outbox finalization. A later finalization rollback cannot erase
that observation or release an already-paid reserved code. A seat hold owned
when payment is observed remains protected while the same order retries;
late payment without an existing hold still requires availability validation.
No roster, message or learner code is produced by the receipt-recording step.
The form reports payment received/confirmation pending and suppresses another
payment action until finalization succeeds. Paid observations require manual
reconciliation for cancellation/refund; they are never reclaimed as unpaid.
Refunded orders remain terminal when an older paid callback replays, including
after the old roster entry was cancelled. A different payment-intent identity
cannot be treated as an idempotent replay by either persistence boundary.

Stripe requires at least 30 minutes between session creation and expiration:
https://docs.stripe.com/api/checkout/sessions/create#expires_at
The stable provider deadline is 31 minutes after the immutable SQL hold deadline,
so an upload delay does not invalidate Checkout creation. The SQL seat hold stays
30 minutes. Any late paid event must revalidate capacity and code ownership;
conflicts go to payment review rather than an oversold confirmed registration.

Local release prerequisites are the ordered new migrations, configured private
storage, aligned public-registration/webhook Stripe account and secrets, and the
explicit public endpoint JWT setting in `supabase/config.toml`. Deploy backend
and verify contracts before publishing form/selector assets. Preserve the
existing default-off BLS activation and fulfillment/delivery configuration until
verified. Paid code assignment is not proof of actual learner delivery. Configured qualifying paid types may automatically send their assigned code through the private default-off learner-code bridge.

Run the focused tests and independent-connection PostgreSQL gate in
`.github/workflows/verify-skills-native-claim.yml`. The local PGlite suites prove
SQL behavior in fixtures; they do not prove independent PostgreSQL concurrency.
`tests/generic-checkout-concurrency.mjs` requires a fresh localhost database and
synthetic, nonredeemable codes. Browser QA, real hosted payment/webhook behavior,
staff document retrieval, code fulfillment and confirmation delivery are separate
operational release gates. Never infer those from local mocks.

## Prepared sender connection

`worker/checkout-confirmation.mjs` and its template/config reuse the checkout
owner's prepared bridge at `25cac536a19f9aba5b280de2d17efea480078fd2`.
Both the Worker (`CHECKOUT_DELIVERY_ENABLED`) and database delivery configuration
start disabled. The local Wrangler configuration has no cron or queue consumer;
no sender, token or schedule is activated by this patch. Existing sender identity
and binding names were retained, not verified or provisioned by the local tests.

Fresh database delivery defaults include physical course `509474` alongside
`209806`, `359474`, and `210549`. Existing explicit `course_ids` rows are never
rewritten or enabled. An already-present factory row therefore needs a reviewed
scope decision before activation; there is no automatic expansion of live mail.

The bridge polls the existing private-token lease RPC, renders canonical class
data and settles only with a provider receipt. Explicit pre-send rejections can
retry through the bounded SQL lease policy. An unknown send result or failed
acceptance commit is not resent automatically. Its result reports `accepted`
and `actualDeliveryConfirmed: false`; the database's legacy `sent` state denotes
provider acceptance. Actual delivery needs separate lifecycle event evidence.
Cloudflare's binding contract is documented at
https://developers.cloudflare.com/email-service/configuration/send-bindings/.

Reminders require an explicit separate flag and their existing migration;
delivery-event ingestion likewise requires its separately reviewed RPC/queue
configuration. Those capabilities are not enabled here. The confirmation bridge does not itself include a learner code. The separate
learner-code dispatcher uses private token/lease RPCs from
20261109130000_native_learner_code_delivery.sql. It is authorized for qualifying
paid types without additional manual verification, but defaults OFF in both the
Worker (CHECKOUT_CODE_DELIVERY_ENABLED) and per-product/course policy. The known
mapping is purchased aha_heartcode_bls_online -> assigned product
aha-25-3553-heartcode-bls-online on physical509474 (legacy210549 supported only
with matching assigned purchase). Plain skills/no-code options never qualify.
Other digital products need their exact authoritative course/product mapping;
there is no blanket auto-release of every inventory item.

Claim returns no code. Preparation revalidates financial evidence, ownership,
canonical learner recipient and registration/class terminal states, then marks
possible exposure and returns the code once to the private sender. Known
pre-send rejection may retry the same owned unit with a new lease; ambiguous or
lost results stop for operational recovery. Provider acceptance is recorded
without marking actual delivery/activation or inventory fulfillment complete.
Cancellation/refund before preparation blocks disclosure; a change after an
external send has started cannot recall mail, and settlement preserves the
terminal state/receipt rather than resurrecting the order. Never log RPC code
responses or expose them through public forms, health or receipts.

Actual learner delivery, observer configuration and hosted sender proof remain
separate operational gates. Uploaded evidence is never automatically approved.


## Code delivery event evidence

20261109140000_native_code_delivery_events.sql reuses the existing checkout-owner
Cloudflare Email Service event envelope: cf.email.sending.message.delivered,
deferred, bounced, failed, rejected and complained. Existing worker.queue
already forwards those opaque events to the private-token recorder. The fixed
source domain/account/zone policy comes from the reviewed local event source;
its hosted subscription and binding are not verified or enabled here.

native_code_delivery_history joins exact normalized provider receipt ID AND
canonical delivery recipient, including an event that arrived before local
acceptance settlement. Duplicate event IDs are inert; deferred/older events do
not supersede later definitive evidence, and complaints retain priority as in
the existing message-history contract. This is read-only delivery evidence:
no inventory fulfillment, order/registration revival or resend occurs. Staff
attention distinguishes provider-confirmed recipient delivery, temporary
closure/deferment, failure/complaint and stopped eligibility. A delivered email
is not proof of code activation or course completion. Missing event identity
cannot be guessed from a recipient alone, and sending/queue activation stay OFF.
