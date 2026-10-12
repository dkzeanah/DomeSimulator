@echo off
rem The 2V teaching world.
title DomeSim - Masterclass - 2V
cd /d "%~dp0.."
py -3.12 two_v_masterclass.py %*
if errorlevel 1 pause
