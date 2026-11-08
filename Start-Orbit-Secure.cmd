@echo off
cd /d "%~dp0"
set ORBIT_HTTPS=1
if exist Orbit.exe (
  Orbit.exe --server
) else (
  py -3.10 launch_orbit.py --lan
)
