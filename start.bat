@echo off
echo Starting Action Blocker Service...
cd /d %~dp0
python action_blocker_service.py
pause


