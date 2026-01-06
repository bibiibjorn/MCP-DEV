@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   MCP-PowerBi-Finvision Dev Setup
echo ========================================
echo.

:: Ask for clone location
set "defaultPath=%USERPROFILE%\repos"
echo Where would you like to clone the repository?
echo Default: %defaultPath%
set /p "clonePath=Enter path (or press Enter for default): "

if "%clonePath%"=="" set "clonePath=%defaultPath%"

:: Create directory if it doesn't exist
if not exist "%clonePath%" (
    echo.
    echo Creating directory: %clonePath%
    mkdir "%clonePath%"
)

set "repoPath=%clonePath%\MCP-DEV"

:: Check if repo already exists
if exist "%repoPath%" (
    echo.
    echo Directory already exists: %repoPath%
    set /p "overwrite=Do you want to remove it and clone fresh? (y/N): "
    if /i "!overwrite!"=="y" (
        rmdir /s /q "%repoPath%"
    ) else (
        echo Aborting setup.
        exit /b 1
    )
)

:: Clone the repository
echo.
echo Step 1/5: Cloning repository...
cd /d "%clonePath%"
git clone https://github.com/bibiibjorn/MCP-DEV.git

if errorlevel 1 (
    echo Failed to clone repository!
    exit /b 1
)

cd /d "%repoPath%"

:: Create virtual environment
echo.
echo Step 2/5: Creating virtual environment...
python -m venv venv

if errorlevel 1 (
    echo Failed to create virtual environment!
    echo Make sure Python is installed and in your PATH
    exit /b 1
)

:: Activate virtual environment and install dependencies
echo.
echo Step 3/5: Activating virtual environment...
call "%repoPath%\venv\Scripts\activate.bat"

echo.
echo Step 4/5: Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo Warning: Failed to install some dependencies!
    echo You may need to install them manually
)

:: Configure Claude Desktop
echo.
echo ========================================
echo   Claude Desktop Configuration
echo ========================================
echo.
set "defaultConfig=%APPDATA%\Claude\claude_desktop_config.json"
echo Enter the path to your Claude Desktop config file.
echo Default: %defaultConfig%
set /p "configPath=Config path (or press Enter for default): "

if "%configPath%"=="" set "configPath=%defaultConfig%"

:: Check if config directory exists
for %%F in ("%configPath%") do set "configDir=%%~dpF"
if not exist "%configDir%" (
    echo Creating config directory: %configDir%
    mkdir "%configDir%"
)

echo.
echo Step 5/5: Updating Claude Desktop config...

:: Use PowerShell to handle JSON manipulation properly
powershell -ExecutionPolicy Bypass -Command ^
    "$configPath = '%configPath%';" ^
    "$repoPath = '%repoPath%';" ^
    "" ^
    "# Convert path to proper format with escaped backslashes for JSON" ^
    "$pythonPath = Join-Path $repoPath 'venv\Scripts\python.exe';" ^
    "$scriptPath = Join-Path $repoPath 'src\pbixray_server_enhanced.py';" ^
    "" ^
    "# Create the MCP server config object" ^
    "$mcpServer = @{" ^
    "    'command' = $pythonPath;" ^
    "    'args' = @($scriptPath)" ^
    "};" ^
    "" ^
    "# Load existing config or create new one" ^
    "if (Test-Path $configPath) {" ^
    "    try {" ^
    "        $config = Get-Content $configPath -Raw | ConvertFrom-Json;" ^
    "        Write-Host 'Found existing config file' -ForegroundColor Green;" ^
    "    } catch {" ^
    "        Write-Host 'Config file exists but is invalid, creating new one' -ForegroundColor Yellow;" ^
    "        $config = [PSCustomObject]@{};" ^
    "    }" ^
    "} else {" ^
    "    Write-Host 'Creating new config file' -ForegroundColor Yellow;" ^
    "    $config = [PSCustomObject]@{};" ^
    "}" ^
    "" ^
    "# Ensure mcpServers property exists" ^
    "if (-not $config.PSObject.Properties['mcpServers']) {" ^
    "    $config | Add-Member -NotePropertyName 'mcpServers' -NotePropertyValue ([PSCustomObject]@{});" ^
    "}" ^
    "" ^
    "# Add or update the MCP-PowerBi-Finvision server" ^
    "if ($config.mcpServers.PSObject.Properties['MCP-PowerBi-Finvision']) {" ^
    "    $config.mcpServers.'MCP-PowerBi-Finvision' = $mcpServer;" ^
    "    Write-Host 'Updated existing MCP-PowerBi-Finvision configuration' -ForegroundColor Green;" ^
    "} else {" ^
    "    $config.mcpServers | Add-Member -NotePropertyName 'MCP-PowerBi-Finvision' -NotePropertyValue $mcpServer;" ^
    "    Write-Host 'Added MCP-PowerBi-Finvision configuration' -ForegroundColor Green;" ^
    "}" ^
    "" ^
    "# Write the config file with proper formatting" ^
    "$config | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8;" ^
    "Write-Host '';" ^
    "Write-Host 'Config saved to:' $configPath -ForegroundColor Cyan;" ^
    "Write-Host '';" ^
    "Write-Host 'MCP Server configured with:' -ForegroundColor Cyan;" ^
    "Write-Host '  Python: ' $pythonPath;" ^
    "Write-Host '  Script: ' $scriptPath;"

if errorlevel 1 (
    echo.
    echo Warning: Failed to update Claude Desktop config automatically.
    echo You may need to add the following manually to %configPath%:
    echo.
    echo {
    echo   "mcpServers": {
    echo     "MCP-PowerBi-Finvision": {
    echo       "command": "%repoPath%\venv\Scripts\python.exe",
    echo       "args": ["%repoPath%\src\pbixray_server_enhanced.py"]
    echo     }
    echo   }
    echo }
    echo.
)

:: Success message
echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Repository cloned to: %repoPath%
echo Claude config updated: %configPath%
echo.
echo IMPORTANT: Restart Claude Desktop for changes to take effect!
echo.
echo To start working manually:
echo   1. cd "%repoPath%"
echo   2. venv\Scripts\activate.bat
echo   3. python src/pbixray_server_enhanced.py
echo.

:: Keep the window open
pause
