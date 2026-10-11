# Issue 334 — native class-page repair, round 2

- Assignment: GitHub #334, native metadata/registration follow-up; original strict-link round already accepted before this dispatch.
- Timestamp: 2026-10-11 02:56 UTC (2026-10-10 22:56 EDT).
- Branch: codex/issue334-native-metadata-20261011.
- Substantive commits: 548139d242ef73c89d5114239ee4fbae4353b257; 32c1bb19785252708579df63b6a16774616cd5f2.
- State: VERIFIED native page repair; overall #334 remains OPEN/BLOCKED on cloud-independent recovery and observer proof.
- PRs: https://github.com/Brian910cpr/910cpr-class-landers/pull/377 and https://github.com/Brian910cpr/910cpr-class-landers/pull/378 (both merged).
- Merge commits: b12bff85d36f1a770179654cf68fb48b0c6ded32; e73c4b7aedcfefc87867259eeaead169e2c9a027.

## Findings and changes

Full #334 body/comments, current AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design ethos and proof standard were read. Execution acknowledged before implementation at https://github.com/Brian910cpr/910cpr-class-landers/issues/334#issuecomment-6104745559 . Owner comments were used as authority; no third-party authorization was inferred.

The existing native candidate gate admitted the canonical occurrence, but lifecycle recognition accepted only Enrollware URLs. Flat native records also bypassed course-map normalization. The repair resolves presentation from the existing active course_map entry by course ID/number, without guessing from names, prices or duration. Native scheduled CTA recognition reuses native candidate checks and additionally requires current canonical demand, public location, active known course and the exact canonical LanderWare URL. The follow-up explicitly rejects substituting a syntactically valid legacy Enrollware URL into a native record. Existing cancelled/rescheduled/full/completed and unknown/stale gates remain in force. Native SEO/Event schema eligibility policy was not broadened.

This repairs the customer surface for canonical native Sessions and moves toward Enrollware independence without introducing a second catalog, new Session, Registration, or payment operation. Incumbent course identity and lifecycle separation remain intact; only the native presentation path was repaired.

## Exact intentional changed files

- scripts/build_landers.py
- tests/test_native_lander_metadata.py
- docs/classes/lw-b48b53c7-df11-409f-a8f0-61b72a7f17e9.html
- docs/classes/lw-eb020e4a-b74a-443e-acd8-05727c2a8170.html
- Codex_Reply_Issue334_NativeAnchor_R2.md (this receipt)

## Local validation and bounded generation

Command: python -B -m unittest tests.test_native_lander_metadata tests.test_public_session_landers tests.test_native_public_anchor tests.test_canonical_scheduling_demand tests.test_validate_sitewide_links_strict tests.test_stale_class_link_fallbacks tests.test_course_booking_links

Result: Ran 32 tests; OK. Includes complete two-fixture HTML rendering, known/inactive/unknown course mapping, private location, stale demand/workspace, missing count, wrong backend/source/URL/identity, closed/cancelled/rescheduled/completed lifecycle, native anchor/barnacle compatibility, and strict missing-target rejection. The strict audit fixture intentionally prints FAIL-CLOSED for its one broken target; that is a passing negative test, not a production failure.

Syntax: python -m py_compile passed initially; final ast.parse validation passed for both Python files without new bytecode. git diff --cached --check passed before commits. Targeted audit of the two actual regenerated HTML files: 35 links, all OK, zero BROKEN/SUSPICIOUS. No application test failures observed.

Input: docs/data/schedule_future.json at branch base 649ba485e3005ce374466269a678128fb9f841a2, plus existing data/config/course_map.json. No inventory inputs edited. Targeted builder invocation used python -B with scripts.build_landers.main(), --anchors-only --data-file docs/data/schedule_future.json; a unittest.mock.patch on tqdm selected exactly the two native IDs above. Audit-report writes and historical retirement were suppressed for this bounded call. Output: Landers built: 2; Expired static landers retired: 0. No full build chain ran locally; no offers were regenerated/filtered by this repair.

The October 10 occurrence is now in the past, so it correctly renders completed with no registration CTA. The future October 13 occurrence renders scheduled with canonical registration and Heartsaver/AHA/in-person metadata. Actual October 10 barnacle availability cannot be retrospectively proven from the current public surface; existing deterministic barnacle-policy tests pass and scheduling policy was not changed.

## Production proof

- All PR source-integrity/preflight and Cloudflare preview checks passed. Production host verification is separately GitHub Pages.
- First production Pages run 38106521485 succeeded at 2026-10-11 02:52:58 UTC.
- Existing autonomous admin refresh 38106472530 succeeded and published 85ff765fc8a0c8b584c76e41ec30d21446127c83 (38 workflow-owned files). This run was already active; this dispatch did not start a full refresh. Its intermediate Pages run 38106661136 was cancelled when the follow-up merge arrived; the final deployment below supersedes it.
- Final Pages run https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/38106670739 succeeded at 2026-10-11 02:55:37 UTC for e73c4b7aedcfefc87867259eeaead169e2c9a027.
- Final live GET proof at 02:56:07 UTC: both native class URLs HTTP 200; October 10 class_status completed/no CTA; October 13 class_status scheduled/canonical CTA; neither contains Unmapped course metadata. October 13 no longer contains Registration is not currently available. Canonical /register/?session=lw-eb020e4a-b74a-443e-acd8-05727c2a8170 GET HTTP 200. No booking/payment submitted.
- All four referenced local assets GET HTTP 200: /assets/analytics-attribution.js?v=20260912-1; /assets/live-sessions.js; /assets/session-expiry.js; /css/lander.css?v=20260808-session-discovery. No CSS/JS changed, so their URLs required no version change.
- Live selector check at 02:55:35 UTC: BLS generated 22:53:40 EDT, 3,967 offers; Heartsaver generated 22:53:48 EDT, 8,271 offers; both valid until 23:08:38 EDT / 03:08:38 UTC, both unexpired. These are observed counts, not offers created by this patch.

## Persistent proof contract and exact remaining blocker

Native page publication: PROVEN (source -> builder -> merged Pages -> live metadata/CTA and registration-route GET). Payment/registration submission is untested by design.

Recurring availability: PROVEN local containment; not cloud-independent MONITORED/HEALTHY. Expected outcome is renewed, unexpired, usable public inventory. Current effective freshness window is approximately 15 minutes despite the outer 90-minute lease. Staleness means no successful deployment before the source-capped validUntil or unusable customer HTML/booking paths. Existing local watchdog recovery depends on CYBERPC being awake, online and logged in. Existing scheduled observer is intended to observe watchdog health, but independent observer health is unproven: GitHub API GET actions/variables/AVAILABILITY_WATCHDOG_HEALTH_URL returned HTTP 404 during this dispatch.

Exact gate retained from owner issue comments: repository-restricted fine-grained GitHub token with Actions read/write must be approved/created and stored only as the Cloudflare encrypted GITHUB_ACTIONS_TOKEN secret; engineering can then activate/verify the cloud timer, configure AVAILABILITY_WATCHDOG_HEALTH_URL, and prove the observer itself. No token value was requested, read or committed here. The absent variable is directly observed; secret/token provisioning remains an existing owner-recorded gate, not independently audited in this dispatch.

Recovery: inspect fresh source caps and latest admin/public publisher + Pages outcome; bounded current-main refresh only when required, retaining source/conflict and strict-link safety. Escalate credential/account authorization to owner; deterministic repository failures remain engineering work. Brian must not be accepted as the routine monitoring layer. Do not close #334 based on this page repair.

## Preservation and next action

Original E:/GitHub/910cpr-class-landers dirty checkout preserved. Separate worktree: E:/GitHub/910cpr-issue334-native-metadata. Earl/Jackson HTML and tracked build_landers/build_metadata/title_cleaner bytecode changes remain uncommitted and excluded; no cleanup/reset/rebase performed locally. No private participant data committed. No intentional new untracked files remain. Draft #372 remains OPEN and draft; it was not merged/deployed. Existing assignments and deep workstreams were preserved. Queue titles were scanned; separate significant feature requests were not started as competing deep work.

Recommended ChatGPT action: review the two merged PR diffs and this receipt, acknowledge through the protocol, retain #334 open, and continue the existing cloud-token/observer gate once account authorization is available. Do not reopen the already-accepted strict-link repair or rerun it as a new incident. No owner action is needed for the completed native-page repair; the pre-existing credential gate is the only identified account-level action.

Receipt commit SHA is the branch tip discoverable from GitHub; the substantive SHAs are recorded above to avoid a self-referential receipt hash.