# Issue 290 — current production reverification

- Assignment: https://github.com/Brian910cpr/910cpr-class-landers/issues/290
- Timestamp: 2026-10-10T21:18:39.6563783-04:00 (America/New_York)
- Branch: codex/issue-290-reverification-20261010
- Evidence commit: 499b65c7f6127b830ed14b8749675844d695199d
- Base main: 0acc0c32b5a0deab012c15766e5af71571122a4b
- Work-item state: VERIFIED for existing implementation/static production asset delivery; fresh browser acceptance is BLOCKED by unavailable browser tooling.
- Application evidence: prior implementation PROVEN by retained production/browser evidence; this run rechecks local tests and production HTTP delivery only. No continuous HEALTHY/MONITORED claim.

## Findings and work performed

Read full issue body/comments, current GitHub AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Acknowledged actual execution before implementation: https://github.com/Brian910cpr/910cpr-class-landers/issues/290#issuecomment-6104096962 . Formal blocked_by dependencies returned an empty list.

The requested implementation already exists in merged PR291, production merge b61c05157fb4d0ea6d588e75ced2a3b8b53f0ef6. PR292 persisted production evidence; PR293 corrected PALS artwork. Reused these records; no duplicate implementation/PR, generated art, substitute art or public rebuild. Issue290 remains open for supervisor acceptance.

BLS uses responsive derivatives of the approved 1312 x 1199 original rather than the tiny nurse image. ACLS existing-file numbered discovery and reload rotation remain present. Shared generator retains adjacent AHA branding. Local tests cover 1/2/3/5/12 rotation candidates and missing-number/storage/load-failure cases. Current production HTML for all five requested pages has hero markup, AHA card code and registration code, and none references bls-9to1-nurse.webp. All 16 referenced hero/script/AHA assets match committed main, including their content-version URLs.

## Exact changed files

- data/audit/issue_290_reverification_20261010.json
- Codex_Reply_Issue290_Reverification_20261010_R1.md

Application source/config/output changes: none. No generators executed. No scheduling, offer, price, registration, auth, payment or backend changes.

## Checks and results

- python -B -m unittest tests.test_family_course_art tests.test_family_cpr_page — 24 passed.
- node --test tests/family_hero.test.mjs — 8 passed.
- node --check docs/assets/family-hero.js — passed.
- Python ast.parse: scripts/family_course_art.py; scripts/refresh_selector_presentation.py; scripts/build_bls_block_schedule_pilot.py — passed.
- Production HTTP: 21 URLs returned 200 at 2026-10-11T01:17:48Z. Per-URL hashes/results in the new JSON audit.
- All 16 referenced assets match authoritative Git blob SHA256. Initial working-tree byte comparison failed for JS because Windows converted LF to CRLF; Git blob comparison resolves it. Audit preserves both comparisons.
- git diff --check — passed.
- Browser attempt: cua.createBrowserTab(iab, ...) reported Browser is not available: iab; cua.listBrowsers() returned []. No fresh screenshots, rendered desktop/mobile checks, interactive calendar checks or submitted registrations in this run.

Historical browser evidence is explicitly historical: Codex_Read_Issue290.md and data/audit/issue_290_course_art.md record 1280x900 and 392x844 checks, loaded calendars/registration links, adjacent logos and RN/medic/pharmacist reload rotation. data/audit/issue_290_live_verification.json is the original deployed evidence. No new visual claim is inferred from HTTP alone.

## Workspace safety and unrelated failures

Original E:/GitHub/910cpr-class-landers remains on codex/durable-session-participant-linking with its existing dirty HTML/data/bytecode/runtime artifacts preserved. Fetch failed with missing object 6e61cabca5981d1389e52c60d95424d9893bb50f and bad ref refs/remotes/origin/codex/group-training-experience. Cached origin/main was 2026-09-15, so it was not used for changes. No destructive Git repair, cleanup, restore, rebase or merge performed.

An initially created isolated worktree E:/GitHub/910cpr-issue290-art-20261010, codex/issue-290-art-20261010, remains unused on stale main. Current work uses a fresh isolated shallow checkout E:/GitHub/910cpr-issue290-current-20261010. This is recovery from unusable Git objects, not a replacement application project. Windows case collisions produce unrelated docs/Earl/index.html and docs/Jackson/index.html differences; excluded from commits. No intentional files left untracked after receipt commit.

Queue and existing PRs were scanned. Preserved the primary backend stream and all assignments. PR372 remains draft, unmerged, undeployed. Its existing preview gate requires an owner-authorized isolated Supabase project reference and browser origin; no authorization invented from third-party comments. No unrelated backend mutation was safe/needed for this completed preexisting artwork task; existing backend assignments remain queued/active in their own streams.

## Deployment and next action

Persisted locally and committed; receipt branch pushed to GitHub as part of this dispatch. No merge, deployment or infrastructure action in this run. Prior public implementation remains deployed; current static delivery verified. No binary-asset dependency remains.

ChatGPT: inspect this JSON audit and existing PR291/292/293; arrange a fresh browser desktop/mobile check when browser tooling is available, then accept/close issue290 if satisfied. Do not reopen/rebuild the existing implementation merely because this issue is still open. Do not merge/deploy PR372. No Brian/account action required for artwork; browser-tool availability is the current verification limitation. Shared Git database corruption needs a separate preservation-first maintenance assignment if that checkout must fetch again.

This is a bounded one-time check, not a new persistent monitor. Last current proof is the HTTP/static-asset check above; it does not prove ongoing selector or launcher health. Existing supervisor pickup owns receipt acknowledgement; this run does not claim observer health.
