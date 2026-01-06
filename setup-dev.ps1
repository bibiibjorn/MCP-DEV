# MCP-PowerBi-Finvision Dev Setup Script
# Run this script to clone and set up the development environment

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MCP-PowerBi-Finvision Dev Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Ask for clone location
$defaultPath = "$env:USERPROFILE\repos"
Write-Host "Where would you like to clone the repository?"
Write-Host "Default: $defaultPath" -ForegroundColor Gray
$clonePath = Read-Host "Enter path (or press Enter for default)"

if ([string]::IsNullOrWhiteSpace($clonePath)) {
    $clonePath = $defaultPath
}

# Expand environment variables and resolve path
$clonePath = [System.Environment]::ExpandEnvironmentVariables($clonePath)

# Create directory if it doesn't exist
if (-not (Test-Path $clonePath)) {
    Write-Host ""
    Write-Host "Creating directory: $clonePath" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $clonePath -Force | Out-Null
}

$repoPath = Join-Path $clonePath "MCP-DEV"

# Check if repo already exists
if (Test-Path $repoPath) {
    Write-Host ""
    Write-Host "Directory already exists: $repoPath" -ForegroundColor Red
    $overwrite = Read-Host "Do you want to remove it and clone fresh? (y/N)"
    if ($overwrite -eq "y" -or $overwrite -eq "Y") {
        Remove-Item -Recurse -Force $repoPath
    } else {
        Write-Host "Aborting setup." -ForegroundColor Yellow
        exit 1
    }
}

# Clone the repository
Write-Host ""
Write-Host "Step 1/4: Cloning repository..." -ForegroundColor Green
Set-Location $clonePath
git clone https://github.com/bibiibjorn/MCP-DEV.git

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to clone repository!" -ForegroundColor Red
    exit 1
}

Set-Location $repoPath

# Create virtual environment
Write-Host ""
Write-Host "Step 2/4: Creating virtual environment..." -ForegroundColor Green
python -m venv venv

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to create virtual environment!" -ForegroundColor Red
    Write-Host "Make sure Python is installed and in your PATH" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host ""
Write-Host "Step 3/4: Activating virtual environment..." -ForegroundColor Green
& "$repoPath\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host ""
Write-Host "Step 4/4: Installing dependencies..." -ForegroundColor Green
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install some dependencies!" -ForegroundColor Yellow
    Write-Host "You may need to install them manually" -ForegroundColor Yellow
}

# Success message
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Repository cloned to: $repoPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start working:" -ForegroundColor Yellow
Write-Host "  1. cd `"$repoPath`""
Write-Host "  2. .\venv\Scripts\Activate.ps1"
Write-Host "  3. python src/pbixray_server_enhanced.py"
Write-Host ""
Write-Host "Or run the MCP server with Claude Desktop by adding to config." -ForegroundColor Gray
Write-Host ""
