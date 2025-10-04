# Package PBIXRay Server for Distribution
param(
    [string]$OutputPath = "$env:USERPROFILE\Desktop\PBIXRAY-V2-Portable.zip"
)

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)

Write-Host "Packaging PBIXRay Server V2..." -ForegroundColor Cyan
Write-Host ""

# Verify critical components
$checks = @(
    @{Path = "venv\Scripts\python.exe"; Name = "Python executable"},
    @{Path = "src\pbixray_server_enhanced.py"; Name = "Server script"},
    @{Path = "lib\dotnet\Microsoft.AnalysisServices.AdomdClient.dll"; Name = "ADOMD.NET DLL"},
    @{Path = "lib\dotnet\Microsoft.AnalysisServices.Core.dll"; Name = "AMO Core DLL"},
    @{Path = "requirements.txt"; Name = "Requirements"}
)

$allPresent = $true
foreach ($check in $checks) {
    $fullPath = Join-Path $projectRoot $check.Path
    if (Test-Path $fullPath) {
        Write-Host "[OK] $($check.Name)" -ForegroundColor Green
    }
    else {
        Write-Host "[MISSING] $($check.Name)" -ForegroundColor Red
        $allPresent = $false
    }
}

if (-not $allPresent) {
    Write-Host ""
    Write-Host "ERROR: Some critical components are missing!" -ForegroundColor Red
    Write-Host "Run the consolidation script first." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Creating archive..." -ForegroundColor Yellow

# Create the zip file
try {
    # Remove existing file if present
    if (Test-Path $OutputPath) {
        Remove-Item $OutputPath -Force
    }
    
    Compress-Archive -Path $projectRoot -DestinationPath $OutputPath -Force
    
    $size = (Get-Item $OutputPath).Length / 1MB
    
    Write-Host ""
    Write-Host "SUCCESS: Package created!" -ForegroundColor Green
    Write-Host "  Location: $OutputPath" -ForegroundColor White
    Write-Host "  Size: $([math]::Round($size, 2)) MB" -ForegroundColor White
    Write-Host ""
    Write-Host "Ready for distribution!" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To distribute:" -ForegroundColor Yellow
    Write-Host "1. Share the ZIP file with colleagues" -ForegroundColor White
    Write-Host "2. Have them extract to C:\Tools\" -ForegroundColor White
    Write-Host "3. Run: .\scripts\install_to_claude.ps1" -ForegroundColor White
    Write-Host "4. Restart Claude Desktop" -ForegroundColor White
    Write-Host ""
}
catch {
    Write-Host ""
    Write-Host "ERROR: Failed to create package - $_" -ForegroundColor Red
    exit 1
}
