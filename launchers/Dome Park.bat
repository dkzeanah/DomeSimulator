@echo off
rem Serviced pads and the dome network.
title DomeSim - Dome Park
cd /d "%~dp0.."
py -3.12 dome_park.py %*
if errorlevel 1 pause
