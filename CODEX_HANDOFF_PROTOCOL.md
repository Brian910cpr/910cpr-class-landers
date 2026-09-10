# Codex–ChatGPT Durable Handoff Protocol

## Purpose and authority

This repository-root protocol is the durable outbound mailbox convention between Codex and ChatGPT. It survives separate conversations and Codex sessions because messages are committed to the repository and pushed to GitHub.

This protocol complements the inbound `[CODEX]` GitHub Issue workflow documented in `docs/CODEX_INSTRUCTIONS.md`. That issue workflow remains the authoritative durable instruction channel.

The former mutable `ops/handoff/` workflow is retired. Its retained files are historical reference material only and must not be used to dispatch, generate, poll, or consume Codex handoffs. See `ops/handoff/README.md`.

Unless an assigning prompt explicitly opts out, **every Codex assignment must produce and commit a repository reply file**, including research-only, diagnostic, blocked, and no-code assignments.

## Persistent-system doctrine

For any assignment involving a persistent or operational process, Codex must also follow `LANDERWARE_PROOF_AND_HEALTH_STANDARD.md`.

A persistent system must not be reported as `DONE`, `WORKING`, `LIVE`, or `HEALTHY` merely because code exists, a commit was pushed, a deployment succeeded, or one component ran once. Report the actual evidence level reached: `BUILT`, `CONNECTED`, `PROVEN`, `MONITORED`, or `HEALTHY`.

The default engineering pattern is:

> Prove the smallest useful end-to-end process. Observe it until trustworthy. When proven pieces are composed into a larger process, move the primary health check upward to the larger end-to-end outcome while retaining component diagnostics for failure investigation.

The owner must not be the routine monitoring layer. Every persistent process must define what proves success, when success last occurred, what detects staleness/failure, what observes that detector, and what recovery or escalation path applies.

## Mailbox filenames

Codex writes unread replies at the repository root using:

```text
Codex_Reply_<ID>.md
```

Examples:

- `Codex_Reply_PR155.md`
- `Codex_Reply_Issue160.md`
- `Codex_Reply_LocalStateTest.md`
- `Codex_Reply_PR155_R2.md`

Use the assignment or incident identifier when one exists. Otherwise choose a short, stable, filesystem-safe identifier that clearly distinguishes the assignment.

ChatGPT/the supervising process acknowledges a processed reply by renaming it without changing the identifier:

```text
Codex_Reply_<ID>.md -> Codex_Read_<ID>.md
```

Only ChatGPT/the supervising process may create the `Codex_Read_*` state. **Codex must never create, rename, overwrite, or otherwise manufacture a `Codex_Read_*` file.**

## Required reply contents

Each `Codex_Reply_*` file must include the following when applicable:

- Assignment or incident identifier
- Timestamp, including timezone or UTC offset
- Branch
- Commit SHA
- Root cause or findings
- Work performed
- Exact files changed
- Tests and checks performed
- Test results
- Known unrelated failures
- Deployment status, explicitly distinguishing local validation, push, merge, and deployment
- Persistent-system evidence state (`BUILT`, `CONNECTED`, `PROVEN`, `MONITORED`, `HEALTHY`) when applicable
- Last successful end-to-end proof and its evidence when applicable
- Failure/staleness condition and observer health when applicable
- Remaining risks or unresolved questions
- Exact recommended next action for ChatGPT
- Whether user-level or account-level action is required

Facts, inferences, limitations, and blockers should be clearly distinguished. Research-only tasks still require a reply. If an assignment produces no application-code changes, Codex may commit only the reply and operational documentation needed for the handoff.

## Codex send procedure

1. Choose an unused reply identifier and check the repository root for both `Codex_Reply_<ID>.md` and `Codex_Read_<ID>.md`.
2. Complete and validate the assignment to the extent possible.
3. For persistent systems, classify the result under `LANDERWARE_PROOF_AND_HEALTH_STANDARD.md` and do not overstate completion.
4. Write the reply with the required contents. Never overwrite a prior reply or processed handoff.
5. Commit the reply with the assignment changes, or in a separate communication-only commit when that makes the record clearer.
6. Push the branch. A local-only file is not a durable cross-session handoff.
7. In the Codex UI response, identify the reply filename, branch, and commit SHA unless the assignment specifies a narrower response.

When a reply needs to name a commit and including the reply in that same commit would create a self-referential SHA problem, use two commits: commit the substantive work first, then commit the reply referencing that substantive commit. The pushed branch tip remains discoverable from GitHub.

## Round trips and immutable history

After ChatGPT processes a reply, it may rename it from `Codex_Reply_<ID>.md` to `Codex_Read_<ID>.md` and commit/push that acknowledgement.

If additional work is required, Codex creates a new round instead of overwriting history:

```text
Codex_Reply_PR155.md -> Codex_Read_PR155.md
Codex_Reply_PR155_R2.md -> Codex_Read_PR155_R2.md
```

Continue with `_R3`, `_R4`, and so on. Never reuse or overwrite a prior unread or processed filename.

## ChatGPT supervisor sweep

Whenever ChatGPT is awakened for **any Codex-related task**, it should first sweep the repository root for all `Codex_Reply_*` files, not only the reply associated with the event that caused the wake-up. This global sweep allows one completed Codex task to accelerate discovery of replies from other concurrent tasks.

ChatGPT may rename a reply to `Codex_Read_*` only after it has:

1. Read the reply.
2. Inspected the referenced work as appropriate.
3. Determined the next action.

ChatGPT/the supervising process should then commit and push the acknowledgement rename. If more work is required, it should dispatch the next round using a new round identifier.

## Supervisory timing model

This section documents intended ChatGPT behavior; it does not authorize repository code or workflow automation for timers.

- Each Codex dispatch should normally cause ChatGPT to schedule a fast pickup check approximately 20 minutes later.
- Every pickup checks all unread `Codex_Reply_*` files.
- Independent pending pickup timers remain useful even if their originating reply was already processed, because each timer provides another global mailbox sweep.
- A persistent hourly ChatGPT watcher acts as the recovery/fallback sweep.
- A missing reply remains outstanding. It is not a failure merely because the first fast check occurred before Codex finished.

## Safety and scope

- Mailbox files live at the repository root and are ordinary version-controlled Markdown.
- Do not store secrets, credentials, private participant data, or sensitive account information in replies.
- Do not use this protocol as authority to merge, deploy, modify application behavior, or broaden an assignment.
- Preserve existing reply/read history.
- Resolve filename collisions by selecting the next round identifier, never by overwriting.

## Authority and retired mechanisms

This file defines the only authoritative Codex-to-ChatGPT reply and acknowledgement mechanism in this repository. The authoritative directions are therefore:

- ChatGPT/owner to Codex: `[CODEX]` GitHub Issues, as documented in `docs/CODEX_INSTRUCTIONS.md`.
- Codex to ChatGPT: root `Codex_Reply_*` files governed by this protocol.
- ChatGPT acknowledgement: root `Codex_Read_*` files governed by this protocol.

Do not reactivate `ops/handoff/next_task.md`, recreate `ops/scripts/show_handoff.ps1`, or write new `ops/handoff/latest_*` outputs. Historical files under `ops/handoff/` may be consulted for their task-specific facts, but they have no mailbox state and no operational authority.
