# ChatGPT Handoff: Build Your Training Day

## Outcome

The rejected BLS-led group catalog was replaced with one corporate workflow on `docs/group-training.html`. `docs/request_group_session.html` is now a query-preserving compatibility adapter to that builder.

## Authoritative files

- `scripts/build_slug_hubs.py` — renders the group-only training-day builder while leaving other course hubs unchanged.
- `scripts/build_request_group_session.py` — renders the compatibility adapter.
- `docs/assets/group-training-builder.js` — request model, mixed-course selection, live summary, query prefill, analytics event, and populated email handoff.
- `docs/css/lander.css` — compact desktop/mobile builder layout.
- `tests/test_group_training_builder.py` — focused structural and contract tests.
- `tests/test_public_semantic_routes.py` — updated group route compatibility tests.
- `scripts/start_group_training_review.ps1` — corrected handling for repository paths containing spaces.

## Final rendered files

- `docs/group-training.html`
- `docs/request_group_session.html`

## Request contract

The browser exposes a `training_day_request_v1` structure with:

- organization name, team type, and pasted requirement
- multiple `training_items`, each with its own `training_key`, participant count, and delivery preference
- location mode and structured address fields
- timing mode, preferred windows, deadline, and operational notes
- contact information and preferred channel
- pending evaluation states for travel, instructor availability, duration, pricing, and tentative reservation

No price, duration, travel limit, availability, group maximum, course ID, or reservation promise was invented.

## Validation results

- JavaScript syntax: `node --check docs/assets/group-training-builder.js` passed.
- Python syntax: both modified generators passed `py_compile`.
- Focused tests: 10 passed.
- Global page requirements: 758 eligible pages, 0 violations.
- Sitewide link audit: 741 files, 28,282 links/buttons, 0 broken, 0 suspicious, 3 low-confidence review items.
- `git diff --check`: passed; line-ending warnings only.
- Desktop browser: one builder heading, seven peer training rows, no console warnings/errors.
- Mixed browser scenario: 12 BLS + 18 First Aid/CPR/AED + 18 Bloodborne Pathogens rendered as three independent summary lines.
- Mobile browser: seven rows span approximately 511 CSS pixels, compact row height approximately 67 pixels, no horizontal overflow, mobile summary displayed.
- Compatibility browser scenario: the legacy request URL retained `program`, `location`, and `preferred_month`, then preselected Bloodborne Pathogens and populated Wilmington/October 2026.

## Known limitations

- Email remains the delivery mechanism because the repository contains no verified server-side group lead endpoint.
- The page deliberately reports estimate, travel, staffing, and availability as pending review.
- No production deployment or merge was performed.
- Existing unrelated runtime/debug/cache changes remain unstaged.
