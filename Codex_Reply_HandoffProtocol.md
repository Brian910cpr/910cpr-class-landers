# Codex Reply: HandoffProtocol

## Assignment

- Identifier: `HandoffProtocol`
- Timestamp: `2026-09-08T21:54:21.9660937-04:00`
- Retirement-sweep update: `2026-09-10T08:56:24-04:00`
- Branch: `codex/handoff-protocol`
- Protocol implementation commit: `67c49acab302823734fe49b719b4c96f24101d9c`
- Legacy-retirement commit: `8c38a9ddb7e89a45827400d0044bace782834633`

## Findings and placement decision

The repository already contained an `ops/handoff/` directory, a mutable latest-task bundle added in commit `3bce4ea61cf9ca216b3dc4e5f2f340de0e996562` on June 9, 2026. Its `next_task.md` instructed Codex to overwrite four `latest_*` outputs, and `ops/scripts/show_handoff.ps1` presented that task and those outputs as the active handoff. No workflow or other repository script invoked the helper, but a person or older session could still run it. It therefore competed with the new durable mailbox and was retired.

The sweep also found the `[CODEX]` GitHub Issue instruction inbox in `docs/CODEX_INSTRUCTIONS.md` and `AGENTS.md`. It is active, durable inbound instruction intake rather than a competing Codex-to-ChatGPT reply mechanism, so it was preserved and explicitly documented as complementary.

A bounded scan of safely discoverable Codex worktrees found one older checkout of this repository containing the same `ops/handoff/` mechanism and no additional Start handoff, handoff starter, Codex inbox, agent mailbox, reply-polling, or ChatGPT/Codex bridge implementation. Old checkouts were not modified; the authoritative branch retirement prevents the legacy mechanism from returning when they update.

The durable protocol was therefore placed at repository root in `CODEX_HANDOFF_PROTOCOL.md`. This is the most discoverable stable location and matches the assignment's preferred location. The former `ops/handoff/` mechanism is now explicitly inert; the inbound `[CODEX]` GitHub Issue workflow remains intact and is explicitly described as complementary.

## Work performed

- Added the full durable mailbox contract in `CODEX_HANDOFF_PROTOCOL.md`.
- Added a concise mandatory `AGENTS.md` instruction requiring every Codex assignment to leave a repository reply unless the assigning prompt explicitly opts out.
- Defined `Codex_Reply_<ID>.md` as unread and `Codex_Read_<ID>.md` as processed.
- Reserved creation and renaming of `Codex_Read_*` exclusively for ChatGPT/the supervising process.
- Defined required reply fields, immutable round identifiers, global supervisor sweeps, the approximately 20-minute pickup model, and the hourly fallback watcher.
- Documented that timing is ChatGPT behavior only and is not implemented by repository application code.
- Declared `CODEX_HANDOFF_PROTOCOL.md` the sole authoritative outbound reply/acknowledgement mechanism.
- Replaced `ops/handoff/next_task.md` with an explicit retirement marker.
- Added `ops/handoff/README.md` to classify retained doctrine, notes, and `latest_*` files as inert historical snapshots.
- Removed the obsolete executable `ops/scripts/show_handoff.ps1` so it cannot present or consume the retired workflow.
- Preserved `ops/handoff/MUST_REMEMBER.md`, `chatgpt_notes.md`, and historical reports because they contain unique scheduling doctrine, safety notes, and task history.
- Bootstrapped this assignment with this `Codex_Reply_HandoffProtocol.md` reply.

## Files changed

- `AGENTS.md`
- `CODEX_HANDOFF_PROTOCOL.md`
- `Codex_Reply_HandoffProtocol.md`
- `ops/handoff/README.md`
- `ops/handoff/next_task.md`
- `ops/scripts/show_handoff.ps1` (removed)

No scheduling, registration, availability, public-page, Cloudflare, deployment, participant, Enrollware, HOT_SYNC, or other production application files were changed.

## How future Codex tasks discover the rule

Codex reads the repository-root `AGENTS.md` as the repository instruction source. Its new mandatory mailbox section points directly to `CODEX_HANDOFF_PROTOCOL.md` and states the default requirement, opt-out rule, reply naming rule, and prohibition against Codex creating `Codex_Read_*` files. The full root protocol then supplies the operational details.

## Checks and results

- Inspected `AGENTS.md`, `ops/handoff/`, `ops/scripts/show_handoff.ps1`, root documentation, repository history, references to legacy filenames, the existing inbound Codex instruction mechanism, and safely discoverable local worktrees for this repository.
- Confirmed the required protocol phrases and timing/sweep rules are present.
- Ran `git diff --check` for the protocol changes: passed.
- Confirmed the initial protocol commit contains only `AGENTS.md` and `CODEX_HANDOFF_PROTOCOL.md`.
- Confirmed retirement commit `8c38a9ddb7e89a45827400d0044bace782834633` contains only protocol/legacy-handoff documentation and removal of the obsolete helper.
- Confirmed no tracked workflow or script outside the retired mechanism invokes `show_handoff.ps1` or the mutable `latest_*` output contract.
- Application tests were not run because this assignment changes only Markdown operational documentation.
- Known unrelated working-tree state: Windows case-colliding generated pages (`docs/ACLS.html`, `docs/BLS.html`, `docs/Earl/index.html`, `docs/HEARTSAVER.html`, and `docs/PALS.html`) appeared modified immediately after clean worktree creation. They were not altered, staged, or committed by this task.

## Deployment status

- Protocol: committed in `67c49acab302823734fe49b719b4c96f24101d9c`.
- Legacy retirement: committed in `8c38a9ddb7e89a45827400d0044bace782834633`.
- Reply: committed in a separate communication-only commit after the protocol commit to avoid a self-referential commit SHA.
- Branch push: performed after both commits.
- Merge: not performed.
- Application deployment: not applicable and not performed.

## Limitations and remaining risks

- The repository convention cannot itself wake ChatGPT or create timers. ChatGPT/the supervising system must implement the 20-minute pickup checks and hourly recovery sweep externally.
- Cross-conversation durability depends on Codex pushing its branch and ChatGPT having GitHub access to sweep relevant branches/repository state.
- `AGENTS.md` makes the convention mandatory for agents that load repository instructions; it is not a server-side enforcement hook.
- Concurrent tasks must select unique IDs or round suffixes. The protocol forbids overwriting but does not add application code to lock filenames.
- Older local worktrees retain their historical checkout until fetched/updated; they were inspected but not mutated because they contain unrelated state.

## Recommended next action for ChatGPT

Fetch branch `codex/handoff-protocol`, inspect commits `67c49acab302823734fe49b719b4c96f24101d9c` and `8c38a9ddb7e89a45827400d0044bace782834633` plus this reply, then merge the branch if acceptable. After actually reading and deciding the next action, rename `Codex_Reply_HandoffProtocol.md` to `Codex_Read_HandoffProtocol.md`, commit that acknowledgement, and push it without overwriting prior history.

## User or account-level action required

No user/account action is required to use the repository file convention itself. The supervising ChatGPT environment must separately provide GitHub repository access and configure the documented pickup/watcher timing if automated sweeps are desired.

## Readiness

The durable handoff protocol is ready for use once this branch is merged into the branch from which future Codex assignments begin.
