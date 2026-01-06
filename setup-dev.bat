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
echo Step 1/4: Cloning repository...
cd /d "%clonePath%"
git clone https://github.com/bibiibjorn/MCP-DEV.git

if errorlevel 1 (
    echo Failed to clone repository!
    exit /b 1
)

cd /d "%repoPath%"

:: Create virtual environment
echo.
echo Step 2/4: Creating virtual environment...
python -m venv venv

if errorlevel 1 (
    echo Failed to create virtual environment!
    echo Make sure Python is installed and in your PATH
    exit /b 1
)

:: Activate virtual environment and install dependencies
echo.
echo Step 3/4: Activating virtual environment...
call "%repoPath%\venv\Scripts\activate.bat"

echo.
echo Step 4/4: Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo Warning: Failed to install some dependencies!
    echo You may need to install them manually
)

:: Success message
echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Repository cloned to: %repoPath%
echo.
echo To start working:
echo   1. cd "%repoPath%"
echo   2. venv\Scripts\activate.bat
echo   3. python src/pbixray_server_enhanced.py
echo.
echo Or run the MCP server with Claude Desktop by adding to config.
echo.

:: Keep the window open
pause
