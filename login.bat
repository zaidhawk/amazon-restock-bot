@echo off
title Amazon Stock Bot - Setup Login
echo ========================================================
echo Launching browser for one-time Amazon.ca login...
echo ========================================================
cd /d "%~dp0"
call .\venv\Scripts\python.exe login.py
pause
