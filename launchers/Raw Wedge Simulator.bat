@echo off
rem The live raw-wedge solver and 3-D dome.
title DomeSim - Raw Wedge Simulator
cd /d "%~dp0.."
py -3.12 geodesic_raw_wedge_dome_dihedral.py %*
if errorlevel 1 pause
