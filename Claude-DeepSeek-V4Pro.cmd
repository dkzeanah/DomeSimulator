@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Claude-DeepSeek-V4Pro.ps1" %*
