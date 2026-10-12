@echo off
rem The persuasive presentation, teleprompter style.
title DomeSim - Wedge Teleprompter
cd /d "%~dp0.."
py -3.12 geodesic_wedge_teleprompter.py %*
if errorlevel 1 pause
