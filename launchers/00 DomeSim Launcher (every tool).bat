@echo off
rem The main launcher: one window with a tab for every tool.
title DomeSim - 00 DomeSim Launcher (every tool)
cd /d "%~dp0.."
py -3.12 launcher.py %*
if errorlevel 1 pause
