@echo off
title Amazon Stock Bot - Monitoring
echo ========================================================
echo Starting Amazon.ca Stock Monitor and Checkout Bot...
echo ========================================================
cd /d "%~dp0"
call .\venv\Scripts\python.exe run.py
pause
