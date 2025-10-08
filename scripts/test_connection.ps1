# Test PBIXRay Server Connection
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$pythonExe = Join-Path $projectRoot "venv\Scripts\python.exe"
$serverScript = Join-Path $projectRoot "src\pbixray_server_enhanced.py"

Write-Host "Testing PBIXRay Server..." -ForegroundColor Cyan
Write-Host "Python: $pythonExe" -ForegroundColor Gray
Write-Host "Script: $serverScript" -ForegroundColor Gray
Write-Host ""

if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $serverScript)) {
    Write-Host "ERROR: Server script not found!" -ForegroundColor Red
    exit 1
}

# Test Python and imports
Write-Host "Testing Python environment..." -ForegroundColor Yellow
$testCode = @"
import sys
import os

# Test imports
try:
    import mcp
    print("OK - MCP module loaded")
except Exception as e:
    print(f"ERROR - MCP: {e}")
    sys.exit(1)

try:
    import clr
    print("OK - CLR module loaded")
except Exception as e:
    print(f"ERROR - CLR: {e}")
    sys.exit(1)

# Test DLL path (inside project root)
script_dir = os.path.dirname(os.path.abspath(__file__))
dll_folder = os.path.join(script_dir, "lib", "dotnet")

if os.path.exists(dll_folder):
    dlls = [f for f in os.listdir(dll_folder) if f.endswith('.dll')]
    print(f"OK - Found {len(dlls)} DLLs in {dll_folder}")
else:
    print(f"ERROR - DLL folder not found: {dll_folder}")
    sys.exit(1)

print("\nAll tests passed!")
"@

$testFile = Join-Path $projectRoot "test_quick.py"
Set-Content -Path $testFile -Value $testCode

try {
    $output = & $pythonExe $testFile 2>&1
    Write-Host $output
    
    if ($output -match "All tests passed") {
        Write-Host "`nSUCCESS: Server is ready to use!" -ForegroundColor Green
        Write-Host "`nNext steps:" -ForegroundColor Cyan
        Write-Host "1. Run: .\scripts\install_to_claude.ps1" -ForegroundColor White
        Write-Host "2. Restart Claude Desktop" -ForegroundColor White
        Write-Host "3. Open Power BI Desktop with a .pbix file" -ForegroundColor White
        Write-Host "4. Ask Claude to detect instances" -ForegroundColor White
    }
    else {
        Write-Host "`nWARNING: Some tests failed" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "`nERROR: Test failed - $_" -ForegroundColor Red
}
finally {
    Remove-Item $testFile -ErrorAction SilentlyContinue
}

Write-Host ""
