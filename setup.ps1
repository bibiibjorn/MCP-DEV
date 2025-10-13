# MCP-PowerBi-Finvision - One-Click Setup Script
# This script automates the entire installation process

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSCommandPath

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MCP-PowerBi-Finvision Setup v2.4.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = py --version 2>&1
    Write-Host "  ✓ Found: $pythonVersion" -ForegroundColor Green

    # Check if version is 3.10+
    if ($pythonVersion -match "Python 3\.(\d+)") {
        $minorVersion = [int]$matches[1]
        if ($minorVersion -lt 10) {
            Write-Host "  ✗ Python 3.10 or higher required" -ForegroundColor Red
            Write-Host "  Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
            exit 1
        }
    }
}
catch {
    Write-Host "  ✗ Python not found" -ForegroundColor Red
    Write-Host "  Please install Python 3.10+ from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "  Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    exit 1
}

# Step 2: Create virtual environment
Write-Host ""
Write-Host "[2/5] Creating virtual environment..." -ForegroundColor Yellow
$venvPath = Join-Path $projectRoot "venv"

if (Test-Path $venvPath) {
    Write-Host "  ⚠ Virtual environment already exists" -ForegroundColor Yellow
    $response = Read-Host "  Do you want to recreate it? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host "  Removing old virtual environment..." -ForegroundColor Gray
        Remove-Item $venvPath -Recurse -Force
    }
    else {
        Write-Host "  Using existing virtual environment" -ForegroundColor Green
    }
}

if (-not (Test-Path $venvPath)) {
    Write-Host "  Creating venv..." -ForegroundColor Gray
    & py -3 -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "  ✓ Virtual environment created" -ForegroundColor Green
}

# Step 3: Install dependencies
Write-Host ""
Write-Host "[3/5] Installing Python dependencies..." -ForegroundColor Yellow
$pipExe = Join-Path $venvPath "Scripts\pip.exe"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"

Write-Host "  Upgrading pip..." -ForegroundColor Gray
& $pythonExe -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Failed to upgrade pip" -ForegroundColor Red
    exit 1
}

Write-Host "  Installing requirements (this may take 2-5 minutes)..." -ForegroundColor Gray
$requirementsPath = Join-Path $projectRoot "requirements.txt"
& $pipExe install -r $requirementsPath --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ Dependencies installed successfully" -ForegroundColor Green

# Step 4: Optional - Install .NET assemblies
Write-Host ""
Write-Host "[4/5] Installing .NET assemblies (optional)..." -ForegroundColor Yellow
Write-Host "  These enable advanced features like BPA and TMSL export" -ForegroundColor Gray
$response = Read-Host "  Install .NET assemblies? (Y/n)"

if ($response -ne "n" -and $response -ne "N") {
    $dotnetPath = Join-Path $projectRoot "lib\dotnet"
    $installScript = Join-Path $dotnetPath "install.ps1"

    if (Test-Path $installScript) {
        Push-Location $dotnetPath
        try {
            & .\install.ps1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ .NET assemblies installed" -ForegroundColor Green
            }
            else {
                Write-Host "  ⚠ .NET assembly installation had issues (non-critical)" -ForegroundColor Yellow
            }
        }
        catch {
            Write-Host "  ⚠ .NET assembly installation failed (non-critical)" -ForegroundColor Yellow
        }
        finally {
            Pop-Location
        }
    }
}
else {
    Write-Host "  ⊘ Skipped .NET assemblies (can install later)" -ForegroundColor Gray
}

# Step 5: Configure Claude Desktop
Write-Host ""
Write-Host "[5/5] Configuring AI client..." -ForegroundColor Yellow
Write-Host "  Choose your AI client:" -ForegroundColor Gray
Write-Host "    1) Claude Desktop (automated)" -ForegroundColor White
Write-Host "    2) ChatGPT Desktop (manual - instructions will be shown)" -ForegroundColor White
Write-Host "    3) Skip (configure manually later)" -ForegroundColor White
Write-Host ""
$choice = Read-Host "  Enter choice (1-3)"

switch ($choice) {
    "1" {
        Write-Host "  Configuring Claude Desktop..." -ForegroundColor Gray
        $installScript = Join-Path $projectRoot "scripts\install_to_claude.ps1"
        if (Test-Path $installScript) {
            & $installScript
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ Claude Desktop configured" -ForegroundColor Green
            }
        }
    }
    "2" {
        Write-Host ""
        Write-Host "  ChatGPT Desktop Configuration:" -ForegroundColor Cyan
        Write-Host "  1. Open ChatGPT Desktop" -ForegroundColor White
        Write-Host "  2. Go to Settings → Tools → Developer" -ForegroundColor White
        Write-Host "  3. Add this configuration:" -ForegroundColor White
        Write-Host ""
        Write-Host "  {" -ForegroundColor Gray
        Write-Host "    `"name`": `"MCP-PowerBi-Finvision`"," -ForegroundColor Gray
        Write-Host "    `"command`": `"$($pythonExe.Replace('\', '\\'))`"," -ForegroundColor Gray
        Write-Host "    `"args`": [" -ForegroundColor Gray
        Write-Host "      `"$((Join-Path $projectRoot 'src\pbixray_server_enhanced.py').Replace('\', '\\'))`"" -ForegroundColor Gray
        Write-Host "    ]" -ForegroundColor Gray
        Write-Host "  }" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  Press Enter when done..." -ForegroundColor Yellow
        Read-Host
    }
    default {
        Write-Host "  ⊘ Skipped AI client configuration" -ForegroundColor Gray
        Write-Host "  See INSTALL.md for manual setup instructions" -ForegroundColor Yellow
    }
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Installation location:" -ForegroundColor White
Write-Host "  $projectRoot" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. " -NoNewline -ForegroundColor White
Write-Host "Fully restart your AI client (close from system tray)" -ForegroundColor Gray
Write-Host "  2. " -NoNewline -ForegroundColor White
Write-Host "Open Power BI Desktop with a .pbix file" -ForegroundColor Gray
Write-Host "  3. " -NoNewline -ForegroundColor White
Write-Host "In AI client, ask: 'Detect my Power BI Desktop instances'" -ForegroundColor Gray
Write-Host "  4. " -NoNewline -ForegroundColor White
Write-Host "Then ask: 'Connect to instance 0'" -ForegroundColor Gray
Write-Host "  5. " -NoNewline -ForegroundColor White
Write-Host "Try: 'List tables'" -ForegroundColor Gray
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  • Quick start: README.md" -ForegroundColor Gray
Write-Host "  • Full guide: INSTALL_GUIDE.md" -ForegroundColor Gray
Write-Host "  • Troubleshooting: INSTALL.md" -ForegroundColor Gray
Write-Host ""
Write-Host "Happy analyzing! 🎉" -ForegroundColor Cyan
Write-Host ""
