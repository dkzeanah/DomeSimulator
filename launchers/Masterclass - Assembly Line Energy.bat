@echo off
rem The assembly-line energy lesson.
title DomeSim - Masterclass - Assembly Line Energy
cd /d "%~dp0.."
py -3.12 line_masterclass.py %*
if errorlevel 1 pause
