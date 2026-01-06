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
Write-Host "Step 1/5: Cloning repository..." -ForegroundColor Green
Set-Location $clonePath
git clone https://github.com/bibiibjorn/MCP-DEV.git

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to clone repository!" -ForegroundColor Red
    exit 1
}

Set-Location $repoPath

# Create virtual environment
Write-Host ""
Write-Host "Step 2/5: Creating virtual environment..." -ForegroundColor Green
python -m venv venv

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to create virtual environment!" -ForegroundColor Red
    Write-Host "Make sure Python is installed and in your PATH" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host ""
Write-Host "Step 3/5: Activating virtual environment..." -ForegroundColor Green
& "$repoPath\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host ""
Write-Host "Step 4/5: Installing dependencies..." -ForegroundColor Green
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install some dependencies!" -ForegroundColor Yellow
    Write-Host "You may need to install them manually" -ForegroundColor Yellow
}

# Configure Claude Desktop
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Claude Desktop Configuration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$defaultConfig = "$env:APPDATA\Claude\claude_desktop_config.json"
Write-Host "Enter the path to your Claude Desktop config file."
Write-Host "Default: $defaultConfig" -ForegroundColor Gray
$configPath = Read-Host "Config path (or press Enter for default)"

if ([string]::IsNullOrWhiteSpace($configPath)) {
    $configPath = $defaultConfig
}

# Check if config directory exists
$configDir = Split-Path $configPath -Parent
if (-not (Test-Path $configDir)) {
    Write-Host "Creating config directory: $configDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

Write-Host ""
Write-Host "Step 5/5: Updating Claude Desktop config..." -ForegroundColor Green

# Build paths for MCP server
$pythonPath = Join-Path $repoPath "venv\Scripts\python.exe"
$scriptPath = Join-Path $repoPath "src\pbixray_server_enhanced.py"

# Create the MCP server config object
$mcpServer = @{
    "command" = $pythonPath
    "args" = @($scriptPath)
}

# Load existing config or create new one
if (Test-Path $configPath) {
    try {
        $config = Get-Content $configPath -Raw | ConvertFrom-Json
        Write-Host "Found existing config file" -ForegroundColor Green
    } catch {
        Write-Host "Config file exists but is invalid, creating new one" -ForegroundColor Yellow
        $config = [PSCustomObject]@{}
    }
} else {
    Write-Host "Creating new config file" -ForegroundColor Yellow
    $config = [PSCustomObject]@{}
}

# Ensure mcpServers property exists
if (-not $config.PSObject.Properties["mcpServers"]) {
    $config | Add-Member -NotePropertyName "mcpServers" -NotePropertyValue ([PSCustomObject]@{})
}

# Add or update the MCP-PowerBi-Finvision server
if ($config.mcpServers.PSObject.Properties["MCP-PowerBi-Finvision"]) {
    $config.mcpServers."MCP-PowerBi-Finvision" = $mcpServer
    Write-Host "Updated existing MCP-PowerBi-Finvision configuration" -ForegroundColor Green
} else {
    $config.mcpServers | Add-Member -NotePropertyName "MCP-PowerBi-Finvision" -NotePropertyValue $mcpServer
    Write-Host "Added MCP-PowerBi-Finvision configuration" -ForegroundColor Green
}

# Write the config file with proper formatting
$config | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8

Write-Host ""
Write-Host "Config saved to: $configPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "MCP Server configured with:" -ForegroundColor Cyan
Write-Host "  Python: $pythonPath"
Write-Host "  Script: $scriptPath"

# Success message
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Repository cloned to: $repoPath" -ForegroundColor Cyan
Write-Host "Claude config updated: $configPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT: Restart Claude Desktop for changes to take effect!" -ForegroundColor Yellow
Write-Host ""
Write-Host "To start working manually:" -ForegroundColor Gray
Write-Host "  1. cd `"$repoPath`""
Write-Host "  2. .\venv\Scripts\Activate.ps1"
Write-Host "  3. python src/pbixray_server_enhanced.py"
Write-Host ""
