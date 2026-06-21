# Live Availability Recheck Plan

This is a read-only plan for the next scheduler phase. It does not modify public pages, call Enrollware, create appointments, change appointment URLs, enable Worker creation, or publish buttons.

## Current Proof

A deterministic appointment URL successfully opened the intended Enrollware enrollment page for:

- `appointmentDayId=260671`
- `startTime=8:30 AM`
- `courseId=209806`

That proves the deterministic URL pattern can reach the expected Enrollware enrollment surface. It does not prove the slot should be public without live availability and occupancy rechecks.

## Availability Sources

### Brian Inverse Availability Calendar

Brian's calendar should be treated as inverse availability: open time is potentially available unless a blocking event says otherwise. The solver must still apply course duration, instructor qualification, room/location availability, DNS blocks, personal blocks, employment/ADR blocks, and existing occupancy.

### Amy Actual Availability Calendar

Amy's calendar should be treated as explicit availability: only declared available windows can become candidate seeds. If Amy's advanced classes are only available before the configured 13:00 rule, the current policy correctly hides those seeds.

### DNS / Do Not Schedule Markers

DNS markers are hard blocks. Any seed overlapping DNS should be hidden at page-load refresh and rejected at click-time recheck.

### ADR / Employment Blocks

ADR or employment blocks are hard blocks unless Brian explicitly models an exception. They should consume instructor time before public offers are shown.

### Personal Calendar Blocks

Personal calendar blocks should prevent display and redirect. If personal calendar access is stale or unavailable, fail closed for click-time redirect.

### Existing Enrollware Occupancy

Enrollware remains the roster/enrollment endpoint. Existing Enrollware classes or appointments should block conflicting public seeds. If live Enrollware occupancy is unavailable, use the freshest local snapshot at build time but require click-time recheck before redirect.

## Stale-Page Risk

Static pages can become stale after build. A seed that was valid at build time can become invalid when:

- Brian or Amy adds a calendar block.
- DNS/employment/personal blocks appear.
- Enrollware occupancy changes.
- A seed remains technically URL-valid but is no longer desirable under current policy.

The public UI must not assume static build output is final truth.

## Safest Architecture

### 1. Build-Time Preview

Build-time preview should remain static and read-only. It can prebuild:

- Course catalog facts.
- People/instructor policy.
- Appointment container ranges.
- Candidate offers from local snapshots.
- Schedule seeds.
- Deterministic appointment URL previews.
- Audit reports.

Build-time preview must not publish appointment buttons without a live recheck layer.

### 2. Page-Load Refresh

When a customer loads a schedule page, a lightweight endpoint should refresh the seed list against recent availability snapshots. This endpoint should return displayable options only, not create anything.

It should check:

- Calendar snapshot age.
- Brian inverse blocks.
- Amy explicit availability.
- DNS blocks.
- ADR/employment blocks.
- Personal blocks.
- Known Enrollware occupancy snapshot freshness.
- Seed policy still allowing the course/time.

If the refresh endpoint is unavailable, the page should either hide dynamic appointment buttons or show a conservative contact/help state.

### 3. Click-Time Recheck

Click-time recheck is the final gate before redirecting to Enrollware. It must revalidate:

- Seed still exists and is policy-allowed.
- Instructor is still eligible.
- Course is still appointment-allowed.
- Appointment container still owns the computed appointmentDayId.
- Calendar availability still allows the full course duration.
- No DNS, ADR/employment, personal, or occupancy conflict exists.
- The slot is still desirable, not just technically URL-valid.

Only after this passes should the system redirect to the deterministic Enrollware URL.

### 4. Fallback Message If Unavailable

If recheck fails, do not redirect. Show:

> That class time is no longer available. Please choose another option or contact 910CPR and we can help find the right class.

The system should log the internal reason with `seed_id`, `source_offer_id`, `course_id`, `appointmentDayId`, `startTime`, and the recheck failure code.

## If A Seed Is No Longer Valid

Hide it on refresh. If a customer clicked it before refresh completed, fail closed at click-time and show the fallback message.

## If A URL Is Valid But The Slot Is No Longer Desirable

A valid Enrollware URL is not enough. If policy says the slot should no longer be offered, do not redirect. Log the policy reason and suggest alternate times.

## Static vs Live

### Can Be Prebuilt Statically

- Course catalog.
- People catalog and assignment policy.
- Appointment container ranges.
- Deterministic appointmentDayId math.
- Candidate offer previews.
- Seed previews.
- URL previews.
- Brian review reports.

### Must Be Checked Live Or Near-Live

- Brian calendar blocks.
- Amy availability windows.
- DNS markers.
- ADR/employment blocks.
- Personal calendar blocks.
- Existing Enrollware occupancy.
- Snapshot freshness.
- Click-time redirect eligibility.

## Next Implementation Step

Build a read-only recheck prototype that accepts a `seed_id`, loads the latest local/calendar snapshots, and returns one of:

- `available_for_redirect`
- `unavailable_calendar_block`
- `unavailable_occupancy_conflict`
- `unavailable_policy_rejected`
- `unknown_stale_snapshot`

Do this before exposing any public appointment button.
