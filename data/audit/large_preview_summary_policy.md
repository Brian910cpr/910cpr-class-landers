# Large Preview Summary Policy

Full generated preview files are not source-of-truth and should not be tracked in `data/audit`.

## Full Runtime Artifacts
- `data/runtime/audit_previews/dynamic_offers_preview.json`
- `data/runtime/audit_previews/public_sellable_offers_preview.json`

These files are generated, ignored by git, and should be regenerated locally when row-level debugging is needed.

## Tracked Review Summaries
- `data/audit/dynamic_offers_preview_summary.json`
- `data/audit/dynamic_offers_preview_summary.md`
- `data/audit/public_sellable_offers_preview_summary.json`
- `data/audit/public_sellable_offers_preview_summary.md`

Summaries include total counts, August counts, BLS counts, selected seed counts where detectable, top rejection/hidden reasons when present, generated timestamp, size, and a pointer to the runtime full preview.

## Rule
Commit compact summaries and audit reports. Do not commit regenerated full preview JSON unless Brian explicitly approves a temporary review exception.
