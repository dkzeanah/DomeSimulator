@echo off
rem The hexagonal-dome teaching world.
title DomeSim - Masterclass - Hexagonal Dome
cd /d "%~dp0.."
py -3.12 hex_masterclass.py %*
if errorlevel 1 pause
