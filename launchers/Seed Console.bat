@echo off
rem The seed dome's cost calculator in 3-D.
title DomeSim - Seed Console
cd /d "%~dp0.."
py -3.12 seed_console.py %*
if errorlevel 1 pause
