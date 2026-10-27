@echo off
cd /d "%~dp0"
start "match3 server" python server.py
timeout /t 1 /nobreak >nul
start "" http://localhost:8765
