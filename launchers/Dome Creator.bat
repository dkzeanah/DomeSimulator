@echo off
rem Walkable build-a-home dome customiser.
title DomeSim - Dome Creator
cd /d "%~dp0.."
py -3.12 dome_creator.py %*
if errorlevel 1 pause
