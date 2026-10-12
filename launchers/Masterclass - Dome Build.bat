@echo off
rem Start-to-finish 2V construction.
title DomeSim - Masterclass - Dome Build
cd /d "%~dp0.."
py -3.12 dome_build_masterclass.py %*
if errorlevel 1 pause
