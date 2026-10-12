@echo off
rem The zome teaching world.
title DomeSim - Masterclass - Zome
cd /d "%~dp0.."
py -3.12 zome_masterclass.py %*
if errorlevel 1 pause
