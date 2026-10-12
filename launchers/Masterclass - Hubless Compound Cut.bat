@echo off
rem The compound-cut lesson.
title DomeSim - Masterclass - Hubless Compound Cut
cd /d "%~dp0.."
py -3.12 hubless_cut_masterclass.py %*
if errorlevel 1 pause
