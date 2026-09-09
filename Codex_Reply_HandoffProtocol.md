# Codex Reply: HandoffProtocol

## Assignment

- Identifier: `HandoffProtocol`
- Timestamp: `2026-09-08T21:54:21.9660937-04:00`
- Branch: `codex/handoff-protocol`
- Protocol implementation commit: `67c49acab302823734fe49b719b4c96f24101d9c`

## Findings and placement decision

The repository already contained an `ops/handoff/` directory, but it is a mutable latest-task bundle with scheduling-specific doctrine and reports. Reusing it as an immutable unread/read mailbox would create overlapping meanings and risk overwriting history.

The durable protocol was therefore placed at repository root in `CODEX_HANDOFF_PROTOCOL.md`. This is the most discoverable stable location and matches the assignment's preferred location. The existing `ops/handoff/` mechanism and the inbound `[CODEX]` GitHub Issue workflow remain intact and are explicitly described as complementary rather than replaced.

## Work performed

- Added the full durable mailbox contract in `CODEX_HANDOFF_PROTOCOL.md`.
- Added a concise mandatory `AGENTS.md` instruction requiring every Codex assignment to leave a repository reply unless the assigning prompt explicitly opts out.
- Defined `Codex_Reply_<ID>.md` as unread and `Codex_Read_<ID>.md` as processed.
- Reserved creation and renaming of `Codex_Read_*` exclusively for ChatGPT/the supervising process.
- Defined required reply fields, immutable round identifiers, global supervisor sweeps, the approximately 20-minute pickup model, and the hourly fallback watcher.
- Documented that timing is ChatGPT behavior only and is not implemented by repository application code.
- Bootstrapped this assignment with this `Codex_Reply_HandoffProtocol.md` reply.

## Files changed

- `AGENTS.md`
- `CODEX_HANDOFF_PROTOCOL.md`
- `Codex_Reply_HandoffProtocol.md`

No scheduling, registration, availability, public-page, Cloudflare, deployment, participant, Enrollware, HOT_SYNC, or other production application files were changed.

## How future Codex tasks discover the rule

Codex reads the repository-root `AGENTS.md` as the repository instruction source. Its new mandatory mailbox section points directly to `CODEX_HANDOFF_PROTOCOL.md` and states the default requirement, opt-out rule, reply naming rule, and prohibition against Codex creating `Codex_Read_*` files. The full root protocol then supplies the operational details.

## Checks and results

- Inspected `AGENTS.md`, `ops/handoff/`, `ops/scripts/show_handoff.ps1`, root documentation, and the existing inbound Codex instruction mechanism.
- Confirmed the required protocol phrases and timing/sweep rules are present.
- Ran `git diff --check` for the protocol changes: passed.
- Confirmed the substantive protocol commit contains only `AGENTS.md` and `CODEX_HANDOFF_PROTOCOL.md`.
- Application tests were not run because this assignment changes only Markdown operational documentation.
- Known unrelated working-tree state: Windows case-colliding generated pages (`docs/ACLS.html`, `docs/BLS.html`, `docs/Earl/index.html`, `docs/HEARTSAVER.html`, and `docs/PALS.html`) appeared modified immediately after clean worktree creation. They were not altered, staged, or committed by this task.

## Deployment status

- Protocol: committed locally in `67c49acab302823734fe49b719b4c96f24101d9c`.
- Reply: committed in a separate communication-only commit after the protocol commit to avoid a self-referential commit SHA.
- Branch push: performed after both commits.
- Merge: not performed.
- Application deployment: not applicable and not performed.

## Limitations and remaining risks

- The repository convention cannot itself wake ChatGPT or create timers. ChatGPT/the supervising system must implement the 20-minute pickup checks and hourly recovery sweep externally.
- Cross-conversation durability depends on Codex pushing its branch and ChatGPT having GitHub access to sweep relevant branches/repository state.
- `AGENTS.md` makes the convention mandatory for agents that load repository instructions; it is not a server-side enforcement hook.
- Concurrent tasks must select unique IDs or round suffixes. The protocol forbids overwriting but does not add application code to lock filenames.

## Recommended next action for ChatGPT

Fetch branch `codex/handoff-protocol`, inspect commit `67c49acab302823734fe49b719b4c96f24101d9c` and this reply, then merge the branch if acceptable. After actually reading and deciding the next action, rename `Codex_Reply_HandoffProtocol.md` to `Codex_Read_HandoffProtocol.md`, commit that acknowledgement, and push it without overwriting prior history.

## User or account-level action required

No user/account action is required to use the repository file convention itself. The supervising ChatGPT environment must separately provide GitHub repository access and configure the documented pickup/watcher timing if automated sweeps are desired.

## Readiness

The durable handoff protocol is ready for use once this branch is merged into the branch from which future Codex assignments begin.
