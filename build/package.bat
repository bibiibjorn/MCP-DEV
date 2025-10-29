@echo off
:: Change to repository root (parent of build/)
cd /d "%~dp0\.."

echo ========================================
echo MCP-PowerBi-Finvision Packager
echo ========================================
echo.

:: Read version from __version__.py (hardcoded for reliability)
set VERSION=3.4.2
echo Version: %VERSION%
echo.

:: Check Python
echo [1/5] Checking Python...
py -3 --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3 not found
    pause
    exit /b 1
)
py -3 --version
echo.

:: Setup venv
echo [2/5] Checking virtual environment...
if not exist "venv" (
    echo Creating venv...
    py -3 -m venv venv
)
echo.

:: Install dependencies
echo [3/5] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo Dependencies installed
echo.

:: Check mcpb
echo [4/5] Checking mcpb...
where mcpb >nul 2>&1
if errorlevel 1 (
    echo Installing mcpb...
    call npm install -g @anthropic-ai/mcpb
)
echo.

:: Package
echo [5/5] Creating package...
if not exist "dist" mkdir dist

set OUTFILE=dist\mcp-powerbi-finvision-%VERSION%.mcpb
if exist "%OUTFILE%" (
    echo Removing old package...
    del "%OUTFILE%"
)

echo Packaging to: %OUTFILE%
echo.
echo Checking manifest.json version...
findstr /C:"\"version\": \"%VERSION%\"" manifest.json >nul
if errorlevel 1 (
    echo WARNING: manifest.json version does not match %VERSION%
    echo Please update manifest.json before packaging
    pause
    exit /b 1
)
echo Manifest version verified: %VERSION%
echo.
echo ============================================================
echo IMPORTANT: This takes 3-5 minutes with NO visible progress
echo After "Manifest schema validation passes!" it will appear
echo to hang - THIS IS NORMAL. It's packaging 9000+ files.
echo DO NOT close this window. Please wait...
echo ============================================================
echo.

mcpb pack . "%OUTFILE%"
set PACK_EXIT_CODE=%errorlevel%

echo.
echo mcpb pack completed with exit code: %PACK_EXIT_CODE%
echo.

if not exist "%OUTFILE%" (
    echo.
    echo ERROR: Package was not created!
    echo Check the output above for errors.
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS!
echo ========================================
echo.
echo Package: %OUTFILE%
echo Full path: %CD%\%OUTFILE%
echo.
dir "%OUTFILE%" | findstr "mcpb"
echo.
echo Install in Claude Desktop:
echo 1. Settings ^> MCP Servers
echo 2. Install from file
echo 3. Select the .mcpb file above
echo.
pause
