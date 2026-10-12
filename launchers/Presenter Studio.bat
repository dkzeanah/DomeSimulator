@echo off
rem Text to explainer video for the 3-D worlds.
title DomeSim - Presenter Studio
cd /d "%~dp0.."
py -3.12 presenter_studio.py %*
if errorlevel 1 pause
