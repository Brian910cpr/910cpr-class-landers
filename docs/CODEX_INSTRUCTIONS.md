# Giving Codex Instructions

Use a GitHub Issue as the durable instruction inbox for this repository.

## From ChatGPT

Tell ChatGPT what should change in ordinary language. When GitHub access is available, ChatGPT should create or update an issue whose title begins with `[CODEX]`. That issue preserves the instruction, discussion, decisions, and resulting pull request even after the chat ends.

## From GitHub

1. Open the repository's **Issues** tab.
2. Choose **New issue**.
3. Select **Instruction for Codex**.
4. Describe the outcome you want. Technical language is not required.
5. Add screenshots, links, or exact wording when helpful.
6. Choose whether it belongs in the queue, should be next, or represents a production failure.

## Status

The issue conversation is the authoritative task record. Codex should post:

- its interpretation and material assumptions;
- any question that blocks correct implementation;
- the branch or pull request;
- what was validated;
- whether the result is local, merged, deployed, and live-verified.

A markdown report elsewhere in the repository is supporting evidence, not a substitute for answering on the issue.

## Production-line workstream rule

The queue is **not** a strict one-item-at-a-time conveyor. Codex should keep one primary/deep implementation workstream as the focus while opportunistically advancing independent quick wins in parallel.

On every queue refresh or wake:

1. Continue the active primary workstream unless it is blocked or unsafe to continue.
2. Scan all open actionable `[CODEX]` issues, not merely the oldest or current issue.
3. Identify independent quick wins that can be completed or materially advanced without destabilizing the primary workstream.
4. Prefer quick wins that are low-risk, narrowly scoped, independently testable, and unlikely to create merge conflicts with the primary workstream.
5. Complete as many safe quick wins as practical during the available work period while continuing the primary workstream.
6. Record an independent receipt/status for every item touched. Do not make one task wait merely because another task has not finished.
7. If an item is blocked, record the blocker and continue with other actionable work. A blocked item must not stall the queue.

Do **not** start several competing deep refactors merely to create parallelism. Parallelism is primarily for independent quick fixes, diagnostics, tests, documentation, narrowly scoped repairs, and other work that can safely coexist with the primary job.

The approximately 20-minute ChatGPT pickup cadence is a **heartbeat/checkpoint, not a job timebox**. Codex does not stop a valid longer-running workstream when a pickup occurs. ChatGPT may consume completed receipts and dispatch follow-up work while Codex continues other outstanding items.

A useful checkpoint can therefore report several different states at once, for example: one issue deployed and verified, another with tests fixed and a PR open, another blocked with a documented reason, and the primary implementation still in progress.

Brian may explicitly promote an issue when priorities change. Production failures and safety-critical conflicts outrank ordinary quick wins.
