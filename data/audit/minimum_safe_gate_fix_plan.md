# Minimum Safe Gate Fix Plan

1. Keep existing Class Report rows rendering when they have `/enroll?id=` URLs and reviewed page/card mapping.
2. Apply Course Master gates only to generated public rows: appointment seeds, dynamic offers, and request-only rows.
3. Suppress appointment seeds unless `appointment_seed_allowed=true` or an explicit reviewed exception exists.
4. Suppress dynamic offers unless `dynamic_offer_allowed=true`.
5. Block generated rows when `review_needed_for_scheduling=true` or `course_key` is `UNKNOWN`.
6. Preserve the stacked renderer; do not replace it.
7. Make August visibility explicit by creating/verifying real Enrollware rows before relying on generated seeds.
