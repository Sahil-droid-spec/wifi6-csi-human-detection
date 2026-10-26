@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" launch_orbit.py %*
    if errorlevel 1 pause
    exit /b
)
where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 launch_orbit.py %*
) else (
    python launch_orbit.py %*
)
if %errorlevel% neq 0 pause
