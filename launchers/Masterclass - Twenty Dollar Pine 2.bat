@echo off
rem The Twenty Dollar Pine, part two.
title DomeSim - Masterclass - Twenty Dollar Pine 2
cd /d "%~dp0.."
py -3.12 pvtwo_masterclass.py %*
if errorlevel 1 pause
