# Codex read — Issue 380 R8 ranking hardening

Reviewed: 2026-10-12T16:40:05.640Z
Round: delta-watch-20261012T1642Z-issue380-r8
Reply: Codex_Reply_Issue380_20261012_R8.md
Substantive commit: 1ca2d536be80ab6bbf99266d876a386a6bc52171
PR: #381

Reviewed the exact ranking diff and branch checks. The change fails closed by recomputing each candidate from its supplied typed state and expected version instead of trusting a cached caller-supplied decision. It also rejects duplicate/non-positive/non-integer issue identities and unknown priorities while preserving deterministic P0/owner/tie ordering. The focused 41-test suite, syntax checks, Source Integrity, and Cloudflare preflight passed.

Safe disposition: keep PR #381 draft. This closes a latent ranking defect but grants no execution authority and has no runtime caller. Continue on the same PR with authenticated canonical snapshot intake, transactional versioned claim/skip/audit, and an actual pre-mutation no-launch proof. No merge, deployment, installed-loop change, or owner action was performed.