@echo off
rem The fabrication jig, up close.
title DomeSim - Jig Focus World
cd /d "%~dp0.."
py -3.12 jig_focus_world.py %*
if errorlevel 1 pause
