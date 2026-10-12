@echo off
rem The franken-dome build lesson.
title DomeSim - Masterclass - Frankendome
cd /d "%~dp0.."
py -3.12 frankendome_masterclass.py %*
if errorlevel 1 pause
