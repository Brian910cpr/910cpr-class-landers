# Codex read receipt — Issue #371 Path A R1

- Reviewed at: 2026-10-12T14:44:21.752Z
- Handoff: `Codex_Reply_Issue371_PathA_Audit_20261012_R1.md`
- Substantive commit reviewed: `a2798d1873f9537d81246ad5572ec135a81adb65`
- Result: live read-only metadata exposed a material grant bug in the pending migrations: PostgreSQL default ACLs give `service_role` ALL, so allowlisted grants alone would leave UPDATE/DELETE/TRUNCATE on audit storage. The branch now explicitly revokes inherited privileges before granting the intended allowlist, with 38 local SQL/auth tests passing.
- Safety boundary: no production migration, function deployment, customer write, merge, UI exposure, or rollout occurred. PR #372 remains draft.
- Remaining gates: verified recoverable backup/export and restore path, feature-gated durable UI, real owner-session browser/API/database reload-resume-conflict proof, and tested CORS/endpoint allowlisting.
- Brian action: none yet; request explicit GO only after the safety gates pass.
