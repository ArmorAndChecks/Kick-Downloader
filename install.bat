@echo off
setlocal enabledelayedexpansion

title Kick Multi-Tool Installer
echo ==========================================
echo       KICK MULTI-TOOL INSTALLER
echo ==========================================
echo.

:: Ensure we are in the script's directory
cd /d "%~dp0"

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b
)

if not exist requirements.txt (
    echo [!] Error: requirements.txt not found in the current directory.
    echo Please make sure you extracted all files from the ZIP.
    pause
    exit /b
)

echo [+] Python found.
echo [+] Installing Dependencies (this may take a minute)...
python -m pip install --upgrade pip
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo [!] Installation failed. Check your internet connection or permissions.
    pause
    exit /b
)

echo.
echo ==========================================
echo        INSTALLATION SUCCESSFUL!
echo ==========================================
echo.
echo Use 'start_tool.bat' to run the application.
echo.
pause
