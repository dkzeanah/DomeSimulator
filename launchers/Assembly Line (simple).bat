@echo off
rem The simpler factory simulation.
title DomeSim - Assembly Line (simple)
cd /d "%~dp0.."
py -3.12 assembly_line_simple.py %*
if errorlevel 1 pause
