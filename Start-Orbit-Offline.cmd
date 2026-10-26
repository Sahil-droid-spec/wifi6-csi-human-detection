@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" launch_orbit.py --offline --lan %*
) else (
    py -3.10 launch_orbit.py --offline --lan %*
)
if errorlevel 1 pause
