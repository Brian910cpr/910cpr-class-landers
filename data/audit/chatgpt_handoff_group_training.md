# ChatGPT Handoff: 910CPR Group Training Experience

## Primary audit/report

# Group Training Competitive Analysis

| CPR-Professionals behavior | Current 910CPR behavior | Opportunity | Implemented 910CPR solution |
|---|---|---|---|
| Opens with a plain promise that training comes to the buyer's facility. | Opened with broad program language and a BLS-first CTA. | Confirm the service before asking the buyer to understand course names. | New independent-search hero: on-site staff training, Wilmington/coastal NC positioning, and immediate request/email/text/call actions. |
| Answers minimum size, equipment, geography, timing, certification, and pricing questions before contact. | Exposed course tabs but few operational answers on the landing page. | Reduce the office manager's need to call just to understand the service. | Added at-a-glance answers, a four-step process, and eight group-specific FAQs without inventing unknown limits or prices. |
| Repeats a clear quote CTA and makes human contact visible. | Routed to a detailed request page, but its form posted to `#`; phone was mostly confined to the header. | Preserve the structured request flow while making it actually actionable. | Request form now opens a populated email to `info@910cpr.com`; email, SMS, phone, and individual-seat routes are visible on both pages. |
| Uses course, industry, FAQ, and service-area language throughout the site. | Had strong course hubs, sitemap inclusion, canonicals, and scheduling pages, but sparse group/local intent copy. | Add relevant local intent while retaining live scheduling infrastructure. | Updated title/description/headings, added workplace/healthcare/school language, Wilmington/coastal NC coverage, internal course routes, and Service + FAQ JSON-LD. |
| Uses a simple contact/quote funnel. | 910CPR already has Enrollware inventory, program-specific landers, real availability, and direct individual booking. | Do not imitate a simpler funnel at the expense of LanderWare. | Group flow remains request-based while public-course links and existing inventory/scheduling scripts remain unchanged. |

## Important source/config/test paths

- `data/config/slug_hubs.json` — group-training metadata and course mappings.
- `scripts/build_slug_hubs.py` — group landing content, FAQ/Service schema, and preserved hub rendering.
- `scripts/build_request_group_session.py` — request program choices and populated email handoff.
- `docs/css/lander.css` — responsive group landing/request styles.
- `tests/test_public_semantic_routes.py` — group route, contact, schema, and buyer-answer assertions.
- `docs/group-training.html` and `docs/request_group_session.html` — final rendered artifacts.

## Commands and results that matter

- `python -m py_compile scripts/build_slug_hubs.py scripts/build_request_group_session.py` — passed.
- Four focused `PublicSemanticRouteTests` for group routes, request context, buyer answers, and generated primary links — 4 passed.
- `python -m scripts.audit_global_page_requirements` — passed; 758 eligible pages, 1 documented exclusion, 0 violations.
- `python -m scripts.audit_internal_missing_links` — 741 public files and 28,305 links/buttons scanned; 0 broken, 1 suspicious, 4 low-confidence review items.
- HTML parser check — one H1, one viewport, and GTM present on each changed page.
- Group JSON-LD parse — passed.
- `git diff --check` — passed (line-ending conversion warnings only).

## Known unrelated test drift

The combined semantic/CSS suite also ran and exposed three existing failures outside this change:

- 127 IDs in `docs/public_schedule.json` currently lack matching files under `docs/classes/`.
- `docs/index.html` and `scripts/build_index_and_sitemap.py` reference `/css/lander.css?v=20260719-home-authority`, while two older stylesheet tests require the unversioned path.

These were not repaired because doing so would require an unrelated inventory rebuild/homepage change.

## Browser/layout validation limitation

The in-app browser security policy blocked local `file://` navigation. No policy bypass was attempted. Responsive behavior was checked statically against the 980px and 700px CSS breakpoints, DOM structure, single-column mobile rules, full-width mobile CTAs, HTML parsing, and link audits. Production visual verification remains required after deployment.

## Changed files

- `data/audit/group_training_competitive_analysis.md`
- `data/audit/chatgpt_handoff_group_training.md`
- `data/config/slug_hubs.json`
- `docs/css/lander.css`
- `docs/group-training.html`
- `docs/request_group_session.html`
- `scripts/build_request_group_session.py`
- `scripts/build_slug_hubs.py`
- `tests/test_public_semantic_routes.py`

## Open questions/assumptions

- Email composition is used because no verified server-side lead endpoint exists in the repository.
- Existing prices on the request page were preserved; no new pricing claims were invented.
- Deployment, merge, and live HTML/CSS verification are intentionally not part of this local review commit.
