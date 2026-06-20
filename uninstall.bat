@echo off
echo ==========================================
echo       UNINSTALLER
echo ==========================================
echo.
set /p confirm="Are you sure you want to uninstall dependencies and clean cache? (y/n): "

if /i "%confirm%" neq "y" (
    echo Uninstall cancelled.
    pause
    exit /b
)

echo [+] Uninstalling Python Packages...
pip uninstall -r requirements.txt -y

echo [+] Removing Python Cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo.
echo [!] Done. 'Downloads' folder was preserved.
echo.
pause
