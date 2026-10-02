# Actual calendar integration — local, release blocked

Owner instruction: https://github.com/Brian910cpr/910cpr-class-landers/issues/338
Branch: `fix/calendar-open-shifts-20261002`, based on `ceb84d44cd5999e0f31bce0d9ec1aaece5a5f1e7`.

## Exact release diff

Runtime files: `docs/admin/dashboard.html`, `docs/admin/open-shift-model.js`, `docs/admin/open-shift-policy.js`.
Authoritative policy builder: `scripts/build_calendar_policy.py` (one output asset, never inventory or sessions).
Regression checks: `tests/open_shifts.test.cjs`, `tests/calendar_open_shifts_browser.py`.
Supporting evidence: this directory and root `Codex_Reply_CalendarOpenShifts20261002.md`.

The prior isolated lab remains on `lab/scheduling-laboratory-20261002`; it is not imported by runtime. Unrelated Earl and Jackson edits are excluded. Open PR #333 touches anchor ingestion/selection, which this change does not modify; #332 covers global build signatures. Recheck overlap before release. This change targets the Operations site calendar (`/admin/dashboard.html`), not the public booking selector's inventory generation or registration/payment APIs.

The old dashboard computed free gaps between 8 AM and 7 PM and merged all instructors' busy time together. The replacement derives each instructor's availability from explicit HARD/SOFT events or approved active inverse-calendar appointment-container dates. Sources and scheduled sessions must be current; the 30-minute source limit is an explicit conservative display policy tied to the workflow's nominal ten-minute cadence, not a guarantee that GitHub cron runs on time.

Real scheduled sessions and deliberate holds block time without requiring participant counts. Imported start=end intervals use existing explicit source metadata or course-consumption rules; unresolved intervals suppress openings, including unresolved prior-night sources. Cancelled sessions/events are excluded; closed/full real classes still block. Unclassified personal Google events do not indiscriminately become work commitments. Instructor/location identity and source IDs are retained in `window.lastOpenShiftReport`.

Real classes form same-instructor/location contiguous blocks. Intervening commitments prevent cleanup merging. Every edge considers configured short-skills variants in BLS HeartCode, Heartsaver, ARC and HSI before rejection; no ACLS/PALS, no once-per-day skills rule, no planted-day scatter. Genuine free windows display hourly starts, tight windows half-hour starts. Next-day real blockers and travel constrain cross-midnight consumption; midnight itself is not a blocker. Room aliases are conservatively normalized to shared venue occupancy, so cross-instructor room allocation needs confirmation before fine-grained sharing.

The dashboard's month badge and day list share the validated results. Existing published feed starts are shown only when validated or matching an identifiable real session. New suggestions are explicitly **not published** and contain no manufactured booking links. Customer booking feeds, schedule JSON contracts, existing registrations, instructor data and production services are not modified. Source-policy hashes and asset version can be copied with the new diagnostics button.

## Timing blocker and required source decision

Heartsaver `209808`, `329495`, `251545` each map to the same blended/online course identity across selector config/catalog/master. Catalog/master say 45-minute classroom/skills/display time. Consumption rules and deployed selector feeds say 120-minute consumption/minimum reservation. The master has no confirmed scheduler consumption. Evidence does **not** establish that these are different offerings or that 120 is only a stale error. All affected candidates are visible in diagnostics with `unresolved_course_duration` and `outside_short_skills_rule`; the calendar does not silently choose 45, 60 or a certification equivalence.

Owner/source decision needed: is 120 minutes a required instructor reservation around 45-minute teaching, or should the reservation rule be corrected to an authoritative short-skills duration? Specify by course ID, including setup/cleanup. Only then update the authoritative rule and rebuild this single code asset. HSI `445670` catalog setup/cleanup (15/30) also differs from the operational 45-minute rule; current operational rule is retained with the limitation recorded. Configured instructor groups are the current eligibility evidence, not proof of credential expiration. Unknown offsite travel uses the existing Brian 90-minute rule; non-Brian unknown travel fails closed.

## Verification and source limits

`node --test tests/open_shifts.test.cjs`: 21 passed.
`node --test tests/open_shifts.test.cjs tests/canonical_session_model.test.cjs tests/schedule_reader.test.cjs`: 29 passed.
`python -B -m unittest tests.test_apply_anchor_policy tests.test_anchor_state tests.test_publish_admin_schedule tests.test_build_live_availability_snapshot`: 44 passed.
`python tests/calendar_open_shifts_browser.py`: actual CyberPC Chrome desktop/mobile rendering passed, zero page errors, chain growth and free-day assertions passed. External network requests are blocked and authentication is mocked only in the isolated test browser. This is not a production owner-login proof. Playwright and Chrome are installed on CyberPC; no new dependency was added to production.
JavaScript asset/inline-script and Python AST syntax checks passed; whitespace check passed.

Broader dashboard suites have two existing failures on both this branch and a temporary unmodified-main baseline: `dashboard_ops` expects a password input that current main makes hidden, and `dashboard_schedule` expects removed “Same-time location conflict” text. These authentication/legacy-text differences were preserved. No exhaustive repository suite or full build chain was run.

Read-only public feeds checked around 04:43 UTC on October 2: schedule generated 00:53:37 UTC with 29 sessions; availability generated 00:53:38 UTC with 175 events. Amy/Nick exported zero availability events. Last observed refresh workflow succeeded at 00:56 UTC; a successful run is not current-source health. `source-review.json` records those observations.

`local-source-audit.json` distinguishes CURRENT checks (zero proven openings from stale feeds) from a frozen-source replay (structural simulation five minutes after source timestamp). At the frozen reference, October 2/3/5/12 produced 12/12/15/12 candidates and 0/3/9/5 accepted display suggestions respectively, after real classes/blocks/travel/lead/duration constraints. These are not newly published offers or proof of current availability. Inputs: 29 sessions and 175 calendar events; counts/reasons/diagnostics retained per date. Screenshots use synthetic noon occupancy only and contain no real participants.

## Release plan — not executed

1. Resolve Heartsaver timing semantics from owner/source evidence; confirm credential, buffer and shared-resource assumptions as needed. Do not bypass real conflicts to increase displayed counts.
2. Recheck remote main and concurrent PR #333/#332 plus local modifications. Apply only the bounded intended diff; preserve Earl/Jackson and other work. Rebuild policy with `python -B -m scripts.build_calendar_policy` (exactly one asset).
3. Rerun focused/browser and relevant existing tests. Address any new failures; record the two proven baseline failures distinctly.
4. With existing release approval, push only the repair branch, open/merge the narrow PR after repository checks, and wait for production GitHub Pages deployment. Do not merge or deploy the separate lab branch.
5. Run the already-authorized calendar refresh only after timing rules are settled. Verify schedule/availability source timestamps and source export states, rendered live calendar dates/overnight examples, and every versioned changed JS asset. Preserve paid sessions and registration/payment state.
6. Report BUILT/CONNECTED/PROVEN/MONITORED/HEALTHY according to actual evidence. Present state is BUILT with local browser/fixture validation, BLOCKED for release. The browser detects stale sources on load, but there is no independent observer-health proof; Brian is not claimed to be relieved of monitoring burden. No live end-to-end or production health proof exists.
