@echo off
rem The Frankendome montage.
title DomeSim - Masterclass - Frankendome Hype
cd /d "%~dp0.."
py -3.12 frankendome_hype.py %*
if errorlevel 1 pause
