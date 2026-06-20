@echo off
title Kick Multi-Tool
python main.py
if %errorlevel% neq 0 (
    echo.
    echo [!] The program crashed or was not installed correctly.
    echo [!] Try running install.bat again.
    pause
)
pause
