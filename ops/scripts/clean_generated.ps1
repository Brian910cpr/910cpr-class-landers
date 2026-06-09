Write-Host "=== CLEAN GENERATED DEBUG + PYCACHE ==="

Remove-Item -LiteralPath "debug/appointment_offer_calendar.html" -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "debug/appointment_offer_inventory.json" -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "debug/appointment_offer_inventory.md" -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "debug/hub_offer_model_report.json" -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "debug/hub_offer_model_report.md" -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "debug/hub_render_preview.json" -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "debug/hub_render_preview.md" -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "debug/hub_render_preview_validation.json" -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "debug/hub_render_preview_validation.md" -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "debug/lander_safety_preflight.json" -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "debug/lander_safety_preflight.md" -ErrorAction SilentlyContinue

git restore -- scripts/__pycache__ 2>$null
git clean -f -- scripts/__pycache__/*.pyc

Write-Host "`n=== Final status ==="
git status --short
