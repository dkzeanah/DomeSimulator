@echo off
rem The layered dome builder.
title DomeSim - Dome Forge
cd /d "%~dp0.."
py -3.12 dome_forge.py %*
if errorlevel 1 pause
