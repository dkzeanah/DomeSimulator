@echo off
rem Dome Sketch (sketch-claude): model the panel dome in the browser, draw its plan set and showcase.
title DomeSim - Dome Sketch (sketch-claude)
cd /d "%~dp0.."
py -3.12 -m sketch_claude serve %*
if errorlevel 1 pause
