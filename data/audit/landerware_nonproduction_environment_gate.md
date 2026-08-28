# LanderWare non-production environment gate

Status: **BLOCKED BEFORE ENVIRONMENT CREATION — production untouched**

Checked: 2026-08-28 EDT

## Environment discovery

- Supabase organization: `910CPR` (`kukukymsnhicxzwsvxgo`)
- Active project: `LanderWare` (`wktwgcnwdvbebcobgyey`)
- The active project is the production project referenced by public application URLs and was used only for read-only environment inventory.
- Existing Supabase development branches: none
- Other project: `ShiftCommander` (`cskcgwjvgsgawxwncjrf`), inactive and unrelated; it is not an acceptable staging substitute.
- Latest migration visible on production: `20260827151830_add_maxim_invoice_assignments`
- Unified registration migration `20260827220000_landerware_unified_registration` is not applied to production.
- `landerware-registration` is not deployed in production. No production mutation or deployment was attempted.

## Safest minimal path

Create an ephemeral Supabase development branch from `LanderWare`, then apply migration `20260827220000_landerware_unified_registration`, deploy only the branch copy of `landerware-registration`, execute the disposable `nhcso-foundations-instructor-led-v1` trace, collect evidence, and delete the branch after review/approval.

Supabase reports the development-branch cost as **$0.01344 per hour**. Supabase requires explicit cost confirmation before branch creation. That confirmation is the current blocker.

After approval, the branch must receive any function secret configuration needed by the Edge Function, without copying unrelated production secrets. Production will remain untouched.

## Existing rendered-page assertions

### `test_public_pages_and_generator_use_the_same_shared_projection`

- Expected: rendered `docs/bls.html` includes `ResolvedSelectorAvailability.filterDatesByCourse`, proving the public page consumes the shared availability projection.
- Actual: the marker is absent from the rendered page.
- Predates lifecycle commit: the marker is also absent at parent commit `0a294cceed92ceb0852bf33f2a4f050d9874f23d`; `docs/bls.html` was last changed by `e20c702eb8353fe3c3a2da86505f499efe2326cf`, before `77f6c1428327ae31e927986443be3e0533d2e0e6`.
- Production risk: unrelated to durable registration persistence, but it may allow generated public availability behavior to drift from the shared selector projection. It is a pre-existing public scheduling consistency risk and should not be represented as passing.

### `test_self_service_is_token_scoped_and_enforces_requirement_and_expiration`

- Expected: rendered `docs/corp/maxim-schedule.html` explicitly filters past dates and dates after the employee requirement expiration using `if(day.date<today||day.date>ends)continue`.
- Actual: it filters dates after `person.expirationDate` but does not contain the expected lower-bound/past-date filter.
- Predates lifecycle commit: the expected condition is absent at parent commit `0a294cceed92ceb0852bf33f2a4f050d9874f23d`; the page was last changed by `4c5e4f36a83cc837e3fc6ff15e45197d4495c4eb`, before `77f6c1428327ae31e927986443be3e0533d2e0e6`.
- Production risk: unrelated to the generic registration backend, but stale availability data could present a past date in the MAXIM self-service UI. Server-side registration validation rejects dates earlier than the current Eastern date, limiting this primarily to presentation/usability rather than unauthorized durable registration.

## Current GO/NO-GO

**NO-GO** for production deployment. The environment-level trace has not run because no non-production Supabase environment exists and paid branch creation has not yet been authorized.
