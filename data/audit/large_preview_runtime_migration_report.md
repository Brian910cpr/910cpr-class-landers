# Large Preview Runtime Migration Report

- Branch: `codex/large-preview-runtime-migration`
- Head when generated: `aac616c0b65df555745a1ceb2b3a764b6cc46ab7`
- Deploy performed: no
- Scheduling behavior intentionally changed: no

## Decision
Full generated preview JSON files now live under ignored runtime storage:
- `data/runtime/audit_previews/dynamic_offers_preview.json`
- `data/runtime/audit_previews/public_sellable_offers_preview.json`

Compact summaries remain tracked:
- `data/audit/dynamic_offers_preview_summary.json`
- `data/audit/dynamic_offers_preview_summary.md`
- `data/audit/public_sellable_offers_preview_summary.json`
- `data/audit/public_sellable_offers_preview_summary.md`

## File Tracking

- `data/audit/dynamic_offers_preview.json`: staged for deletion = True, tracked after commit = False, exists in working tree = False
- `data/audit/public_sellable_offers_preview.json`: staged for deletion = True, tracked after commit = False, exists in working tree = False
- `data/runtime/audit_previews/dynamic_offers_preview.json`: tracked = False, exists = True, size = 98.57 MiB
- `data/runtime/audit_previews/public_sellable_offers_preview.json`: tracked = False, exists = True, size = 96.43 MiB

## Behavior Proof Targets
- 6 August AHA BLS appointment seeds still render in `docs/bls.html`.
- 3 Initial and 3 Renewal are expected.
- Preferred 09:15 time remains.
- Duplicate selected seed rows: 0.
- Existing real Enrollware BLS rows still render.
- Public offer integrity must pass.
