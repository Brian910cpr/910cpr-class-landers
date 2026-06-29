# Large Generated Audit File Policy

Status: report only. No files were deleted, moved, truncated, or compressed.

| File | Size MB | Tracked | Downstream tests need full file now? | Recommendation |
| --- | ---: | --- | --- | --- |
| `data/audit/dynamic_offers_preview.json` | 98.57 | True | True | Keep temporarily on this review branch for exact audit reproducibility; long-term, store summarized/truncated previews in git and move full generated previews to runtime/debug or external artifact storage. |
| `data/audit/public_sellable_offers_preview.json` | 96.43 | True | True | Keep temporarily on this review branch for exact audit reproducibility; long-term, store summarized/truncated previews in git and move full generated previews to runtime/debug or external artifact storage. |

Recommended repo policy: keep small summarized audit outputs in git, keep full generated previews out of long-term source history unless a specific review requires exact row-level artifacts, and add a reproducible command path to regenerate full previews locally.
