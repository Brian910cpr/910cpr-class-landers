# Release Candidate Large File Policy

## data/audit/dynamic_offers_preview.json
- Size: 98.57 MiB (103363008 bytes)
- Tracked: True
- Referencing scripts/tests: 19

## data/audit/public_sellable_offers_preview.json
- Size: 96.43 MiB (101112247 bytes)
- Tracked: True
- Referencing scripts/tests: 24

## Policy
- Keep tracked long-term: False
- Safe to remove in this release candidate: False
- Recommendation: Keep compact Markdown/JSON/CSV proof artifacts tracked. Move full generated previews to ignored runtime/debug/cache storage after a dedicated migration, and replace tests that assert large tracked files with summary-fixture assertions.
- Action taken: No file deletion or relocation was performed in this release-candidate pass.
