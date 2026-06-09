param(
  [string]$TaskFile = "ops/handoff/next_task.md"
)

Write-Host "=== HANDOFF STATUS ==="

Write-Host "`n=== Git status ==="
git status --short

Write-Host "`n=== Recent log ==="
git log --oneline -8

Write-Host "`n=== Next task ==="
Get-Content -LiteralPath $TaskFile

Write-Host "`n=== Codex output files ==="
Write-Host "ops/handoff/latest_codex_report.md"
Write-Host "ops/handoff/latest_validation_run.txt"
Write-Host "ops/handoff/latest_git_status.txt"
Write-Host "ops/handoff/latest_chatgpt_bundle.md"
