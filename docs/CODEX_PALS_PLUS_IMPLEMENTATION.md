# PALS Plus integration — implement now

A public SEO sales page is already committed at `/docs/courses/pals-plus.html`.

Complete the PALS-family integration without creating a second scheduling species.

## Product/business rules
- Product: AHA PALS Plus® complete package.
- Public price: $385 total. Do NOT break out the AHA online component or 910CPR skills-session price to customers.
- 910CPR absorbs sales tax; do not add tax above the advertised $385.
- Internal wholesale reference only: PALS Plus product #25-1476, reseller cost $256.50 from Cardio Partners/Stephen Weiss (10% reseller discount).
- Instructor economics: Amy receives the existing HeartCode PALS skills rate, $50/student. This is internal only.
- Scheduling: PALS Plus occupies the SAME calendar space and compatibility rules as AHA HeartCode PALS skills. It must be able to share a compatible skills-session slot with ordinary HeartCode PALS. Do not create dedicated PALS Plus anchors or duplicate calendar capacity.
- Credential/sales proposition: advanced pediatric education developed by AHA/AAP; successful completion carries the PALS Plus designation on the AHA PALS Provider eCard. Use AHA terminology `designation`, not `endorsement`.

## PALS family calendar page
Update the durable source/generator that produces `docs/PALS.html`, not only the generated HTML, then rebuild generated output.

Add a visible fourth PALS-family tile/card for **PALS Plus® Complete**:
- price: `$385.00`
- delivery badge: `ONLINE + SKILLS`
- concise copy: `Advanced PALS Plus online learning + hands-on PALS skills session. Includes the PALS Plus designation pathway.`
- image: use an appropriate existing PALS/HeartCode image unless a PALS Plus asset already exists in the repo.
- deep-link aliases: `pals-plus`, `palsplus`, `plus`
- `full_course_page`: `/courses/pals-plus.html`
- scheduling/availability must resolve through the same eligible time inventory as HeartCode PALS course 209812. Do not invent an Enrollware course ID if one does not exist. Use a product/variant alias layer or mapped availability as appropriate.

The tile should make it obvious that $385 is the complete package, while HeartCode PALS `$100` remains the skills-session-only option for students who already bought/completed their online course.

## “See details” behavior
The user explicitly wants the various `See details...` buttons/links to lead to real SEO course pages. In the PALS-family selector, add/repair a clear `See details` link for each course option using its `details.full_course_page`, without making the details link accidentally select/register the course.

For PALS Plus, `See details` must go to `/courses/pals-plus.html`.

Verify the existing PALS Provider and Renewal detail-page paths. If dedicated pages exist, point their `full_course_page` values there instead of looping back to `/pals.html`. HeartCode PALS should remain `/courses/heartcode-pals.html`.

## SEO/discovery
- Add `/courses/pals-plus.html` to sitemap/discovery sources used by the site.
- Add internal links from relevant PALS detail pages where appropriate, especially HeartCode PALS, with natural anchor text such as `PALS Plus` or `advanced PALS option`.
- Preserve canonical URL and structured Course + FAQ data on the new page.
- Do not claim PALS Plus is a separate AHA certification. Describe it as the PALS Plus designation on the PALS Provider eCard.

## Verification
Run the repo's normal build/tests. Verify:
1. `/courses/pals-plus.html` is reachable.
2. PALS family shows PALS Provider, PALS Renewal, HeartCode PALS skills-only, and PALS Plus Complete.
3. PALS Plus shows `$385.00`.
4. PALS Plus calendar availability mirrors compatible HeartCode PALS skills availability without double-booking capacity.
5. `See details` links work for all PALS-family options.
6. PALS Plus registration flows through LanderWare's current registration architecture and does not expose wholesale cost or internal instructor pay.
7. No sales tax is added above the advertised $385 package price.

Commit the implementation and leave a concise verification note in the repo.