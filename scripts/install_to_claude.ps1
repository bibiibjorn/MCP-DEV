# Install MCP-PowerBi-Finvision Server to Claude Desktop
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$pythonExe = Join-Path $projectRoot "venv\Scripts\python.exe"
$serverScript = Join-Path $projectRoot "src\pbixray_server_enhanced.py"
$configPath = "$env:APPDATA\Claude\claude_desktop_config.json"

Write-Host "Installing MCP-PowerBi-Finvision Server to Claude Desktop..." -ForegroundColor Cyan
Write-Host ""

# Verify files exist
if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Python not found at $pythonExe" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $serverScript)) {
    Write-Host "ERROR: Server script not found at $serverScript" -ForegroundColor Red
    exit 1
}

# Create config directory if it doesn't exist
$configDir = Split-Path $configPath
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    Write-Host "Created Claude config directory" -ForegroundColor Green
}

# Read existing config or create new
if (Test-Path $configPath) {
    try {
        $configJson = Get-Content $configPath -Raw
        $config = $configJson | ConvertFrom-Json
        Write-Host "Found existing Claude config" -ForegroundColor Yellow
    }
    catch {
        Write-Host "WARNING: Could not parse existing config, creating new one" -ForegroundColor Yellow
        $config = @{
            mcpServers = @{}
        }
    }
}
else {
    $config = @{
        mcpServers = @{}
    }
    Write-Host "Creating new Claude config" -ForegroundColor Green
}

# Ensure mcpServers exists
if (-not $config.mcpServers) {
    $config | Add-Member -MemberType NoteProperty -Name "mcpServers" -Value @{} -Force
}

# Add or update the MCP-PowerBi-Finvision server
$config.mcpServers."MCP-PowerBi-Finvision" = @{
    command = $pythonExe
    args = @($serverScript)
}

# Save config
try {
    $config | ConvertTo-Json -Depth 10 | Set-Content $configPath
    Write-Host ""
    Write-Host "SUCCESS: Configuration updated!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Configuration file: $configPath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Server details:" -ForegroundColor Cyan
    Write-Host "  Python: $pythonExe" -ForegroundColor White
    Write-Host "  Script: $serverScript" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. RESTART Claude Desktop (fully close and reopen)" -ForegroundColor White
    Write-Host "2. Open Power BI Desktop with a .pbix file" -ForegroundColor White
    Write-Host "3. Ask Claude: 'Detect my Power BI Desktop instances'" -ForegroundColor White
    Write-Host "4. Ask Claude: 'Connect to instance 0'" -ForegroundColor White
    Write-Host "5. Ask Claude: 'What tables are in this model?'" -ForegroundColor White
    Write-Host "" 
}
catch {
    Write-Host ""
    Write-Host "ERROR: Failed to save configuration - $_" -ForegroundColor Red
    exit 1
}
