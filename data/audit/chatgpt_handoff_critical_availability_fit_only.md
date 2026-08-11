# Critical availability fit-only debugging handoff

## Result

The public block selector now runs in `FIT_ONLY_DEBUG` mode. Candidate eligibility uses the selected course's actual `duration_minutes`; setup, cleanup, travel, lead-time, same-day anchor, shared cooldown, and publication-cap preferences do not exclude a fitting candidate. Real seated-class/calendar overlap, operating hours, public location/container feasibility, and instructor qualification remain hard gates.

The live calendar snapshots were refreshed read-only on 2026-08-11. The previous July 20 snapshot was stale and showed Aug 13 blocked from 06:00-18:00. The refreshed snapshot shows a continuous available window from 06:00 on Aug 13 through midnight, containing the planner's 08:00-10:00 and 18:00-19:00 windows.

## Primary audit

- `data/audit/critical_availability_fit_only_debug.json`
- Mode: `FIT_ONLY_DEBUG`
- Aug 12-13 fitting offers across the five affected pages: 563
- Rejected candidate/course starts retained with full diagnostics: 445
- Every rejection row exposes `candidate_date`, `candidate_start`, `course_id`, `required_duration_minutes`, `open_window_start`, `open_window_end`, and `rejection_reason`.

## Skills-testing starts

- AHA HeartCode BLS (`210549`, 60 minutes): Aug 12 every 30 minutes from 08:00 through 17:00; Aug 13 every 30 minutes from 08:00 through 19:00.
- HSI BLS Challenge (`463743`, 60 minutes): Aug 12 every 30 minutes from 08:00 through 17:00; Aug 13 every 30 minutes from 08:00 through 19:00.
- HSI BLS + Adult First Aid (`445670`, 45 minutes): Aug 12 every 30 minutes from 08:00 through 17:00; Aug 13 every 30 minutes from 08:00 through 19:00.
- Online learning + in-person skills (`329495`, 120 minutes): Aug 12 every 30 minutes from 08:00 through 16:00; Aug 13 every 30 minutes from 08:00 through 19:00.

## Rejections on the target dates

The regenerated artifacts reject target-date candidates only for `OUTSIDE_ALLOWED_OPERATING_HOURS` and `INSUFFICIENT_CONTIGUOUS_TIME`. No target-date rejection is caused by setup/cleanup/travel padding, lead time, preferred spacing, repeat suppression, barnacle placement, or offer caps. Full candidate rows are in the primary JSON audit and each family block-schedule JSON.

## Authoritative changes and outputs

- Source: `scripts/block_start_time_selector.py`
- Test: `tests/test_block_start_time_selector.py`
- Refreshed inputs: `data/runtime/calendar_snapshots/*.json`
- Refreshed planner projection: `data/audit/live_availability_snapshot_preview.json`
- Generated public availability: `docs/data/block-selector-availability/{bls,heartsaver,uscg_first_aid_cpr_aed,hsi,family_cpr}.json`
- Generated family HTML and audit JSON/Markdown were rebuilt by `scripts.build_bls_block_schedule_pilot.run_page` for those same five pages.

## Validation

- `python -m py_compile scripts/block_start_time_selector.py tests/test_block_start_time_selector.py`: passed.
- Three focused unit tests covering fit-only mode, disabled lead-time exclusion, and preserved travel-rule behavior outside fit-only occupancy: passed.
- Generated artifact assertions verified HeartCode starts at 08:00, 08:30, 09:00, and 09:30 on both dates and 18:00 on Aug 13.
- Required rejection diagnostic fields: verified on all 445 target-date rejection rows.
- `git diff --check` on source and test: passed (line-ending warnings only).

## Repository state

Prepared as an isolated commit on existing branch `codex/maxim-authoritative-availability`. Not pushed, deployed, or live-HTML verified. The worktree already contained extensive unrelated changes; those changes are excluded from the availability-fix commit.
