@echo off
rem The launcher with the extra book tab.
title DomeSim - Two Trees Codex Launcher
cd /d "%~dp0.."
py -3.12 launcher_two_trees_codex.py %*
if errorlevel 1 pause
