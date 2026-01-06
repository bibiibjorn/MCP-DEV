@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   MCP-PowerBi-Finvision Dev Setup
echo ========================================
echo.

:: Check if Python 3.13 is available
echo Checking Python version...
py -3.13 --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python 3.13 is not installed!
    echo.
    echo This project requires Python 3.13 (pythonnet doesn't support 3.14 yet).
    echo.
    echo Please install Python 3.13 first:
    echo   Option 1: Run install-python.bat from this folder
    echo   Option 2: Download from https://www.python.org/downloads/release/python-3130/
    echo   Option 3: Run: winget install Python.Python.3.13
    echo.
    echo After installing, open a NEW terminal and run this script again.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('py -3.13 --version') do echo Found: %%i
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

:: Create virtual environment using Python 3.13
echo.
echo Step 2/5: Creating virtual environment with Python 3.13...
py -3.13 -m venv venv

if errorlevel 1 (
    echo.
    echo Failed to create virtual environment!
    echo.
    pause
    exit /b 1
)

if not exist "%repoPath%\venv\Scripts\python.exe" (
    echo.
    echo ERROR: Virtual environment was not created properly!
    echo The venv folder or python.exe is missing.
    echo.
    pause
    exit /b 1
)

echo Virtual environment created successfully.

:: Activate virtual environment and install dependencies
echo.
echo Step 3/5: Activating virtual environment...
call "%repoPath%\venv\Scripts\activate.bat"

echo.
echo Step 4/5: Installing dependencies...
echo This may take a few minutes...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo WARNING: Failed to install some dependencies!
    echo You may need to install them manually.
    echo.
    echo Press any key to continue anyway...
    pause >nul
)

:: Configure Claude Desktop
echo.
echo ========================================
echo   Claude Desktop Configuration
echo ========================================
echo.

:: Extract user folder from clone path to construct AppData path
:: Clone path like C:\Users\username\repos -> user folder is C:\Users\username
set "configPath="
for /f "tokens=1,2,3,* delims=\" %%a in ("%clonePath%") do (
    if /i "%%a"=="C:" if /i "%%b"=="Users" (
        set "userFolder=%%a\%%b\%%c"
        set "configPath=%%a\%%b\%%c\AppData\Roaming\Claude\claude_desktop_config.json"
    )
)

:: Fallback to %APPDATA% if we couldn't extract from clone path
if "%configPath%"=="" (
    echo Could not deduce user folder from clone path.
    set "configPath=%APPDATA%\Claude\claude_desktop_config.json"
)

echo Detected config path: %configPath%

:: Check if config directory exists
for %%F in ("%configPath%") do set "configDir=%%~dpF"
if not exist "%configDir%" (
    echo Creating config directory: %configDir%
    mkdir "%configDir%"
)

echo.
echo Step 5/5: Updating Claude Desktop config...

:: Use PowerShell to handle JSON manipulation properly
:: Note: Uses "MCP-PowerBi-Finvision-DEV" to avoid overwriting production server
powershell -ExecutionPolicy Bypass -Command ^
    "$configPath = '%configPath%'; $repoPath = '%repoPath%';" ^
    "$serverName = 'MCP-PowerBi-Finvision-DEV';" ^
    "$pythonPath = Join-Path $repoPath 'venv\Scripts\python.exe';" ^
    "$scriptPath = Join-Path $repoPath 'src\pbixray_server_enhanced.py';" ^
    "$mcpServer = @{ 'command' = $pythonPath; 'args' = @($scriptPath) };" ^
    "if (Test-Path $configPath) { try { $config = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json; Write-Host 'Found existing config file' -ForegroundColor Green } catch { Write-Host 'Config file exists but is invalid, creating new one' -ForegroundColor Yellow; $config = [PSCustomObject]@{} } } else { Write-Host 'Creating new config file' -ForegroundColor Yellow; $config = [PSCustomObject]@{} };" ^
    "if (-not $config.PSObject.Properties['mcpServers']) { $config | Add-Member -NotePropertyName 'mcpServers' -NotePropertyValue ([PSCustomObject]@{}) };" ^
    "if ($config.mcpServers.PSObject.Properties[$serverName]) { $config.mcpServers.$serverName = $mcpServer; Write-Host ('Updated existing ' + $serverName + ' configuration') -ForegroundColor Green } else { $config.mcpServers | Add-Member -NotePropertyName $serverName -NotePropertyValue $mcpServer; Write-Host ('Added ' + $serverName + ' configuration') -ForegroundColor Green };" ^
    "$json = $config | ConvertTo-Json -Depth 10; [System.IO.File]::WriteAllText($configPath, $json, [System.Text.UTF8Encoding]::new($false));" ^
    "Write-Host ''; Write-Host 'Config saved to:' $configPath -ForegroundColor Cyan;" ^
    "Write-Host ''; Write-Host 'MCP Server configured as:' $serverName -ForegroundColor Cyan;" ^
    "Write-Host '  Python: ' $pythonPath; Write-Host '  Script: ' $scriptPath;"

if errorlevel 1 (
    echo.
    echo Warning: Failed to update Claude Desktop config automatically.
    echo You may need to add the following entry to mcpServers in %configPath%:
    echo.
    echo     "MCP-PowerBi-Finvision-DEV": {
    echo       "command": "%repoPath%\venv\Scripts\python.exe",
    echo       "args": ["%repoPath%\src\pbixray_server_enhanced.py"]
    echo     }
    echo.
)

:: Success message
echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Repository cloned to: %repoPath%
echo Claude config: %configPath%
echo MCP Server added as: MCP-PowerBi-Finvision-DEV
echo.
echo NOTE: Your existing MCP servers are preserved.
echo       The DEV version runs alongside production.
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
