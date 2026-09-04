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

## Workstream rule

Only one implementation workstream is active at a time. A new issue preserves the request without silently interrupting active production work. Brian may explicitly promote an issue when priorities change.
