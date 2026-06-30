# Large Generated Audit File Policy

Status: full generated previews are stored under ignored runtime storage; compact summaries remain tracked in `data/audit`.

| File | Size MB | Tracked | Downstream tests need full file now? | Recommendation |
| --- | ---: | --- | --- | --- |
| `data/runtime/audit_previews/dynamic_offers_preview.json` | 98.69 | False | False | Full generated preview is stored under ignored runtime storage. Keep compact summaries tracked in data/audit and regenerate the full preview locally when row-level audit detail is needed. |
| `data/runtime/audit_previews/public_sellable_offers_preview.json` | 96.62 | False | False | Full generated preview is stored under ignored runtime storage. Keep compact summaries tracked in data/audit and regenerate the full preview locally when row-level audit detail is needed. |

Recommended repo policy: keep small summarized audit outputs in git, keep full generated previews out of long-term source history unless a specific review requires exact row-level artifacts, and add a reproducible command path to regenerate full previews locally.
