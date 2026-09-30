# BLS Initial offer materialization

## Operational result

A real public BLS Initial offer at the Shipyard can now be accepted without a pre-existing LanderWare `class_sessions` row. The public registration edge function reads the authoritative schedule payload, passes the trusted offer facts to the checkout RPC, and the RPC atomically materializes one LanderWare class, creates the temporary seat hold, and returns Stripe Checkout. Paid-order finalization remains the existing step that promotes the held student registrations.

## Scope and guardrails

- Limited to course `209806` (AHA BLS Provider), public direct booking, and a Shipyard offer.
- The offer must carry the matching external ID, a valid start/end window, and capacity 6.
- The database resolves the canonical BLS course, active Shipyard location, and active `brian` instructor record itself.
- A transaction advisory lock on the offer ID prevents duplicate class creation under concurrent checkout requests.
- Any other course or untrusted offer continues to require its normal existing-session behavior.

## Production application and validation

Applied directly to the linked production Supabase project because migration history is already divergent and `db push` is not safe for this repository state:

1. `20260930205856_materialize_bls_offer_sessions.sql`
2. `20260930210146_assign_bls_offer_instructor.sql`
3. `public-registration` Edge Function deployed with `--no-verify-jwt`.

Validation performed:

- `npx --yes deno check supabase/functions/public-registration/index.ts` passed.
- `python -B -m unittest tests.test_public_registration` passed: 11 tests.
- A live RPC test inside `BEGIN; ... ROLLBACK;` created the materialized session and hold successfully, then left no test record.
- A live public `POST /functions/v1/public-registration/start` for authoritative BLS offer `14501248` returned HTTP 200 with an order, a 30-minute hold, and a Stripe Checkout URL. This produced the expected live offer/session and checkout hold.

## Files to review

- `supabase/functions/public-registration/index.ts`
- `supabase/migrations/20260930205856_materialize_bls_offer_sessions.sql`
- `supabase/migrations/20260930210146_assign_bls_offer_instructor.sql`
- `docs/bls.html`
- `docs/BLS.html`
- `tests/test_public_registration.py`

## Notes

The BLS calendar route has been restored so BLS Initial seated offers open `/register/?session=<offer-id>`. BLS Renewal and HeartCode remain on Enrollware through their existing appointment URLs.
