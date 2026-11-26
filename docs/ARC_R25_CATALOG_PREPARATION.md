# ARC r.25 catalog preparation — issue #360

This extends data/config/course_catalog.json, not a second catalog. Existing eight blended identities and six skills identities are reused, including legacy Enrollware IDs 372258, 410694 and 248287. External IDs remain provenance, not new booking targets.

The incumbent model separates course, occurrence, registration and fulfillment. Here customer_product supplies a search/display identity on the existing canonical course; commercial_choices references exact fulfillment SKU and cost fields. Source names and January 1, 2027 effective date are explicit. Pricing is computed with decimal arithmetic by scripts/arc_catalog_pricing.py: $55 service + source cost * 1.08, fee rounded half-up to cents. This offline projection is not wired to public checkout. It moves native product/pricing representation toward Enrollware independence without claiming registration/fulfillment replacement.

## Reconciliation and blockers

- 372258: reused Adult CPR/AED blended, SKU AP-HSSSFA511-BL-r.25.
- 410694: reused Adult and Pediatric FA/CPR/AED blended, SKU AP-HSSSFA516-BL-r.25.
- 248287: reused BLS blended, SKU AP-HSSBLS101-BL-r.25.
- 369209: legacy classroom Adult and Pediatric FA/CPR/AED; no verified r.25 equivalence. Retained unchanged, including legacy qualification/capacity; not used for these commercial choices.
- 444919: legacy BLS Challenge; no verified blended/skills equivalence. Retained unchanged.
- 248288: legacy classroom BLS; no verified blended/skills equivalence. Retained unchanged.
- Pediatric CPR/AED remains a valid customer product. No separate skills SKU was supplied; routing it to a broader product would require confirmed fulfillment authorization. Skills-only quote BLOCKED with null total, never a guessed $55 total.
- BLS has no skills-only SKU/cost in the supplied block. Skills-only quote likewise BLOCKED pending exact fulfillment/fee policy.
- Product source is the owner transcription in #360 and preexisting catalog, not independent inspection of the full price-list attachment. Exact names/SKUs/costs must be checked against that document before activation.

## Release boundary

Evidence BUILT only. Session families retain four seats per session and r.25 instructor requirements as already represented; no instructor credential is invented. #359 draft PR #403 still needs complete paid-seat/hold projection, atomic final-seat concurrency proof and #342 composed shadow regressions. No scheduler integration or production mutation in this change. #372 remains draft/unmerged/undeployed. No generated page changes staged. No public SEO page or checkout proof claimed.

Before activation, resolve missing fulfillment mappings, verify current instructor qualifications and price-list effective date, compose #403 shadow validation, then separately authorize customer-facing integration. No ongoing process or monitor was introduced; production end-to-end proof and observer health remain unestablished for these choices.

Validation: python -B -m unittest tests.test_arc_catalog_pricing -v (5 passed); ast.parse on both Python files; exact JSON comparison proves all non-ARC rows unchanged and all existing IDs/capacities preserved; git diff --check passed. No broad generator executed.
