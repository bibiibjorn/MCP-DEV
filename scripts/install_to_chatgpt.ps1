# Install PBIXRay Server to ChatGPT (local MCPs)
# Requires ChatGPT desktop app with MCP support (mcpServers.local in settings.json)

param(
    [string]$ServerName = "PBIXRAY-V2"
)

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$pythonExe = Join-Path $projectRoot "venv\Scripts\python.exe"
$serverScript = Join-Path $projectRoot "src\pbixray_server_enhanced.py"

# ChatGPT desktop config (user-level)
# Example paths (adjust if OpenAI changes app config location):
# Windows: %APPDATA%\OpenAI\ChatGPT\settings.json
# If not present, we create or update minimally the mcpServers.local section.

$configPath = Join-Path $env:APPDATA "OpenAI\ChatGPT\settings.json"

Write-Host "Installing PBIXRay Server to ChatGPT (local MCPs)..." -ForegroundColor Cyan

if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Python not found at $pythonExe" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $serverScript)) {
    Write-Host "ERROR: Server script not found at $serverScript" -ForegroundColor Red
    exit 1
}

# Ensure settings directory
$configDir = Split-Path $configPath
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

# Read or create config
if (Test-Path $configPath) {
    try {
        $config = Get-Content $configPath -Raw | ConvertFrom-Json
    } catch {
        Write-Host "WARNING: Could not parse existing ChatGPT settings.json, creating a new one" -ForegroundColor Yellow
        $config = @{}
    }
} else {
    $config = @{}
}

# Ensure nested objects
if (-not $config.mcpServers) { $config | Add-Member -MemberType NoteProperty -Name mcpServers -Value @{} }
if (-not $config.mcpServers.local) { $config.mcpServers | Add-Member -MemberType NoteProperty -Name local -Value @{} }

# Register server
$config.mcpServers.local.$ServerName = @{
    command = $pythonExe
    args = @($serverScript)
}

# Save settings
try {
    $config | ConvertTo-Json -Depth 20 | Set-Content $configPath
    Write-Host "SUCCESS: ChatGPT MCP configuration updated" -ForegroundColor Green
    Write-Host "Settings: $configPath" -ForegroundColor Gray
    Write-Host "Server: $ServerName" -ForegroundColor Gray
    Write-Host "Python: $pythonExe" -ForegroundColor Gray
    Write-Host "Script: $serverScript" -ForegroundColor Gray
    Write-Host "\nNext: Restart the ChatGPT app and open a chat, then enable the MCP server if prompted." -ForegroundColor Yellow
} catch {
    Write-Host "ERROR: Failed to write ChatGPT settings.json - $_" -ForegroundColor Red
    exit 1
}
