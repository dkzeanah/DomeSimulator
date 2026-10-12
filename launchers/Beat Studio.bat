@echo off
rem Sequence rendered beats into a cut.
title DomeSim - Beat Studio
cd /d "%~dp0.."
py -3.12 beat_studio.py %*
if errorlevel 1 pause
