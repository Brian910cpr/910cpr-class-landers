# Production refresh seated-only lease validation

Run37631430887 completed selector rendering and stopped in validate_public_refresh_output: acls expired publication. ACLS has4 existing-class starts and no calculated offerings; V2 finalizer sets publication expiry to calculation time when no calculated offers remain. Existing finalizer/browser deliberately preserve seated classes after offer lease expiry.

Narrow validator alignment: require aware expiry always; require unexpired publication whenever any calculated or untyped offer exists. Only strictly seated-only/empty inventory may pass without a calculated-offer lease. Existing source identity, booking reconciliation and every other inventory validation unchanged. No lease extended or fabricated.

27 targeted validation/publication tests passed. New regression permits existing classes after lease expiry but rejects mixed expired dynamic and untyped offers. Scope only failed validation step. Production not claimed updated. Current dirty Earl/Jackson pages preserved.
