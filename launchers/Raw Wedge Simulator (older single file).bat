@echo off
rem The earlier single-file solver.
title DomeSim - Raw Wedge Simulator (older single file)
cd /d "%~dp0.."
py -3.12 geodesic_raw_wedge_dome_single.py %*
if errorlevel 1 pause
