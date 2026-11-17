# Codex Read — Issue #367 Manual Safety Slice

- **Round:** 20261011T032638Z-I367-MANUAL-SAFETY-READ-R1
- **Reply reviewed:** `Codex_Reply_Issue367_ManualSafety_20261010_R1.md`
- **Receipt tip:** `b520f0982af641a642b0aa6200174c1fd9fb685c`
- **Substantive commit:** `f3ab6ebb95d67bb366a3587f136cc24ffa4fc281`
- **Draft PR:** #379

Reviewed the exact two-file implementation diff, executable renderer test, current PR state, passing integrity/preflight checks, and the reported baseline routing failure.

## Disposition

The narrow safety slice is reasonable but remains partial and must not be merged as completion of #367:

- The physical BLS manual radio is disabled, visibly out of stock, and unselected.
- The direct AHA link remains usable in a new tab with `noopener noreferrer`.
- The eBook and own-copy choices use current 2025 wording.
- No catalog price or product ID changed.
- The focused renderer test executes the actual JavaScript output.

PR #379 remains draft, unmerged, and undeployed. Browser/mobile rendering, live checkout, payment/webhook behavior, the full family/cross-sell/manual matrix, and eCode fulfillment metadata are not proven. The pre-existing native-routing test failure also remains unresolved.

## Next action

Preserve the active #371/#372 deep implementation stream and reuse PR #379 when the single-stream allocation is explicitly handed to #367. Then complete the full acceptance matrix, resolve the baseline routing failure, perform desktop/mobile and payment/webhook proof, and only then consider merge/deployment. No new Brian credential action is required for this partial slice.
