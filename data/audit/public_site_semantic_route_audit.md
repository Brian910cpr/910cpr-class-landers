# Public Site Semantic Route Audit

Generated: `2026-07-11T10:07:40.790695-04:00`

## Summary

- Pages crawled: 153
- Links checked: 1728

## Before / After Counts

- group_flow_defects: `5` -> `0`
- wrong_family_routes: `1` -> `0`
- unnecessary_selectors: `0` -> `0`
- self_loops: `4` -> `0`
- technically_broken_links: `28` -> `0`
- semantically_wrong_links: `10` -> `0`

## Repairs Applied

- Group-training tab routes now use /request_group_session.html?request_type=group instead of individual public course pages.
- BLS tab schedule routes now use /bls-schedule.html.
- Heartsaver tab schedule routes now use /heartsaver-schedule.html.
- HSI BLS + First Aid no longer routes to a BLS-family combo page.
- USCG tab route now uses the existing USCG selector page.
- Class landers regenerated so ACLS/PALS Book This Class links resolve.
- Generated class landers now define the ForwardToEnrollware fragment target used by Book This Class links.
- Legacy docs/courses/bls.html and docs/courses/acls.html now redirect/canonicalize to current hubs instead of stale Class Report tables.

## Remaining Finding Counts

- `repaired semantic route`: 6
- `valid fragment`: 124
- `valid internal`: 778
- `valid registration`: 426

## Notes

- `valid internal` means same-site navigation whose target exists and matches the promised user intent.
- `valid external` means non-registration external links that are intentional.
- `valid registration` means direct registration/Enrollware destinations.
- `valid fragment` means same-page or same-site fragment destinations that exist, including the generated class-forwarding target.
- `repaired semantic route` means a route corrected by this work order and now semantically valid.
- `intentionally indirect` is reserved for routes where an intermediate page is deliberate; none are currently required.
- `unresolved finding` count is zero.
- Selectors were retained for BLS, ACLS, PALS, and Heartsaver because each has multiple meaningful course/delivery choices.
- No normal navigation points to a generic error page.
