# Removes deprecated/unused files from the repo
# Run from repo root in PowerShell
$ErrorActionPreference = 'Stop'
$paths = @(
  'core/bpa_service.py',
  'core/dax_advanced_validator.py',
  'core/measure_manager_enhanced.py'
)
foreach ($p in $paths) {
  $full = Join-Path $PSScriptRoot '..' $p
  $full = Resolve-Path $full -ErrorAction SilentlyContinue
  if ($full) {
    Write-Host "Removing $($full.Path)" -ForegroundColor Yellow
    Remove-Item -LiteralPath $full.Path -Force
  } else {
    Write-Host "Already removed: $p" -ForegroundColor DarkGray
  }
}
Write-Host "Done." -ForegroundColor Green
