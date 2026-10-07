# Codex read delta: V2 release reconciliation

Reviewed 2026-10-07 after the original read receipt, against PR #353 commit `c36f3e818df09f9983dd404925d838c49748f58f` and the resulting actual-data probe.

This file preserves the earlier `Codex_Read_v2_release_reconciliation.md` and records changed evidence rather than replacing it.

## Changed evidence

[Run 37618669167](https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/37618669167) again read current production sources successfully: 250 iCal events, 25 canonical demand sessions, three HOT_SYNC records, 161 calendar events, and 206 inverse-generated availability blocks.

The calculation then advanced beyond the prior empty-evaluation guard and failed in the publication adapter at:

`public_policy_reasons -> if start < reference`

with:

`TypeError: can't compare offset-naive and offset-aware datetimes`

Publication remained stopped and only the proof artifact was uploaded.

## Current disposition

PR #353 remains draft, shadow-only, and not accepted for merge or activation. A successful branch preview still does not satisfy release proof.

The existing requested receipt `Codex_Reply_PR353_20261007T121500Z_R1.md` must include both stages of actual-data evidence:

1. the earlier 205/205 `unresolved_occupied_bounds` rejection; and
2. the later timezone-normalization crash.

Repair the timezone contract at the policy boundary, add an explicit mixed-offset regression, then rerun the same nonpublishing probe. Acceptance still requires `evaluated_windows > 0`, inspectable decision/rejection evidence, no unbounded occupancy admitted, and `published: false`.

Owner-only action: none; engineering is handling this bounded repair.
