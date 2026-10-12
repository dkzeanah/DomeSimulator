@echo off
rem The factory simulation (investor demo).
title DomeSim - Assembly Line
cd /d "%~dp0.."
py -3.12 assembly_line.py %*
if errorlevel 1 pause
