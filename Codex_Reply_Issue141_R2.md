# Codex reply: Issue 141, round 2

- Assignment: GitHub issue #141, `Brian910cpr/910cpr-class-landers`
- Timestamp: 2026-09-11T13:19:05-04:00
- Branch: `codex/issue-141-historical-browser`
- Substantive commit: `4ac773aaef9cffbb06a4373b294ad048536b2647`
- Pull request: #187 (stacked on issue #141 backfill PR #147)
- Work-item state: `PR_OPEN`
- Persistent-system evidence state: not applicable to this design-only checkpoint; no persistent process was built or enabled

## Findings

The production historical backfill reported on issue #141 has run, but PR #147 remains open. The issue's historical record-browser outcome overlaps issue #129, whose owner direction explicitly pauses implementation. Implementing another browser now would violate that dependency and create a competing UI/auth boundary.

Existing checked-in LanderWare tables already provide anchors for people, organizations, requirements, sessions, registrations, roster memberships, documents, messages, activity events, credentials, and self-service tokens. However, the authoritative DDL for the older production `class_sessions`, `customers`, and `registrations` tables targeted by PR #147 is not checked in. A bridging migration cannot be safely designed from query references alone.

## Work performed

Created the required pre-implementation design gate for the owner additions on issue #141:

- scheduling/rescheduling lifecycle with mandatory required-by context;
- positive-fact attendance separate from completion and closeout;
- affirmative provenance gate before missed-class or employer communication;
- reusable, hashed, server-validated self-service token behavior;
- neutral participant/employer communication policy;
- proposed fail-closed bulk absence anomaly thresholds;
- compact one-page KJ-1958-derived roster field map for up to 10 participants;
- continuation-page and instructor-responsibility behavior for more than 10 participants;
- admin/Maxim surface map, dependencies, and the next safe migration/test slice.

Posted a public, PII-free design checkpoint with hard gates to issue #141: https://github.com/Brian910cpr/910cpr-class-landers/issues/141#issuecomment-5638076209

## Exact files intentionally changed

- `data/audit/issue_141_lifecycle_and_roster_design.md`
- `Codex_Reply_Issue141_R2.md` (this receipt)

## Tests and checks

- `git diff --check -- data/audit/issue_141_lifecycle_and_roster_design.md` — passed.
- Read the full issue body and every issue comment before work.
- Read repository `AGENTS.md` and `CODEX_HANDOFF_PROTOCOL.md` from current `origin/main` before work; the issue branch predates the root protocol file.
- Read `LANDERWARE_PROOF_AND_HEALTH_STANDARD.md` and the relevant canonical LanderWare migrations.
- Checked PR #147 state/checks and issue #129 dependency state.
- No generator, database query/write, migration, outbound message, document upload, merge, or deployment was performed.

## Known unrelated working-tree changes

The clean continuation worktree acquired modifications to five generated pages immediately after checkout: `docs/ACLS.html`, `docs/BLS.html`, `docs/Earl/index.html`, `docs/HEARTSAVER.html`, and `docs/PALS.html`. They were not created for this assignment, were preserved, and were not staged or committed.

The original checkout also remains dirty on `codex/durable-session-participant-linking`; it was not modified or cleaned by this work.

## Deployment status

- Local validation: design artifact validated.
- Push: substantive commit pushed.
- PR: #187 open, stacked on PR #147.
- Merge: not performed.
- Deployment: not performed and not applicable to a design-only artifact.
- Production changes: none.

## Blockers and remaining risks

1. PR #147 remains open; its Cloudflare Pages check is failing.
2. Issue #129 explicitly pauses historical record-browser implementation.
3. Production DDL for the older canonical tables must be introspected/documented before bridging them to `landerware_*` tables.
4. Owner approval is required for the proposed anomaly thresholds and expiration-to-required-by policy.
5. Approved AHA/910CPR/host logo assets and usage rights must be identified before roster rendering.
6. Outbound automation remains prohibited until database tests prove unknown attendance cannot send, provenance is required per recipient, replay is idempotent, and anomaly batches fail closed.

## Recommended next action for ChatGPT

Review PR #187's design artifact and obtain owner decisions on anomaly thresholds and required-by derivation. Separately resolve/review PR #147 and its failing Cloudflare Pages check. Once #147 has an integration base and production schema introspection is available, authorize the narrow migration-and-database-test slice described in the design; keep outbound sends disabled. Do not start the historical browser until issue #129 is reactivated.

## User/account action required

Owner decisions are required for the proposed bulk anomaly thresholds, deadline derivation policy, and approved logo assets. Authorized production schema introspection may require account credentials/access not present in this checkout.
