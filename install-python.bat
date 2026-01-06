@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   Python 3.13 Installer
echo ========================================
echo.

:: Check if Python 3.13 is already installed
py -3.13 --version >nul 2>&1
if %errorlevel%==0 (
    echo Python 3.13 is already installed!
    py -3.13 --version
    echo.
    pause
    exit /b 0
)

echo Python 3.13 not found. Installing...
echo.

:: Check if winget is available
winget --version >nul 2>&1
if %errorlevel%==0 (
    echo Using winget to install Python 3.13...
    echo.
    winget install Python.Python.3.13 --accept-source-agreements --accept-package-agreements

    if %errorlevel%==0 (
        echo.
        echo ========================================
        echo   Installation Complete!
        echo ========================================
        echo.
        echo IMPORTANT: Close this window and open a NEW terminal
        echo            for Python to be available in PATH.
        echo.
    ) else (
        echo.
        echo Installation failed via winget.
        echo Please install manually from: https://www.python.org/downloads/release/python-3130/
        echo.
    )
) else (
    echo winget not found. Downloading Python installer directly...
    echo.

    :: Download Python installer using PowerShell
    set "installerUrl=https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe"
    set "installerPath=%TEMP%\python-3.13.0-amd64.exe"

    echo Downloading from python.org...
    powershell -Command "Invoke-WebRequest -Uri '%installerUrl%' -OutFile '%installerPath%'"

    if exist "%installerPath%" (
        echo.
        echo Running installer...
        echo Please follow the installation wizard.
        echo IMPORTANT: Check "Add Python to PATH" during installation!
        echo.
        start /wait "" "%installerPath%" /passive InstallAllUsers=0 PrependPath=1 Include_test=0

        echo.
        echo ========================================
        echo   Installation Complete!
        echo ========================================
        echo.
        echo IMPORTANT: Close this window and open a NEW terminal
        echo            for Python to be available in PATH.
        echo.

        :: Clean up installer
        del "%installerPath%" >nul 2>&1
    ) else (
        echo.
        echo Failed to download Python installer.
        echo Please install manually from: https://www.python.org/downloads/release/python-3130/
        echo.
    )
)

pause
