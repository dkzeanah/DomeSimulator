@echo off
rem Furnish a dome scene.
title DomeSim - Dome Composer
cd /d "%~dp0.."
py -3.12 dome_composer.py %*
if errorlevel 1 pause
