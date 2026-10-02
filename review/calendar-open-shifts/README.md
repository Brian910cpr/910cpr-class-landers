# Calendar implementation checkpoint

Owner request: https://github.com/Brian910cpr/910cpr-class-landers/issues/338
Branch: fix/calendar-open-shifts-20261002. Evidence: BUILT; release IN_PROGRESS.

The Operations calendar now derives occupancy, merged blocks, edges and validated skills/full-course candidates from configured instructor calendars and real sessions. Skills are45 instruction+15 cleanup; in-person120+30. Source starts are preserved, longer real source commitments remain occupied, unknown counts remain unknown. Friday10:45/12:45 and Saturday12:30/13:00 cleanup overlaps produce diagnostics and constrain overlapping offers without suppressing unrelated legitimate edges. No session/registration/payment source was mutated.

Final checkpoint validation:28 focused JS tests,8 adjacent JS tests,65 refresh-workflow scheduling tests,20 publisher/availability tests passed. Chrome desktop/mobile fixture QA passed with zero errors,36 candidates/16 accepted/20 rejected, sequential growth, full-class growth and24-hour free-day checks. Asset node syntax and git diff whitespace checks passed. Broader full-repository suites were not run.

Two broader dashboard tests previously reproduced on unmodified HEAD:tests/dashboard_ops.test.cjs:61 demands adminKeyInput type=password while current authentication uses hidden;tests/dashboard_schedule.test.cjs:82 demands removed literal Same-time location conflict. These assertions do not invalidate the separately tested calendar model/render; authentication behavior was preserved. They remain uncorrected baseline test debt.

Isolated lab worktree:C:/Users/ten77/AppData/Local/Temp/landerware-scheduling-lab; branchlab/scheduling-laboratory-20261002; timing commit8b5fb4975;26 lab tests passed. Candidate diagnostics show instruction/cleanup ends. One historical conflicting Heartsaver-duration fixture is deliberately retained and labeled for guard regression.

## Public release gate
Read-only live Chrome verification at2026-10-02T05:12UTC found the actual public /bls.html calendar rendered without JS errors and retained the real October2 12:45PM class. Availability was expired (validUntil02:23:51UTC); schedule and availability snapshots were00:53UTC. review/calendar-open-shifts/public-calendar-checkpoint.json records source timestamps and rendered text.

The public feed reports daily-anchor-stack-v1,808 suppressed offers,zero barnacle positions,one_course_type_per_calendar_day=true. scripts/apply_anchor_policy.py:324 excludes anchored courses from repeat candidates; lines335-371 select around individual sessions rather than merged occupied blocks. Therefore this Operations-only integration cannot prove the owner's customer-facing block-growth requirement. This is a material release gate, not an authorization question. Push/PR/merge/deploy/refresh authorization remains in force after final gates pass. None has been performed in this checkpoint.

Next:implement and test the public selector/publication bridge using legitimate merged block edges and existing validated appointment identifiers; preserve real sessions and fail on unresolved source constraints. Recheck concurrent PR333 (anchor/selector overlap), then review/merge/deploy and authorized refresh; verify live dated offers, assets, freshness and booking preservation. No independent observer-health proof exists; do not classify HEALTHY. Unrelated Earl/Jackson edits are excluded.
