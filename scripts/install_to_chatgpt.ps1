<#
Installs PBIXRay MCP Server into ChatGPT (Custom Tools) by generating a JSON config snippet.

What this script does:
- Detects your Python executable
- Resolves the full path to the server entrypoint (src/pbixray_server_enhanced.py)
- Prints a JSON block you can paste into ChatGPT > Settings > Tools > Developer > Add a Model Context Protocol (MCP) server
- Optionally writes the JSON to clipboard (if Windows clipboard is available)

Usage:
- Right-click this file and select "Run with PowerShell" OR run in a PowerShell prompt.
#>

param(
    [switch]$CopyToClipboard
)

function Resolve-PathSafe($path) {
    try { return (Resolve-Path -LiteralPath $path).Path } catch { return $null }
}

# Workspace root (this script's parent dir parent)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$ServerPath = Join-Path $RootDir 'src/pbixray_server_enhanced.py'
$ServerPathFull = Resolve-PathSafe $ServerPath

if (-not $ServerPathFull) {
    Write-Error "Could not resolve server path: $ServerPath"
    exit 1
}

# Detect python
$pythonCandidates = @('python.exe', 'py.exe', 'python3.exe')
$PythonPath = $null
foreach ($cand in $pythonCandidates) {
    $p = (Get-Command $cand -ErrorAction SilentlyContinue | Select-Object -First 1).Path
    if ($p) { $PythonPath = $p; break }
}

if (-not $PythonPath) {
    Write-Warning "Python not found on PATH. You can still configure ChatGPT with any Python you use."
    $PythonPath = 'python'
}

# Build MCP server entry
$displayName = 'MCP-PowerBi-Finvision'
$envVars = @{}

$json = [ordered]@{
    name = $displayName
    command = $PythonPath
    args = @($ServerPathFull)
    env = $envVars
}

# Output instructions
Write-Host "" -ForegroundColor Cyan
Write-Host "MCP-PowerBi-Finvision – ChatGPT MCP Configuration" -ForegroundColor Cyan
Write-Host "------------------------------------------------" -ForegroundColor Cyan
Write-Host "1) Open ChatGPT > Settings > Tools > Developer > Add a Model Context Protocol (MCP) server" -ForegroundColor Gray
Write-Host "2) Use the following JSON for the server configuration:" -ForegroundColor Gray

$pretty = $json | ConvertTo-Json -Depth 5
Write-Host $pretty -ForegroundColor Yellow

if ($CopyToClipboard) {
    try {
        $pretty | Set-Clipboard
        Write-Host "Configuration JSON copied to clipboard" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to copy to clipboard."
    }
}

Write-Host "3) Save, then in ChatGPT start using the 'MCP-PowerBi-Finvision' tool." -ForegroundColor Gray
Write-Host "If Python packages are missing, install them via:" -ForegroundColor Gray
Write-Host "   pip install -r requirements.txt" -ForegroundColor DarkGray
Write-Host "(Run that from the repo root: $RootDir)" -ForegroundColor DarkGray
