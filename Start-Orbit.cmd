@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 launch_orbit.py %*
) else (
    python launch_orbit.py %*
)
if %errorlevel% neq 0 pause
